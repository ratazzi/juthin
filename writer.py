#!/usr/bin/env python
# encoding=utf-8

import os.path
import re
import sys,os
import datetime,time
import tornado.options
import tornado.web
import tornado.wsgi
import wsgiref.handlers
import unicodedata
import markdown
import hashlib
from tornado.options import define, options
from google.appengine.ext import db
from django.utils import simplejson

from juthin.core import Entry, Tags, Helper
from juthin import twitter

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id: return None

class OverviewHandler(BaseHandler):
    def get(self):
        if not self.get_secure_cookie('user'):
            self.redirect('/writer/signin/')
            return
        rs = db.GqlQuery('SELECT * FROM Entry ORDER BY created DESC LIMIT 25')
        entries = rs.fetch(25)
        self.render('overview.html', entries=entries)

class NewHandler(BaseHandler):
    def get(self):
        if not self.get_secure_cookie('user'):
            self.redirect('/writer/signin/')
            return
        self.render('new.html')

    def post(self):
        if not self.get_secure_cookie('user'):
            self.redirect('/writer/signin/')
            return
        last = Entry.all().order('-created').get()
        entry = Entry()
        if last:
            entry.id = last.id + 1
        else:
            entry.id = 1
        entry.created = int(time.time())
        entry.title = self.get_argument('title')
        entry.tags = [item for item in self.get_argument('tags').split(',')]
        entry.content = markdown.markdown(self.get_argument('content'))
        entry.hits = 0
        entry.lastmodify = int(time.time())
        entry.put()
        self.redirect('/writer/')

class UpdateHandler(BaseHandler):
    def get(self, id):
        id = int(id)
        if not self.get_secure_cookie('user'):
            self.redirect('/writer/signin/')
            return
        rs = db.GqlQuery('SELECT * FROM Entry WHERE id = :1', id)
        entry = rs.get()
        self.render('update.html', entry=entry)

    def post(self, id):
        id = int(id)
        if not self.get_secure_cookie('user'):
            self.redirect('/writer/signin/')
            return
        rs = db.GqlQuery('SELECT * FROM Entry WHERE id = :1', id)
        entry = rs.get()
        entry.title = self.get_argument('title')
        entry.tags = [item for item in self.get_argument('tags').split(',')]
        entry.content = markdown.markdown(self.get_argument('content'))
        entry.lastmodify = int(time.time())
        db.put(entry)
        self.redirect('/writer/')

class RemoveHandler(BaseHandler):
    def get(self, id):
        id = int(id)
        if not self.get_secure_cookie('user'):
            self.redirect('/writer/signin/')
            return
        rs = db.GqlQuery('SELECT * FROM Entry WHERE id = :1', id)
        entry = rs.get()
        db.delete(entry)
        self.redirect('/writer/')

class TwitterHandler(BaseHandler):
    def post(self):
        if not self.get_secure_cookie('user'):
            self.redirect('/writer/signin/')
            return
        status = self.get_argument('status')
        api = twitter.Api(username='ratazzi_potts', password='linux520')
        api.PostUpdate(status)
        self.redirect('/writer/')

class EntrySyncHandler(BaseHandler):
    def post(self):
        error = {'status':'Access Denied.'}
        if not self.get_arguments('key'):
            self.write(simplejson.dumps(error))
            return
        if self.get_argument('key') != hashlib.md5('linux520').hexdigest():
            self.write(simplejson.dumps(error))
            return

        entry = Entry()
        entry.id = int(self.get_argument('id'))
        entry.created = int(self.get_argument('created'))
        entry.title = self.get_argument('title')
        entry.tags = [item for item in self.get_argument('tags').split(',')]
        entry.content = markdown.markdown(self.get_argument('content'))
        entry.hits = 0
        entry.lastmodify = int(self.get_argument('lastmodify'))
        entry.put()
        response = {'status':'ok'}
        self.write(simplejson.dumps(response))

class SigninHandler(BaseHandler):
    def get(self):
        if self.get_secure_cookie('user'):
            self.redirect('/writer/')
            return
        self.render('signin.html')

    def post(self):
        user = self.get_argument('user')
        passwd = self.get_argument('passwd')
        if user == 'ratazzi' and passwd == 'linux520':
            self.set_secure_cookie('user', passwd)
            self.redirect('/writer/')
        else:
            self.redirect('/writer/signin/')

class SignoutHandler(BaseHandler):
    def get(self):
        if self.get_secure_cookie('user'):
            self.clear_cookie('user')
            self.redirect('/')

class Application(tornado.wsgi.WSGIApplication):
    def __init__(self):
        handlers = [
            (r"/writer/", OverviewHandler),
            (r"/writer/new/", NewHandler),
            (r"/writer/update/([0-9]+)", UpdateHandler),
            (r"/writer/remove/([0-9]+)", RemoveHandler),
            (r"/writer/signin/", SigninHandler),
            (r"/writer/signout/", SignoutHandler),
            (r"/twitter/tweet/", TwitterHandler),
            (r"/entry/sync/", EntrySyncHandler),
        ]
        settings = dict(
            blog_title=u"Ratazzi's Blog",
            domain='www.ratazzi.org',
            template_path=os.path.join(os.path.dirname(__file__), "template/writer"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            #ui_modules={"Entry": EntryModule},
            #xsrf_cookies=True,
            cookie_secret="11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/writer/signin/",
        )
        tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)

def main():
    wsgiref.handlers.CGIHandler().run(Application())

if __name__ == "__main__":
    main()
