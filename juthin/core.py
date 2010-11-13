from google.appengine.ext import db
from google.appengine.api import memcache
from django.utils import simplejson
from datetime import tzinfo, datetime, timedelta

class Entry(db.Model):
    id = db.IntegerProperty()
    uid = db.IntegerProperty()
    created = db.IntegerProperty()
    title = db.StringProperty()
    slug = db.StringProperty()
    tags = db.StringListProperty()
    content = db.TextProperty()
    hits = db.IntegerProperty()
    lastmodify = db.IntegerProperty()

class Author(db.Model):
    id = db.IntegerProperty()
    name = db.StringProperty()
    nickname = db.StringProperty()
    passwd = db.StringProperty()
    description = db.StringProperty()
    lastlogin = db.IntegerProperty()
    blog_title = db.StringProperty()
    blog_theme = db.StringProperty()
    blog_domain = db.StringProperty()
    blog_timezone = db.IntegerProperty()
    sync_key = db.StringProperty()
    twitter_oauth = db.IntegerProperty()
    twitter_oauth_key = db.StringProperty()
    twitter_oauth_secret = db.StringProperty()
    twitter_oauth_string = db.StringProperty()
    twitter_id = db.IntegerProperty()
    twitter_name = db.StringProperty()
    twitter_screen_name = db.StringProperty()
    twitter_location = db.StringProperty()
    twitter_description = db.StringProperty()
    twitter_profile_image_url = db.StringProperty()
    twitter_url = db.StringProperty()
    twitter_statuses_count = db.IntegerProperty()
    twitter_followers_count = db.IntegerProperty()
    twitter_friends_count = db.IntegerProperty()
    twitter_favourites_count = db.IntegerProperty()

class Tags:
    def __init__(self):
        pass
    
    def mapping(self):
        if memcache.get('mapping'):
            return simplejson.loads(memcache.get('mapping'))
        entries = Entry.all()
        mapping = {}
        for item in entries:
            for tag in item.tags:
                if not tag:
                    continue
                elif tag in mapping:
                    mapping[tag].append(item.id)
                else:
                    mapping[tag] = [item.id]
        memcache.add('mapping', simplejson.dumps(mapping), 3600 * 24)
        return mapping 

    def cloud(self):
        if memcache.get('cloud'):
            return simplejson.loads(memcache.get('cloud'))
        entries = Entry.all()
        cloud = []
        for item in entries:
            for tag in item.tags:
                if tag and tag not in cloud:
                    cloud.append(tag)
        memcache.add('cloud', simplejson.dumps(cloud), 3600 * 24)
        return cloud
