from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp.template import render
from google.appengine.api.urlfetch import fetch as urlfetch
import logging
import cgi

from django.utils import simplejson as json
import datetime
import urllib


from google.appengine.ext import db
import uuid
import os
import os.path

from ImageServer import ImageMap
time_format = "%a, %d %b %Y %H:%M:%S %Z"

class GrafiteUser(db.Model):
    nickname = db.StringProperty()
    password = db.StringProperty()
    dateJoined = db.DateTimeProperty()
    emailId = db.StringProperty()

    twitter = db.StringProperty()
    facebook = db.StringProperty()
    google = db.StringProperty()
    
    dateLastAccessed = db.DateTimeProperty(auto_now_add=True)
    accessToken = db.StringProperty()
    client=db.StringProperty()
    settings = db.StringProperty()
    
            
    @property
    def profileUrl(self):
        if hasattr(self,'nickname') and self.nickname:
            return "/users/"+self.nickname
        return "/users/"+str(self.key())
    
    @property
    def displayPicture(self):
        if ImageMap.exists(str(self.key())):
            return "/dp/%s/"%str(self.key())
        return "/images/dp/"+"default.jpg"

    @property
    def Nickname(self):
        if hasattr(self,'nickname') and self.nickname:
            return self.nickname
        return self.key().name()[:3] + "..." + self.key().name()[self.key().name().find("@"):]
	    
    @staticmethod
    def getExpirationTimeSpan():
        return datetime.timedelta(hours=5)

    def getLoginExpirationTime(self):
        return self.dateLastAccessed + GrafiteUser.getExpirationTimeSpan()
    
    
    @staticmethod
    def _createNewUser(obj):
        username,password,emailid = obj
        if GrafiteUser.get_by_key_name(username) is None:
            newUser = GrafiteUser(key_name=username)
            newUser.password = password
            newUser.dateJoined = newUser.dateLastAccessed = datetime.datetime.now()
            newUser.client = "Browser"
            newUser.accessToken = None
            newUser.put()
            return newUser
        else:
            return None

    @staticmethod
    def createNewUser(username,password,client):
        newUser = db.run_in_transaction(GrafiteUser._createNewUser,(username,password,client))
        if newUser is not None:
            newUser.accessToken = GrafiteUser._generateNewAccessToken(32)
            newUser.put()
            return ("success",newUser.accessToken,newUser.getLoginExpirationTime())
        else:
            return ("error","user already exists",None)

    @staticmethod
    def _generateNewAccessToken(length):
        accessToken = str(uuid.uuid4())
        while GrafiteUser.getUser(accessToken=accessToken) is not None:
            accessToken = str(uuid.uuid4()) #.bytes.encode("base64")[:length]
        return accessToken
    
    @staticmethod
    def checkAccessTokenValidity(username, token):
        if token is None or str(token) == '':
            return False
        
        user = GrafiteUser.getUser(accessToken=token)
        if user is None or user.key().name()!=username:
            return False
        return True
    
    @staticmethod
    def login(username,password,client):
        user = GrafiteUser.get_by_key_name(username)
        if user is None:
            return ("error","user doesn't exist",None)
        if user.password != password:
            return ("error","Invalid Credentials",None)
        user.client = client
        if not GrafiteUser.checkAccessTokenValidity(user.key().name(), user.accessToken):
            user.accessToken = GrafiteUser._generateNewAccessToken(32)
        user.dateLastAccessed = datetime.datetime.now()
        user.put()
        return ("success",user.accessToken,user.getLoginExpirationTime())

    @staticmethod
    def getAllUsers():
        return '\n'.join([repr({"id":x.key().name(), "access_token":x.accessToken, "dateLastAccessed":x.dateLastAccessed}) for x in db.GqlQuery("select * from User")])
	
    @staticmethod
    def getUser(username=None, accessToken=None):
        if username is not None:
            user = GrafiteUser.get_by_key_name(username)
            if user is not None:
                user.dateLastAccessed = datetime.datetime.now()
                user.put()
                return user
            else:
                return None
        elif accessToken is not None:
            res = db.GqlQuery("Select * from GrafiteUser where accessToken= :1", accessToken)
            user = None
            for x in res:
                user = x
                break
            if user is None:
                return None

            if user.getLoginExpirationTime() > datetime.datetime.now():
                user.dateLastAccessed = datetime.datetime.now()
                user.put()
                return user
            return None
        else:
            return None
        
    @staticmethod
    def getOnlineUsers():
        res = GrafiteUser.all().filter("dateLastAccessed >= ", datetime.datetime.now() - GrafiteUser.getExpirationTimeSpan()).order("dateLastAccessed")
        arr = res.fetch(20)
        arr = map(lambda x: {"ProfileUrl": x.profileUrl, "Nickname":x.Nickname, "dpUrl":x.displayPicture}, arr)
        return {"count":res.count(), "value":arr}


