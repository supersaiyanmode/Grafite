from google.appengine.ext import db
from google.appengine.ext import webapp
from UserService import UserService
from UserService import GrafiteUser
from django.utils import simplejson as json
from FacebookService import FacebookService
from TwitterService import TwitterService
from BuzzService import BuzzService
import re

class Status(db.Model):
    text = db.StringProperty(multiline=True)
    timestamp = db.DateTimeProperty(auto_now_add=True)
    service = db.StringProperty()
    user = db.ReferenceProperty(GrafiteUser,required=True)

    @staticmethod
    def _addStatus(text,user,service):
        s = Status(text=text, user=user, service=service)
        return s.put()

    @staticmethod
    def getTotalStatuses():
        return Status.all().count()


class StatusService(webapp.RequestHandler):
    def post(self):
        user = UserService.getCurrentUserOrJsonError(self)
        if not user:
            return
        
        s = []
        if self.request.get("services"):
            s = self.request.get("services").split(",")

        self.response.headers.add_header("Content-Type","application/json")
        self.response.out.write(json.dumps(StatusService.updateStatus(self.request.get("status"),user,s,{})))
            
    @staticmethod
    def updateStatus(status,user,services=['Facebook','Buzz','Twitter'],settings={}):
        if status in (None,""):
            {"result":"error","message":"Empty Status"}
            return
        urlMatchObj = re.search("((https?|ftp):\/\/)?([-a-z0-9+&@#\/%?=~_|!:,;]{2,}\.)+[-a-z0-9+&@#\/%=~_|]+", status,re.IGNORECASE)
        urlMatch = status[urlMatchObj.start():urlMatchObj.end()] if urlMatchObj else None
        
        s = ['Facebook','Buzz','Twitter']
        services = list(set(services) & set(s))
        if services == []:
            return {"result":"error","message":"Service specification error!"}

        res = {}
        statusObj = {"status":status,"settings":settings}
        if urlMatch:
            from LinkFetcher import LinkFetcher
            try:
                lf = LinkFetcher(urlMatch)
                statusObj['link'] = {}
                statusObj['link']['url'] = lf.url()
                statusObj['link']['description'] = lf.description()
                statusObj['link']['title'] = lf.title()
            except Exception,e:
                pass
            
        for s in services:
            obj = eval(s + 'Service').updateStatus(user,statusObj)
            if obj and obj['result']=='success':
                res[s] = obj
                Status._addStatus(status,user,s)
            else:
                res[s] = obj
        ret = {}
        ret['result'] = "success"
        ret['data'] = res
        return ret
        
    @staticmethod
    def getUserStatusCount(user):
	resFB = Status.all().filter("user = ", user).filter("service = ","Facebook").count()
	resBuzz = Status.all().filter("user = ", user).filter("service = ","Buzz").count()
	resTwitter = Status.all().filter("user = ", user).filter("service = ","Twitter").count()
	return {"Facebook":resFB,"Twitter":resTwitter,"Buzz":resBuzz, "Total":resFB+resBuzz+resTwitter}
	
    @staticmethod
    def getUserStatuses(user):
	return Status.all().filter("user = ", user).order("-timestamp").fetch(20)
	
