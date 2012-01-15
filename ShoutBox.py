from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api.urlfetch import fetch as urlfetch
from django.utils import simplejson as json
from google.appengine.ext.webapp.template import render
from google.appengine.ext import db
import logging
import urllib
import os
from UserService import GrafiteUser,UserService
import uuid
from datetime import timedelta,datetime

class ShoutBoxMessages(db.Model):
    message = db.StringProperty()
    user = db.ReferenceProperty(GrafiteUser)
    time = db.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def getShouts():
        arr = ShoutBoxMessages.all().order("time").fetch(100)
        arr = map(lambda x: {"user":{"nickname":x.user.Nickname, "dp":x.user.displayPicture,"url":x.user.profileUrl}, "message":x.message, "time":x.time.isoformat()}, arr)
        return arr
    
    @staticmethod
    def shout(message, user):
        s = ShoutBoxMessages(message=message,user=user)
        s.put()
        return s
        
    
class ShoutBoxService(webapp.RequestHandler):
    def get(self):
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(json.dumps({"result":"success","data":ShoutBoxMessages.getShouts()}))

    def post(self):
        self.response.headers["Content-Type"] = "application/json"
        user = UserService.getCurrentUserOrJsonError(self)
        if not user:
            return
        msg = self.request.get("message")
        shouts = ShoutBoxMessages.getShouts()
        if msg in (None,""):
            self.response.out.write(json.dumps({"result":"error","message":"No body!"}))
            return
        res = ShoutBoxMessages.shout(msg,user)
        shouts.extend(map(lambda x: {"user":{"nickname":x.user.Nickname, "dp":x.user.displayPicture,"url":x.user.profileUrl}, "message":x.message, "time":x.time.isoformat()}, [res]))
        self.response.out.write(json.dumps({"result":"success","data":shouts}))