class UserService(webapp.RequestHandler):
    def get(self):
        class temp:
            pass
        DATA = temp()
        DATA.user = UserService.getCurrentUserOrRedirect(self)
        if not DATA.user:
            return

        try:
            DATA.settings = json.loads(user.settings)
        except Exception,err:
            obj = {"TwitterShortenURL":False,"TwitterSplitStatus":False}
            DATA.user.settings = json.dumps(obj)
            DATA.user.put()
            DATA.settings = obj
        
        from TwitterService import TwitterStatusUpdater
        from FacebookService import FacebookStatusUpdater
        from BuzzService import BuzzStatusUpdater
        DATA.DPList = []
        for x in ['Buzz', 'Facebook', 'Twitter']:
            obj = eval(x+"StatusUpdater").getAuthenticationStatus(DATA.user)
            if obj[0] == "":
                DATA.DPList.append({"path":obj[1].getDPSrc(),"service":x})
            
        path = os.path.join(os.path.dirname(__file__), 'html/accounts.html')
        self.response.out.write(render(path, {'DATA':DATA}))
        
    def post(self):
        requestType = self.request.get("type")
        if requestType == "add":
            newUserID = self.request.get("user")
            password = self.request.get("password")
            client = self.request.get("client")

            if self.checkRequest([newUserID,password,client]):
                res,msg,expire = GrafiteUser.createNewUser(newUserID,password,client)
                if res == "success":
                    if self.request.get("alt")=="json":
                        self.response.headers['Content-Type'] = 'application/json'
                        self.response.out.write(json.dumps({"result":res,"access_token":msg,"expires":expire.strftime(time_format)}))
                    else:
                        self.response.headers['Set-Cookie'] = UserService.makeCookieString(expire,{"access_token":msg})
                        self.response.headers['Content-Type'] = "text/html"
                        self.response.out.write('<meta http-equiv="refresh" content="1;url=/userHome">Redirecting..')
                else:
                    if self.request.get("alt")=="json":
                        self.response.headers['Content-Type'] = 'application/json'
                        self.response.out.write(json.dumps({"result":res,"message":msg}))
                    else:
                        self.response.out.write('<meta http-equiv="refresh" content="1;url=/login">%s. Redirecting..'%msg)
        elif requestType == "login":
            userID = self.request.get("user")
            password = self.request.get("password")
            client = self.request.get("client")
            #self.response.out.write('\n'.join([str(k)+":"+str(v) for k,v in self.request.cookies.iteritems()]))
            if not self.checkRequest([userID,password,client]):
                return
            res,msg,expire = GrafiteUser.login(userID,password,client)
            if expire is not None:
                expire = expire.strftime(time_format)
            if res == "success":
                if self.request.get("alt")=="json":
                    self.response.headers['Content-Type'] = 'application/json'
                    self.response.out.write(json.dumps({"result":res,"access_token":msg,"expires":expire}))
                else:
                    self.response.headers.add_header('Set-Cookie',UserService.makeCookieString(expire,{"access_token":msg}))
                    self.response.headers.add_header('Content-Type','Text/html')
                    self.response.out.write('<meta http-equiv="refresh" content="1;url=%s">Redirecting..'%self.request.get("to"))
            else:
                if self.request.get("alt")=="json":
                    self.response.headers['Content-Type'] = 'application/json'
                    self.response.out.write(json.dumps({"result":res,"message":msg}))
                else:
                    self.response.out.write('<meta http-equiv="refresh" content="1;url=/login">Invalid credentials. Redirecting..')
                #x = self.request.headers.get("Cookie")
                #self.response.out.write("Cookie="+x)
        
        elif requestType == "logout":
            user = UserService.getCurrentUserOrRedirect(self)
            if not user:
                return

            user.accessToken = ''
            user.put()
            if self.request.get("alt") and self.request.get("alt")=="json":
                self.response.out.write(json.dumps({"result":"success"}))
            else:
                self.redirect("/")

        elif requestType == 'settings':
            user = UserService.getCurrentUserOrJsonError(self)
            if not user:
                return
            
            subtype = self.request.get("subtype")
            if subtype not in ("displaypicture","password","nickname"):
                self.response.out.write(json.dumps({"result":"error","message":"bad subtype"}))
                return
            
            if subtype == "displaypicture":
                if self.request.get("dpUrl") in (None,""):
                    self.response.out.write(json.dumps({"result":"error","message":"No dpUrl"}))
                    return
                #fetch the url, save the image
                res = ImageMap.updateImage(str(user.key()), self.request.get("dpUrl"))
                if res['result'] == "success":
                    res['url'] = "/dp/%s/"%res['key']
                self.response.out.write(json.dumps(res))
                return
            
            elif subtype == "nickname":
                nick = self.request.get("nickname")
                if nick in (None,""):
                    self.response.out.write(json.dumps({"result":"error","message":"Improper Nickname"}))
                    return
                if GrafiteUser.all().filter("nickname=",nick).count():
                    self.response.out.write(json.dumps({"result":"error","message":"duplicate nickname"}))
                    return
                user.nickname = nick
                user.put()
                self.response.out.write(json.dumps({"result":"success"}))
                return
            elif subtype == "password":
                pass
            return
            
            twitterShortenUrl = False
            twitterSplitStatus = False
            if self.request.get("ShortenUrl") not in (None,""):
                twitterShortenUrl = True
            if self.request.get("SplitStatus") not in (None,""):
                twitterSplitStatus = True
            
            user.nickname = nick
            user.settings = json.dumps({"TwitterShortenURL":twitterShortenUrl,
                        "TwitterSplitStatus":twitterSplitStatus})
            user.put()
            if self.request.get("alt") and self.request.get("alt")=="json":
                self.response.out.write(json.dumps({"result":"success"}))
            else:
                self.redirect("/account")
        else:
            self.checkRequest([None])
        self.response.out.write('\n\n')

    @staticmethod
    def makeCookieString(expire,obj):
        for k,v in obj.iteritems():
            key,value = k,v
            break
        s = key + '=' + value + '; expires=%s;'%expire + "; Path=/"
        return s
        
    @staticmethod
    def getCurrentUser(requestHandler):
        accessToken = requestHandler.request.get("access_token")
        if accessToken is not None and accessToken != "":
            user = GrafiteUser.getUser(accessToken=accessToken)
            if user is not None and GrafiteUser.checkAccessTokenValidity(user.key().name(),accessToken):
                return user
            else:
                return None
        accessToken = None
        for k,v in requestHandler.request.cookies.iteritems():
            if k=="access_token":
                accessToken = v
        if accessToken is None:
            return None
        user = GrafiteUser.getUser(accessToken=accessToken)
        if user is None:
            return None
        if GrafiteUser.checkAccessTokenValidity(user.key().name(),accessToken):
            return user
        return None

    @staticmethod
    def getCurrentUserOrRedirect(requestHandler):
        u = UserService.getCurrentUser(requestHandler)
        if u is None:
            requestHandler.redirect("/login"+(("?to=" + urllib.quote(requestHandler.request.url)) if requestHandler.request.url else ""))
            requestHandler.error(302)
            return None
        return u

    @staticmethod
    def getCurrentUserOrJsonError(requestHandler):
        u = UserService.getCurrentUser(requestHandler)
        if u is None:
            requestHandler.response.out.write(json.dumps({"result":"error","message":"unauthorised"}))
            return None
        return u

    def checkRequest(self,obj):
        jsonop = self.request.get("alt")=="json" if len(self.request.get("alt"))>0 else False
        for x in obj:
            if (x is None) or str(x)=='':
                self.response.out.write(json.dumps({"Result":"Error","Reason":"Bad Request!"}) if jsonop else 
                '<meta http-equiv="refresh" content="1;url=/login">Bad request!..')
                return False
        return True