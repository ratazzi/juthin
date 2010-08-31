#!/usr/bin/env python
# encoding=utf-8

import os.path
import re
import sys,os
import tornado.options
import tornado.web
import tornado.wsgi
from tornado.escape import *
from tornado.options import define, options
import wsgiref.handlers
import unicodedata
import yaml
from juthin.core import Entry, Tags, Helper
from google.appengine.ext import db
from django.utils import simplejson

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id: return None

class MainHandler(BaseHandler):
    def get(self):
        rs = db.GqlQuery('SELECT * FROM Entry ORDER BY created DESC')
        entries = rs.fetch(10)
        clouds = Tags().cloud()
        mapping = Tags().mapping()
        #self.write(simplejson.dumps(mapping))
        self.render('index.html', entries=entries, clouds=clouds)

class ViewHandler(BaseHandler):
    def get(self, id):
        id = int(id)
        rs = db.GqlQuery('SELECT * FROM Entry WHERE id = :1', id)
        mapping = Tags().mapping()
        entry = rs.get()
        ids = []
        for tags in entry.tags:
            if tags in mapping:
                for tag in mapping[tags]:
                    if tag not in ids and tag != id:
                        ids.append(tag)
        if ids:
            rs = db.GqlQuery('SELECT * FROM Entry WHERE id IN :1', ids)
            related = rs.fetch(10)
        else:
            related = []
        #self.write(simplejson.dumps(ids))
        clouds = Tags().cloud()
        self.render('view.html', entry=entry, clouds=clouds, mapping=mapping, related=related)

class TagsHandler(BaseHandler):
    def get(self, tag):
        mapping = Tags().mapping()
        tag = url_unescape(tag)
        if tag in mapping and mapping[tag]:
            rs = db.GqlQuery('SELECT * FROM Entry WHERE id IN :1  ORDER BY created DESC', mapping[tag])
            entries = rs.fetch(10)
            clouds = Tags().cloud()
            self.render('index.html', entries=entries, clouds=clouds, mapping=mapping)
        else:
            self.redirect('/')

"""class HomeHandler(BaseHandler):
    def get(self):
        entries = self.db.query("SELECT * FROM entries ORDER BY published "
                                "DESC LIMIT 5")
        if not entries:
            self.redirect("/compose")
            return
        self.render("home.html", entries=entries)


class EntryHandler(BaseHandler):
    def get(self, slug):
        entry = self.db.get("SELECT * FROM entries WHERE slug = %s", slug)
        if not entry: raise tornado.web.HTTPError(404)
        self.render("entry.html", entry=entry)


class FeedHandler(BaseHandler):
    def get(self):
        entries = self.db.query("SELECT * FROM entries ORDER BY published "
                                "DESC LIMIT 10")
        self.set_header("Content-Type", "application/atom+xml")
        self.render("feed.xml", entries=entries)


class ComposeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        id = self.get_argument("id", None)
        entry = None
        if id:
            entry = self.db.get("SELECT * FROM entries WHERE id = %s", int(id))
        self.render("compose.html", entry=entry)

    @tornado.web.authenticated
    def post(self):
        id = self.get_argument("id", None)
        title = self.get_argument("title")
        text = self.get_argument("markdown")
        html = markdown.markdown(text)
        if id:
            entry = self.db.get("SELECT * FROM entries WHERE id = %s", int(id))
            if not entry: raise tornado.web.HTTPError(404)
            slug = entry.slug
            self.db.execute(
                "UPDATE entries SET title = %s, markdown = %s, html = %s "
                "WHERE id = %s", title, text, html, int(id))
        else:
            slug = unicodedata.normalize("NFKD", title).encode(
                "ascii", "ignore")
            slug = re.sub(r"[^\w]+", " ", slug)
            slug = "-".join(slug.lower().strip().split())
            if not slug: slug = "entry"
            while True:
                e = self.db.get("SELECT * FROM entries WHERE slug = %s", slug)
                if not e: break
                slug += "-2"
            self.db.execute(
                "INSERT INTO entries (author_id,title,slug,markdown,html,"
                "published) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP())",
                self.current_user.id, title, slug, text, html)
        self.redirect("/entry/" + slug)


class AuthLoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()
    
    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Google auth failed")
        author = self.db.get("SELECT * FROM authors WHERE email = %s",
                             user["email"])
        if not author:
            # Auto-create first author
            any_author = self.db.get("SELECT * FROM authors LIMIT 1")
            if not any_author:
                author_id = self.db.execute(
                    "INSERT INTO authors (email,name) VALUES (%s,%s)",
                    user["email"], user["name"])
            else:
                self.redirect("/")
                return
        else:
            author_id = author["id"]
        self.set_secure_cookie("user", str(author_id))
        self.redirect(self.get_argument("next", "/"))


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))


class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="blog", help="blog database name")
define("mysql_user", default="root", help="blog database user")
define("mysql_password", default="linux520", help="blog database password")"""
define("theme", default="default", help="blog theme")

class Application(tornado.wsgi.WSGIApplication):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/view/([0-9]+).html", ViewHandler),
            (r"/tags/([^/]+)?", TagsHandler),
        ]
        settings = dict(
            blog_title=u"Ratazzi's Blog",
            domain='www.ratazzi.org',
            author='Ratazi',
            template_path=os.path.join(os.path.dirname(__file__), "template/" + options.theme),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            #ui_modules={"Entry": EntryModule},
            xsrf_cookies=True,
            cookie_secret="11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/auth/login",
        )
        tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        """self.db = tornado.database.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)"""

def main():
    wsgiref.handlers.CGIHandler().run(Application())

if __name__ == "__main__":
    main()
