#!/usr/bin/env python
# encoding=utf-8

import os.path
import sys,os
import tornado.web
import tornado.wsgi
import wsgiref.handlers
import hashlib
from juthin.core import Author

class InitHandler(tornado.web.RequestHandler):
    def get(self):
        author = Author.all().get()
        if not author:
            author = Author()
            author.name = u'username'
            author.nickname = u'nickname'
            author.passwd = hashlib.md5('password').hexdigest()
            author.blog_title = u'blog title'
            author.blog_theme = u'default'
            author.blog_domain = u'blog domain'
            author.blog_timezone = 8
            author.sync_key = hashlib.md5('sync_key').hexdigest() # 通过 web service api 同步文章
            author.put()
        self.redirect('/writer/signin/')

class Application(tornado.wsgi.WSGIApplication):
    def __init__(self):
        handlers = [
            (r"/init/", InitHandler),
        ]
        settings = dict(
            template_path = os.path.join(os.path.dirname(__file__), "template/writer"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
        )
        tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)

def main():
    wsgiref.handlers.CGIHandler().run(Application())

if __name__ == "__main__":
    main()
