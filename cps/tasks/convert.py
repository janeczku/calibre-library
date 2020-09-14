from __future__ import division, print_function, unicode_literals
import sys
import os
import re

from glob import glob
from shutil import copyfile

from sqlalchemy.exc import SQLAlchemyError

from cps.services.worker import CalibreTask, STAT_FINISH_SUCCESS
from cps import calibre_db, db
from cps import logger, config
from cps.subproc_wrapper import process_open
from flask_babel import gettext as _

from cps.tasks.mail import TaskEmail
from cps import gdriveutils
log = logger.create()


class TaskConvert(CalibreTask):
    def __init__(self, file_path, bookid, taskMessage, settings, kindle_mail):
        super(TaskConvert, self).__init__(taskMessage)
        self.file_path = file_path
        self.bookid = bookid
        self.settings = settings
        self.kindle_mail = kindle_mail

        self.results = dict()

    def run(self, worker_thread):
        self.worker_thread = worker_thread
        filename = self._convert_ebook_format()

        if filename:
            if config.config_use_google_drive:
                gdriveutils.updateGdriveCalibreFromLocal()
            if self.kindle_mail:
                # if we're sending to kindle after converting, create a one-off task and run it immediately
                # todo: figure out how to incorporate this into the progress
                try:
                    task = TaskEmail(self.settings['subject'], self.results["path"],
                               filename, self.settings, self.kindle_mail,
                               self.settings['subject'], self.settings['body'], internal=True)
                    task.start(worker_thread)

                    # even though the convert task might be finished, if this task fails, fail the whole thing
                    if task.stat != STAT_FINISH_SUCCESS:
                        raise Exception(task.error)
                except Exception as e:
                    return self._handleError(str(e))

    def _convert_ebook_format(self):
        error_message = None
        local_session = db.CalibreDB()
        file_path = self.file_path
        book_id = self.bookid
        format_old_ext = u'.' + self.settings['old_book_format'].lower()
        format_new_ext = u'.' + self.settings['new_book_format'].lower()

        # check to see if destination format already exists -
        # if it does - mark the conversion task as complete and return a success
        # this will allow send to kindle workflow to continue to work
        if os.path.isfile(file_path + format_new_ext):
            log.info("Book id %d already converted to %s", book_id, format_new_ext)
            cur_book = calibre_db.get_book(book_id)
            self.results['path'] = file_path
            self.results['title'] = cur_book.title
            self._handleSuccess()
            return file_path + format_new_ext
        else:
            log.info("Book id %d - target format of %s does not exist. Moving forward with convert.",
                     book_id,
                     format_new_ext)

        if config.config_kepubifypath and format_old_ext == '.epub' and format_new_ext == '.kepub':
            check, error_message = self._convert_kepubify(file_path,
                                                          format_old_ext,
                                                          format_new_ext)
        else:
            # check if calibre converter-executable is existing
            if not os.path.exists(config.config_converterpath):
                # ToDo Text is not translated
                self._handleError(_(u"Calibre ebook-convert %(tool)s not found", tool=config.config_converterpath))
                return
            check, error_message = self._convert_calibre(file_path, format_old_ext, format_new_ext)

        if check == 0:
            cur_book = calibre_db.get_book(book_id)
            if os.path.isfile(file_path + format_new_ext):
                # self.db_queue.join()
                new_format = db.Data(name=cur_book.data[0].name,
                                         book_format=self.settings['new_book_format'].upper(),
                                         book=book_id, uncompressed_size=os.path.getsize(file_path + format_new_ext))
                try:
                    local_session.merge(new_format)
                    local_session.commit()
                except SQLAlchemyError as e:
                    local_session.rollback()
                    log.error("Database error: %s", e)
                    return
                self.results['path'] = cur_book.path
                self.results['title'] = cur_book.title
                if config.config_use_google_drive:
                    os.remove(file_path + format_old_ext)
                self._handleSuccess()
                return file_path + format_new_ext
            else:
                error_message = _('%(format)s format not found on disk', format=format_new_ext.upper())
        log.info("ebook converter failed with error while converting book")
        if not error_message:
            error_message = _('Ebook converter failed with unknown error')
        self._handleError(error_message)
        return

    def _convert_kepubify(self, file_path, format_old_ext, format_new_ext):
        quotes = [1, 3]
        command = [config.config_kepubifypath, (file_path + format_old_ext), '-o', os.path.dirname(file_path)]
        try:
            p = process_open(command, quotes)
        except OSError as e:
            return 1, _(u"Kepubify-converter failed: %(error)s", error=e)
        self.progress = 0.01
        while True:
            nextline = p.stdout.readlines()
            nextline = [x.strip('\n') for x in nextline if x != '\n']
            if sys.version_info < (3, 0):
                nextline = [x.decode('utf-8') for x in nextline]
            for line in nextline:
                log.debug(line)
            if p.poll() is not None:
                break

        # ToD Handle
        # process returncode
        check = p.returncode

        # move file
        if check == 0:
            converted_file = glob(os.path.join(os.path.dirname(file_path), "*.kepub.epub"))
            if len(converted_file) == 1:
                copyfile(converted_file[0], (file_path + format_new_ext))
                os.unlink(converted_file[0])
            else:
                return 1, _(u"Converted file not found or more than one file in folder %(folder)s",
                            folder=os.path.dirname(file_path))
        return check, None

    def _convert_calibre(self, file_path, format_old_ext, format_new_ext):
        try:
            # Linux py2.7 encode as list without quotes no empty element for parameters
            # linux py3.x no encode and as list without quotes no empty element for parameters
            # windows py2.7 encode as string with quotes empty element for parameters is okay
            # windows py 3.x no encode and as string with quotes empty element for parameters is okay
            # separate handling for windows and linux
            quotes = [1, 2]
            command = [config.config_converterpath, (file_path + format_old_ext),
                       (file_path + format_new_ext)]
            quotes_index = 3
            if config.config_calibre:
                parameters = config.config_calibre.split(" ")
                for param in parameters:
                    command.append(param)
                    quotes.append(quotes_index)
                    quotes_index += 1

            p = process_open(command, quotes)
        except OSError as e:
            return 1, _(u"Ebook-converter failed: %(error)s", error=e)

        while p.poll() is None:
            nextline = p.stdout.readline()
            if os.name == 'nt' and sys.version_info < (3, 0):
                nextline = nextline.decode('windows-1252')
            elif os.name == 'posix' and sys.version_info < (3, 0):
                nextline = nextline.decode('utf-8')
            log.debug(nextline.strip('\r\n'))
            # parse progress string from calibre-converter
            progress = re.search(r"(\d+)%\s.*", nextline)
            if progress:
                self.progress = int(progress.group(1)) / 100

        # process returncode
        check = p.returncode
        calibre_traceback = p.stderr.readlines()
        error_message = ""
        for ele in calibre_traceback:
            if sys.version_info < (3, 0):
                ele = ele.decode('utf-8')
            log.debug(ele.strip('\n'))
            if not ele.startswith('Traceback') and not ele.startswith('  File'):
                error_message = _("Calibre failed with error: %(error)s", error=ele.strip('\n'))
        return check, error_message

    @property
    def name(self):
        return "Convert"
