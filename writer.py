#!/usr/bin/env python
# encoding=utf-8

import os.path
import re
import sys, os
import datetime, time
import tornado.options
import tornado.web
import tornado.wsgi
import wsgiref.handlers
import unicodedata
import hashlib
from tornado.options import define, options
from google.appengine.ext import db
from django.utils import simplejson
from google.appengine.api import memcache

from juthin.core import Entry, Tags, Author

from twitter.oauthtwitter import OAuthApi
from twitter.oauth import OAuthToken
import config

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id: 
            return None
        else:
            return True

    def get_author(self):
        return Author.all().get()

class OverviewHandler(BaseHandler):
    @tornado.web.signin
    def get(self):
        rs = db.GqlQuery('SELECT * FROM Entry ORDER BY created DESC LIMIT 25')
        entries = rs.fetch(25)
        self.render('overview.html', entries=entries, author=self.get_author())

class NewHandler(BaseHandler):
    @tornado.web.signin
    def get(self):
        self.render('new.html', author=self.get_author())

    @tornado.web.signin
    def post(self):
        last = Entry.all().order('-created').get()
        entry = Entry()
        if last:
            entry.id = last.id + 1
        else:
            entry.id = 1
        entry.created = int(time.time())
        entry.title = self.get_argument('title', default='', strip=True)
        entry.slug = self.get_argument('slug', default='', strip=True)
        entry.tags = [item for item in self.get_argument('tags', default='', strip=True).split(',')]
        entry.content = self.get_argument('content', default='', strip=True)
        entry.hits = 0
        entry.lastmodify = int(time.time())
        entry.put()
        self.redirect('/writer/')

class UpdateHandler(BaseHandler):
    @tornado.web.signin
    def get(self, id):
        rs = db.GqlQuery('SELECT * FROM Entry WHERE id = :1', int(id))
        entry = rs.get()
        self.render('update.html', entry=entry, author=self.get_author())

    @tornado.web.signin
    def post(self, id):
        id = int(id)
        rs = db.GqlQuery('SELECT * FROM Entry WHERE id = :1', id)
        entry = rs.get()
        entry.title = self.get_argument('title', default='', strip=True)
        entry.slug = self.get_argument('slug', default='', strip=True)
        entry.tags = [item for item in self.get_argument('tags', default='', strip=True).split(',')]
        entry.content = self.get_argument('content', default='', strip=True)
        entry.lastmodify = int(time.time())
        db.put(entry)
        self.redirect('/writer/')

class RemoveHandler(BaseHandler):
    @tornado.web.signin
    def get(self, id):
        rs = db.GqlQuery('SELECT * FROM Entry WHERE id = :1', int(id))
        entry = rs.get()
        db.delete(entry)
        self.redirect('/writer/')

class TwitterHandler(BaseHandler):
    @tornado.web.signin
    def post(self):
        status = self.get_argument('status')
        author = Author.all().get()
        if author.twitter_oauth == 1:
            access_token = OAuthToken.from_string(author.twitter_oauth_string)
            twitter = OAuthApi(config.CONSUMER_KEY, config.CONSUMER_SECRET, access_token)
            try:
                twitter.PostUpdate(status.encode('utf-8'))
            except:
                logging.error('Failed to tweet: ' + status)
        self.redirect('/writer/')

