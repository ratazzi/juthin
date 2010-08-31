from google.appengine.ext import db
from google.appengine.api import memcache
from django.utils import simplejson
from datetime import tzinfo, datetime, timedelta

class Entry(db.Model):
    id = db.IntegerProperty()
    uid = db.IntegerProperty()
    created = db.IntegerProperty()
    title = db.StringProperty()
    tags = db.StringListProperty()
    content = db.TextProperty()
    hits = db.IntegerProperty()
    lastmodify = db.IntegerProperty()

class Author(db.Model):
    id = db.IntegerProperty()
    name = db.StringProperty()
    nickname = db.IntegerProperty()
    passwd = db.StringProperty()
    description = db.StringProperty()
    url = db.StringProperty()
    lastlogin = db.IntegerProperty()

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

class Helper:
    def __init__(self):
        pass

    def format_date(self, date):
        return datetime.fromtimestamp(date, tzinfo=GMT8).strftime('%d-%b-%Y %H:%M')

class GMT8(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=5,minutes=30)

    def tzname(self, dt):
        return 'GMT +8'

    def dst(self, dt):
        return timedelta(0)
