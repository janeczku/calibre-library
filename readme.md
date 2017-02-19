##About my fork

I have been messing around with calibre-web in a few different ways and thought I would share them. I am currently working on a couple of features: - 

1. Marking books as read/unread. In the Book View, there is now a row that says whether or not a book is read. If you click it, it will toggle. Further down the line, I plan on adding goodreads support, which if the book has a goodreads link, it will automatically move the book to the "to read" and "read" bookshelves.

2. Google drive support. In my local version, I currently have this working, but it is essentially to make the website have all the books / covers / metadata.db served directly from google drive. I am currently, still optimising a bit of code, and will hopefully have this on GitHub ASAP. 

##About

Calibre Web is a web app providing a clean interface for browsing, reading and downloading eBooks using an existing [Calibre](https://calibre-ebook.com) database.

*This software is a fork of [library](https://github.com/mutschler/calibreserver) and licensed under the GPL v3 License.*

![screenshot](https://raw.githubusercontent.com/janeczku/docker-calibre-web/master/screenshot.png)

##Features
- Bootstrap 3 HTML5 interface
- full graphical setup
- User management
- Admin interface
- User Interface in english, french, german, polish, simplified chinese, spanish
- OPDS feed for eBook reader apps 
- Filter and search by titles, authors, tags, series and language
- Create custom book collection (shelves)
- Support for editing eBook metadata
- Support for converting eBooks from EPUB to Kindle format (mobi/azw)
- Restrict eBook download to logged-in users
- Support for public user registration
- Send eBooks to Kindle devices with the click of a button
- Support for reading eBooks directly in the browser (.txt, .epub, .pdf)
- Upload new books in PDF, epub, fb2 format
- Support for Calibre custom columns
- Fine grained per-user permissions
- Self update capability

## Quick start

1. Execute the command: `python cps.py`
2. Point your browser to `http://localhost:8083` or `http://localhost:8083/opds` for the OPDS catalog 
3. Set `Location of Calibre database` to the path of the folder where your Calibre library (metadata.db) lives, push "submit" button
4. Go to Login page

**Default admin login:**    
*Username:* admin   
*Password:* admin123

## Runtime Configuration Options

The configuration can be changed as admin in the admin panel under "Configuration"

Server Port:
Changes the port calibre-web is listening, changes take effect after pressing submit button

Enable public registration:    
Tick to enable public user registration.

Enable anonymous browsing:    
Tick to allow not logged in users to browse the catalog, anonymous user permissions can be set as admin ("Guest" user)

Enable uploading:
Tick to enable uploading of PDF, epub, FB2. This requires the imagemagick library to be installed.    

## Requirements

Python 2.7+
     
Optionally, to enable on-the-fly conversion from EPUB to MOBI when using the send-to-kindle feature:     

[Download](http://www.amazon.com/gp/feature.html?docId=1000765211) Amazon's KindleGen tool for your platform and place the binary named as `kindlegen` in the `vendor` folder. 

## Docker image

Calibre Web can be run as Docker container. The latest image is available on [Docker Hub](https://registry.hub.docker.com/u/janeczku/calibre-web/).

## Reverse Proxy

Reverse proxy configuration examples for apache and nginx to use calibre-web:

nginx configuration for a local server listening on port 8080, mapping calibre web to /calibre:

```
http {
    upstream calibre {
        server  127.0.0.1:8083;
    }
    server {
            location /calibre-web {
                proxy_bind              $server_addr;
                proxy_pass              http://127.0.0.1:8083;
                proxy_set_header        Host            $http_host;
                proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header        X-Scheme        $scheme;
                proxy_set_header        X-Script-Name   /calibre-web;
        }
    }
}
```

Apache 2.4 configuration for a local server listening on port 443, mapping calibre web to /calibre-web:

The following modules have to be activated: headers, proxy, rewrite.
```
Listen 443

<VirtualHost *:443>
    SSLEngine on
    SSLProxyEngine on
    SSLCipherSuite ALL:!ADH:!EXPORT56:RC4+RSA:+HIGH:+MEDIUM:+LOW:+SSLv2:+EXP:+eNULL
    SSLCertificateFile "C:\Apache24\conf\ssl\test.crt"
    SSLCertificateKeyFile "C:\Apache24\conf\ssl\test.key"
    
    <Location "/calibre-web" >
        RequestHeader set X-SCRIPT-NAME /calibre-web
        RequestHeader set X-SCHEME https
        ProxyPass http://localhost:8083/
        ProxyPassReverse http://localhost:8083/
    </Location>
</VirtualHost>
```

## Start calibre-web as service under Linux

Create a file "cps.service" as root in the folder /etc/systemd/system with the following content:

```[Unit]
Description=Calibre-web

[Service]
Type=simple
User=[Username]
ExecStart=[path to python] [/PATH/TO/cps.py]

[Install]
WantedBy=multi-user.target
```

Replace the user and ExecStart with your user and foldernames.

`sudo systemctl enable cps.service`

enables the service. 
