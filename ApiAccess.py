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

class RegisteredApplications(db.Model):
    #AppId is the key!
    appName = db.StringProperty()

class PermanentAccessCodes(db.Model):
    app = db.ReferenceProperty(RegisteredApplications)
    authenticated = db.IntegerProperty()
    accessToken = db.StringProperty()
    passCode = db.StringProperty()
    user = db.ReferenceProperty(GrafiteUser)
    timestampLastAccessed = db.DateTimeProperty()
    timestampCreated = db.DateTimeProperty()
    
    @staticmethod
    def new():
        obj = PermanentAccessCodes()
        obj.passCode = str(uuid.uuid4())
        obj.authenticated = 0
        obj.timestampLastAccessed = obj.timestampCreated = datetime.now()
        obj.put()
        return obj
    
    @staticmethod
    def clean():
        pass
    
    @staticmethod
    def register(passCode):
        res = PermanentAccessCodes.all().filter("passCode =",passCode)
        if not res.count():
            return {"result":"error","message":"Invalid PassCode"}
        obj = res.fetch(1)[0]
        obj.authenticated = 1
        obj.timestampLastAccessed = datetime.now()
        obj.accessToken = str(uuid.uuid4())
        obj.passCode = ''
        obj.put()
        return {"result":"success","pac":obj.accessToken}
    
    @staticmethod
    def unregister(at):
        res = PermanentAccessCodes.all().filter("accessToken =",at)
        if not res.count():
            return {"result":"error","message":"Invalid AccessToken"}
        obj = res.fetch(1)[0]
        obj.delete()
        return {"result":"success"}
    
    @staticmethod
    def getUserAccessToken(pac):
        res = PermanentAccessCodes.all().filter("accessToken =",pac)
        if res.count()!=1:
            return {"result":"error","message":"Invalid PAC"}
        res = res.fetch(1)[0]
        res, userAt,t = GrafiteUser.login(res.user.key().name(),res.user.password, res.app.appName)
        if res != "success":
            return {"result":"error","message":"Unable to login user!"}
        return {"result":"success","AccessToken":userAt}
    
class ApiAccessService(webapp.RequestHandler):
    def get(self,job):
        appid = self.request.get("appid")
        if appid in (None,""):
            self.error(404)
            return
        if job not in ("register",):
            self.error(404)
            return

        class temp:
            pass
        DATA = temp()
        #check user logged in.
        DATA.user = UserService.getCurrentUser(self)
        if not DATA.user:
            url = urllib.quote("/api/register?appid=%s"%appid)
            self.redirect("/login?to="+url)
            self.error(302)
            return
        
        app = RegisteredApplications.get_by_key_name(appid)
        if app is None:
            self.response.out.write("Invalid application!")
            return

        res = PermanentAccessCodes.all().filter("user = ",DATA.user).filter("app =",app)
        
        if res.count():
            DATA.apiAccess = res.fetch(1)[0]
            DATA.apiAccess.passCode = str(uuid.uuid4())
        else:
            DATA.apiAccess = PermanentAccessCodes.new()
            DATA.apiAccess.user = DATA.user
            DATA.apiAccess.app = app
        DATA.apiAccess.put()
        path = os.path.join(os.path.dirname(__file__), 'html/appaccess.html')
        self.response.out.write(render(path, {'DATA':DATA}))

    def post(self,job):
        t = self.request.get("t")
        self.response.headers["Content-Type"] = "application/json"
        if t not in ("register","unregister","getUserAccessToken","getUserDetails"):
            self.response.out.write(json.dumps({"result":"error","message":"Invalid type! %s"%t}))
            return
        
        self.response.out.write(json.dumps(getattr(self,"post_" + t)()))
    
    def post_register(self):
        code = self.request.get("code")
        if code in (None,""):
            return {"result":"error","message":"Invalid code"}
            
        return PermanentAccessCodes.register(code)
    
    def post_unregister(self):
        code = self.request.get("pac")
        if code in (None,""):
            return {"result":"error","message":"Invalid PAC"}
            
        return PermanentAccessCodes.unregister(code)
        
    def post_getUserAccessToken(self):
        pac = self.request.get("pac")
        if pac in (None,""):
            return {"result":"error","message":"Invalid PAC"}
            
        return PermanentAccessCodes.getUserAccessToken(pac)
        
    def getUserDetails(self):
        if pac in (None,""):
            return {"result":"error","message":"Invalid PAC"}
        
        return {"nickname":x.Nickname,"url":x.profileUrl,"dp":x.displayPicture}