class TwitterLinkHandler(BaseHandler):
    @tornado.web.signin
    def get(self):
        twitter = OAuthApi(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        request_token = twitter.getRequestToken()
        authorization_url = twitter.getAuthorizationURL(request_token)
        memcache.delete('request_token')
        memcache.add('request_token', request_token, 3600)
        self.redirect(authorization_url)

class TwitterCallbackHandler(BaseHandler):
    @tornado.web.signin
    def get(self):
        request_token = memcache.get('request_token')
        twitter = OAuthApi(config.CONSUMER_KEY, config.CONSUMER_SECRET, request_token)
        access_token = twitter.getAccessToken()
        twitter = OAuthApi(config.CONSUMER_KEY, config.CONSUMER_SECRET, access_token)
        user = twitter.GetUserInfo()
        author = Author.all().get()
        author.twitter_oauth = 1
        author.twitter_oauth_key = access_token.key
        author.twitter_oauth_secret = access_token.secret
        author.twitter_oauth_string = access_token.to_string()
        author.twitter_id = int(user.id)
        author.twitter_name = user.name
        author.twitter_screen_name = user.screen_name
        author.twitter_location = user.location
        author.twitter_description = user.description
        author.twitter_profile_image_url = user.profile_image_url
        author.twitter_url = user.url
        author.twitter_statuses_count = user.statuses_count
        author.twitter_followers_count = user.followers_count
        author.twitter_friends_count = user.friends_count
        author.twitter_favourites_count = user.favourites_count
        author.put()
        self.redirect('/writer/settings/')

class SettingsHandler(BaseHandler):
    @tornado.web.signin
    def get(self):
        author = Author.all().get()
        self.render('settings.html', author=author)

    @tornado.web.signin
    def post(self):
        author = Author.all().get()
        if not author:
            author = Author()

        author.name = 'ratazzi'
        author.nickname = 'Ratazzi'
        author.blog_title = self.get_argument('blog_title', default='', strip=True)
        author.blog_theme = self.get_argument('blog_theme', default='default', strip=True)
        author.blog_domain = self.get_argument('blog_domain', default='', strip=True)
        author.blog_timezone = int(self.get_argument('blog_timezone', default=0, strip=True))
        author.sync_key = self.get_argument('sync_key', default='', strip=True)
        author.twitter_user = self.get_argument('twitter_user', default='', strip=True)
        author.twitter_passwd = self.get_argument('twitter_passwd', default='', strip=True)
        author.put()
        self.redirect('/writer/')

class PasswdHandler(BaseHandler):
    @tornado.web.signin
    def post(self):
        author = Author.all().get()
        new_passwd = self.get_argument('new_passwd')
        confirm = self.get_argument('confirm')
        if new_passwd == confirm:
            author.passwd = hashlib.md5(new_passwd).hexdigest()
            author.put()
            self.redirect('/writer/')
        else:
            self.write('两次输入的密码不一致')

class EntrySyncHandler(BaseHandler):
    def post(self):
        error = {'status':'Access Denied.'}
        author = Author.all().get()
        if not self.get_arguments('key') or not author:
            self.write(simplejson.dumps(error))
            return
        if self.get_argument('key') != author.sync_key:
            self.write(simplejson.dumps(error))
            return

        entry = Entry()
        entry.id = int(self.get_argument('id'))
        entry.created = int(self.get_argument('created'))
        entry.title = self.get_argument('title')
        entry.tags = [item for item in self.get_argument('tags').split(',')]
        entry.content = self.get_argument('content')
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
        author = Author.all().get()
        if (user == author.name) and (hashlib.md5(passwd).hexdigest() == author.passwd):
            self.set_secure_cookie('user', user)
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
            (r"/writer/settings/", SettingsHandler),
            (r"/writer/passwd/", PasswdHandler),
            (r"/writer/signin/", SigninHandler),
            (r"/writer/signout/", SignoutHandler),
            (r"/twitter/tweet/", TwitterHandler),
            (r"/twitter/link/", TwitterLinkHandler),
            (r"/oauth/twitter/callback/", TwitterCallbackHandler),
            (r"/entry/sync/", EntrySyncHandler),
        ]
        author = Author.all().get()
        settings = dict(
            blog_title = author.blog_title,
            blog_domain = author.blog_domain,
            blog_timezone = author.blog_timezone,
            blog_author = author.nickname,
            template_path = os.path.join(os.path.dirname(__file__), "template/writer"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret = "11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url = "/writer/signin/",
            debug = os.environ.get("SERVER_SOFTWARE", "").startswith("Development/"),
        )
        tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)

def main():
    wsgiref.handlers.CGIHandler().run(Application())

if __name__ == "__main__":
    main()
