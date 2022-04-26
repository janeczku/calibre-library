#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2022 OzzieIsaacs
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

from markupsafe import escape

from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from flask_babel import gettext as _
from flask_babel import get_locale, format_datetime
from babel.units import format_unit

from . import logger
from .render_template import render_title_template
from .services.worker import WorkerThread, STAT_WAITING, STAT_FAIL, STAT_STARTED, STAT_FINISH_SUCCESS

tasks = Blueprint('tasks', __name__)

log = logger.create()


@tasks.route("/ajax/emailstat")
@login_required
def get_email_status_json():
    tasks = WorkerThread.getInstance().tasks
    return jsonify(render_task_status(tasks))


@tasks.route("/tasks")
@login_required
def get_tasks_status():
    # if current user admin, show all email, otherwise only own emails
    tasks = WorkerThread.getInstance().tasks
    answer = render_task_status(tasks)
    return render_title_template('tasks.html', entries=answer, title=_(u"Tasks"), page="tasks")


# helper function to apply localize status information in tasklist entries
def render_task_status(tasklist):
    rendered_tasklist = list()
    for __, user, __, task in tasklist:
        if user == current_user.name or current_user.role_admin():
            ret = {}
            if task.start_time:
                ret['starttime'] = format_datetime(task.start_time, format='short', locale=get_locale())
                ret['runtime'] = format_runtime(task.runtime)

            # localize the task status
            if isinstance(task.stat, int):
                if task.stat == STAT_WAITING:
                    ret['status'] = _(u'Waiting')
                elif task.stat == STAT_FAIL:
                    ret['status'] = _(u'Failed')
                elif task.stat == STAT_STARTED:
                    ret['status'] = _(u'Started')
                elif task.stat == STAT_FINISH_SUCCESS:
                    ret['status'] = _(u'Finished')
                else:
                    ret['status'] = _(u'Unknown Status')

            ret['taskMessage'] = "{}: {}".format(_(task.name), task.message)
            ret['progress'] = "{} %".format(int(task.progress * 100))
            ret['user'] = escape(user)  # prevent xss
            rendered_tasklist.append(ret)

    return rendered_tasklist


# helper function for displaying the runtime of tasks
def format_runtime(runtime):
    ret_val = ""
    if runtime.days:
        ret_val = format_unit(runtime.days, 'duration-day', length="long", locale=get_locale()) + ', '
    minutes, seconds = divmod(runtime.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    # ToDo: locale.number_symbols._data['timeSeparator'] -> localize time separator ?
    if hours:
        ret_val += '{:d}:{:02d}:{:02d}s'.format(hours, minutes, seconds)
    elif minutes:
        ret_val += '{:2d}:{:02d}s'.format(minutes, seconds)
    else:
        ret_val += '{:2d}s'.format(seconds)
    return ret_val
