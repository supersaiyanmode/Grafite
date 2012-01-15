from google.appengine.ext import db
from google.appengine.ext import webapp
from UserService import GrafiteUser,UserService
from google.appengine.api import taskqueue
from datetime import *
from django.utils import simplejson as json

class RemindersOld(db.Model):
    text = db.StringProperty(multiline=True)
    timeAdded = db.DateTimeProperty(auto_now_add=True)
    remindTime = db.DateTimeProperty(required=True)
    user = db.ReferenceProperty(GrafiteUser,required=True)

class Reminder(db.Model):
    text = db.StringProperty(multiline=True)
    timeAdded = db.DateTimeProperty(auto_now_add=True)
    remindTime = db.DateTimeProperty(required=True)
    user = db.ReferenceProperty(GrafiteUser,required=True)

class ReminderService(webapp.RequestHandler):
    def get(self):
        if self.request.get("password")=="thrustmaximum":
            ReminderService.executeReminders()
            return
        self.response.headers.add_header("Content-Type","application/json")
        user = UserService.getCurrentUserOrJsonError(self)
        if not user:
            return
        res = {}
        res['old'] = map(lambda x:{"text":x.text,"time":x.remindTime.isoformat()},RemindersOld.all().filter("user = ",user).fetch(10))
        res['pending'] = map(lambda x:{"text":x.text,"time":x.remindTime.isoformat()},Reminder.all().filter("user = ",user).fetch(10))
        self.response.out.write(json.dumps({"result":"success","data":res}))
        

    def post(self):
        self.response.headers.add_header("Content-Type","application/json")
        if self.request.get("type") != "add":
            self.response.out.write(json.dumps({"result":"error","message":"Bad type"}))
            return
        user = UserService.getCurrentUserOrJsonError(self)
        if not user:
            return
        if self.request.get("text") in (None,""):
            self.response.out.write(json.dumps({"result":"error","message":"Bad text"}))
            return
        if self.request.get("time") in (None,""):
            self.response.out.write(json.dumps({"result":"error","message":"Bad Time"}))
            return
        text = self.request.get('text')
        time = self.request.get('time')
        try:
            [v,t] = time.split(' ')
            res = ReminderService.addReminder(v,t,text,user)
            if not res:
                self.response.out.write(json.dumps({"result":"error","message":"Bad Time Specification"}))
                return
        except:
            self.response.out.write(json.dumps({"result":"error","message":"Bad Time Specification format"}))
            return
        self.response.out.write(json.dumps({"result":"success"}))


    @staticmethod
    def getCount():
        return Reminder.all().count() + RemindersOld.all().count()
        
    @staticmethod
    def getUserCount(user):
        return Reminder.all().filter("user = ",user).count() + RemindersOld.all().filter("user = ",user).count()

    @staticmethod
    def addReminder(timeVal, timeType, text,user):
        d = None
        try:
            d = eval('timedelta(%s=%s)'%(timeType,timeVal))
        except Exception,e:
            return None
        
        r = Reminder(text=text, user=user, remindTime=datetime.now()+d)
        return r.put()

    @staticmethod
    def executeReminders():
        import XMPPService
        now = datetime.now()
        toDelete = []
        toOld = []
        for x in Reminder.all().order("remindTime"):
            if x.remindTime <= now:
                XMPPService.MyXmppHandler.pingUser(x.user,"*Reminder:* " + x.text)
                toDelete.append(x)
                toOld.append(RemindersOld(text=x.text,timeAdded=x.timeAdded,
                remindTime=x.remindTime, user=x.user))
            else:
                break
        db.delete(toDelete)
        db.put(toOld)