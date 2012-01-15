from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.api.urlfetch import fetch as urlfetch, GET, POST,PUT,DELETE
from wsgiref.handlers import CGIHandler
from google.appengine.ext import webapp
from django.utils import simplejson as json
import httplib
from google.appengine.ext import db
import logging
import re

from UserService import UserService,GrafiteUser
import ShortLink
import time

CLIENT_ID = '1022723150403-06k1vhvgu3d4d40blmg0mkl08qakn6j3.apps.googleusercontent.com'
CLIENT_SECRET = 'G4t1tF7kJncDdjNmdAXQPYU4'
API_KEY = 'AIzaSyA8rEK_zgeRPz-yDkQkcDBcaziMkhdMHQY'

class BlankCredentialsException(Exception):
    pass
class WrongCredentialsException(Exception):
    pass

class BuzzStatusUpdater:
    def __init__(self, user):
        try:
            self.config = json.loads(user.google)
            self.user = user
        except Exception, err:
            pass

    def checkUserCredentials(self):
        if not hasattr(self, 'config'):
            return False
        return self.config['access_token'] != "" and self.config['refresh_token']!=""

    def _requestNewAccessToken(self):
        reqStr = ['client_id='+CLIENT_ID, 'client_secret='+CLIENT_SECRET, 
                'refresh_token='+self.config['refresh_token'], 'grant_type=refresh_token']

        res = urlfetch('https://accounts.google.com/o/oauth2/token',payload='&'.join(reqStr), method=POST,
            headers={'Content-Type':'application/x-www-form-urlencoded'})

        if str(res.status_code) == '200':
            obj = json.loads(res.content)
            self.config['access_token'] = obj['access_token']
            self.user.google = json.dumps(self.config)
            self.user.put()
            return True
        else:
            return False

    def login(self):
        if not self.checkUserCredentials():
            raise BlankCredentialsException()
        return self.verifyCredentials()

    @staticmethod
    def requestAuthenticationURL():
        params = ['client_id='+CLIENT_ID,
                'redirect_uri=http://grafiteapp.appspot.com/buzz/authenticated/',
                'scope=https://www.googleapis.com/auth/buzz,https://www.googleapis.com/auth/emeraldsea.stream.read',
                'response_type=code']
        return 'https://accounts.google.com/o/oauth2/auth?' + '&'.join(params)

    def verifyCredentials(self):
        at = "OAuth " + self.config['access_token']
        res = urlfetch('https://www.googleapis.com/buzz/v1/activities/@me/@self',payload="", method=GET,
            headers={'Content-Type':'application/x-www-form-urlencoded','Authorization':at})
        if str(res.status_code) != '200':
            if not self._requestNewAccessToken():
                raise WrongCredentialsException()
        return True

    def updateStatus(self,statusObj):
        req = {}
        req['data'] = {}
        req['data']['object'] = {}
        req['data']['object']['type'] = "note"
        req['data']['object']['content'] = statusObj['status']
        
        if 'link' in statusObj:
            curUrl = statusObj['link']['url']
            req['data']['object']["attachments"] = [{
                "content":statusObj['link']['description'],
                "type": "article",
                "title": statusObj['link']['title'],
                "links": {
                    "alternate": [{
                        "href": statusObj['link']['url'],
                        "type":"text/html"
                    }],
                }
            }]
        
        reqStr = json.dumps(req)
        
        at = "OAuth " + self.config['access_token']
        res = urlfetch('https://www.googleapis.com/buzz/v1/activities/@me/@self?alt=json&key='+API_KEY,
            payload=reqStr, method=POST,
            headers={'Authorization':at,'Content-Type':'application/json'})
        if str(res.status_code) == '200':
            res = json.loads(res.content)
            res['result'] = 'success'
            gg = json.loads(self.user.google)
            gg['total_statuses'] = gg['total_statuses'] + 1 if 'total_statuses' in gg else 1
            gg['latest_status_id'] = res['data']['id']
            self.user.google = json.dumps(gg)
            res['extra'] = req
            return res
        return {'result':"error",'status':res.status_code, 'message':json.loads(res.content)}
        
    def getDPSrc(self):
        res = self.getProfileDetails()
        if res:
            return res['data']['thumbnailUrl']

    def getProfileDetails(self):
        at = "OAuth " + self.config['access_token']
        res = urlfetch('https://www.googleapis.com/buzz/v1/people/@me/@self?alt=json&key='+API_KEY,
            method=GET,
            headers={'Authorization':at})
        if str(res.status_code) == '200':
            res = json.loads(res.content)
            return res
        return json.loads(res.content)

    def getFollowers(self,page=0):
        at = "OAuth " + self.config['access_token']
        res = urlfetch('https://www.googleapis.com/buzz/v1/people/@me/@groups/@followers?max-results=100&c=%d&alt=json&key='%(page*100) +API_KEY,
            method=GET,
            headers={'Authorization':at})
        if str(res.status_code) == '200':
            res = json.loads(res.content)['data']
            try:
                obj = res['entry']
            except Exception,e:
                res['entry'] = []
            return res['entry']
        return None

    def getFollowing(self, page=0):
        at = "OAuth " + self.config['access_token']
        url = 'https://www.googleapis.com/buzz/v1/people/@me/@groups/@following?max-results=100&c=%d&alt=json&key='%(page*100) + API_KEY
        res = urlfetch(url,
            method=GET,
            headers={'Authorization':at})
        if str(res.status_code) == '200':
            res = json.loads(res.content)['data']
            try:
                obj = res['entry']
            except Exception,e:
                res['entry'] = []
            return res['entry']
        return None

    def followUser(self,bUser2):
        bUserId = None
        try:
            bUserId = bUser2.getProfileDetails()['data']['id']
        except Exception,e:
            return None
        bUserId = str(bUserId)
        at = "OAuth " + self.config['access_token']
        url = 'https://www.googleapis.com/buzz/v1/people/@me/@groups/@following/%s?alt=json&key=%s'%(bUserId,API_KEY)
        res = urlfetch(url,
            method=PUT,
            headers={'Authorization':at})
        if str(res.status_code)[0] == '2':
            res = json.loads(res.content)['data']
            res['result']='success'
            return res
        return {'result':'error','message':res.content}

    def unfollowUser(self,bUser2):
        bUserId = None
        try:
            bUserId = bUser2.getProfileDetails()['data']['id']
        except Exception,e:
            return None
        bUserId = str(bUserId)
        at = "OAuth " + self.config['access_token']
        url = 'https://www.googleapis.com/buzz/v1/people/@me/@groups/@following/%s?alt=json&key=%s'%(bUserId,API_KEY)
        res = urlfetch(url,
            method=DELETE,
            headers={'Authorization':at})
        if str(res.status_code)[0] == '2':
            return {'result':'success'}
        return {'result':'error','message':res.content}

    def getLastStatusDetails(self):
        #GET /buzz/v1/activities/@me/@self?alt=json&key= 
        self.login()
        at = "OAuth " + self.config['access_token']
        res = urlfetch('https://www.googleapis.com/buzz/v1/activities/@me/@self?alt=json&key='+API_KEY,
            method=GET,
            headers={'Authorization':at})
        if str(res.status_code) == '200':
            return json.loads(res.content)
        return None
    
    def getUserFeed(self,paging):
        self.login()
        at = "OAuth " + self.config['access_token']
        url = paging if paging else 'https://www.googleapis.com/buzz/v1/activities/@me/@consumption?alt=json&key='+API_KEY
        res = urlfetch(url,
            method=GET,
            headers={'Authorization':at})
        if str(res.status_code) == '200':
            obj = json.loads(res.content)
            obj['requestUrl'] = url
            return obj
        return {"result":"error","content":res.content}

    @staticmethod
    def getAuthenticationStatus(user):
        gb = BuzzStatusUpdater(user)
        try:
            gb.login()
            return "",gb
        except BlankCredentialsException, e:
            return "blank credentials",None
        except WrongCredentialsException, e:
            return "wrong credentials",None
        except Exception, e:
            return "Unknown Error",None

class BuzzService(webapp.RequestHandler):
    def get(self,job):
        user = UserService.getCurrentUserOrRedirect(self)
        if not user:
            return
        
        if job not in ['authenticate','authenticated','follow','unfollow','feed']:
            self.error(404)
            return
        getattr(self,job)(user)

    def post(self,job):
        user = UserService.getCurrentUserOrRedirect(self)
        if not user:
            return
        if job not in ['status','update']:
            self.error(404)
            return
        getattr(self,job)(user)

    def authenticate(self,user):
        if BuzzStatusUpdater.getAuthenticationStatus(user)[0] != "":
            self.redirect(BuzzStatusUpdater.requestAuthenticationURL())
            self.error(302)
        else:
            self.redirect("/userHome")
            self.error(302)
    
    def authenticated(self,user):
        if self.request.get("code") not in (None,""):
            code = self.request.get("code")
            reqStr = ['code='+code,
                'client_id='+CLIENT_ID,
                'client_secret='+ CLIENT_SECRET,
                'grant_type=authorization_code',
                'redirect_uri=http://grafiteapp.appspot.com/buzz/authenticated/'
                ]
            #httpscon.request("POST","/o/oauth2/token",reqStr)
            res = urlfetch('https://accounts.google.com/o/oauth2/token',payload='&'.join(reqStr),method=POST)
            if str(res.status_code) == '200':
                obj = json.loads(res.content)
                obj['expires'] = time.time()+int(obj['expires_in'])
                user.google = json.dumps(obj)
                user.put()
        self.redirect('/userHome')
        self.error(302)

    def follow(self,user):
        self.response.headers.add_header("Content-Type","application/json")

        userId = self.request.get("gUser")
        if userId in (None,""):
            self.response.out.write(json.dumps({"result":"error","message":"Invalid Parameter!"}))
            return

        user2 = None
        try:
            user2 = GrafiteUser.get(db.Key(encoded=userId))
        except Exception, e:
            self.response.out.write(json.dumps({"result":"error","message":"Invalid User ID","e":str(e)}))
            return
        
        res1, bUser1 = BuzzStatusUpdater.getAuthenticationStatus(user)
        res2, bUser2 = BuzzStatusUpdater.getAuthenticationStatus(user2)
        if res1 != "" or res2 != "":
            self.response.out.write(json.dumps({"result":"error","message":"User hasn't authorised"}))
            return

        res = bUser1.followUser(bUser2)
        logging.debug(res)
        res['newState'] = BuzzService.isFollowing(user, user2)
        self.response.out.write(json.dumps(res))

    def unfollow(self,user):
        self.response.headers.add_header("Content-Type","application/json")
        
        userId = self.request.get("gUser")
        if userId in (None,""):
            self.response.out.write(json.dumps({"result":"error","message":"Invalid Parameter!"}))
            return

        user2 = None
        try:
            user2 = GrafiteUser.get(db.Key(encoded=userId))
        except Exception, e:
            self.response.out.write(json.dumps({"result":"error","message":"Invalid User ID","e":str(e)}))
            return

        res1, bUser1 = BuzzStatusUpdater.getAuthenticationStatus(user)
        res2, bUser2 = BuzzStatusUpdater.getAuthenticationStatus(user2)
        if res1 != "" or res2 != "":
            self.response.out.write(json.dumps({"result":"error","message":"User hasn't authorised"}))
            return
        res = bUser1.unfollowUser(bUser2)
        res['newState'] = BuzzService.isFollowing(user, user2)
        self.response.out.write(json.dumps(res))

    def feed(self,user):
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(json.dumps(BuzzService.getUserFeed(user,self.request.get("paging"))))
        #self.response.out.write(open('feed').read())

    def status(self,user):
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(json.dumps(BuzzService.getStatus(user)))

    def update(self,user):
        if self.request.get("status") in (None,""):
            self.response.out.write(json.dumps({"result":"error","message":"status field missing."}))
            return
        
        self.response.out.write(json.dumps(BuzzService.updateStatus(user,self.request.get("status"))))

    @staticmethod
    def getStatus(user):
        status,usr = BuzzStatusUpdater.getAuthenticationStatus(user)
        if status!= "":
            return {"result":"error","message":"unauthorised",
            "link":ShortLink.getShortUrl("http://grafiteapp.appspot.com/userHome?access_token=%s&redirect=%s"%
            (user.accessToken,"/buzz/authenticate/"))}
        obj = usr.getLastStatusDetails()
        if not obj:
            return {"result":"error","message":"Unable to retrieve details"}
            
        comments = 0
        try:
            comments=obj['data']['items'][0]['links']['replies'][0]['count']
        except Exception,e:
            pass
        likes = 0
        try:
            likes=obj['data']['items'][0]['links']['liked'][0]['count']
        except Exception,e:
            pass
        status = "You haven't posted anything in your Buzz"
        try:
            status = obj['data']['items'][0]['title']
        except Exception,e:
            pass
        DPSrc = "#"
        try:
            DPSrc = obj['data']['items'][0]['actor']['thumbnailUrl']
        except Exception,e:
            pass
        return {"result":"success","status":status,
            "comments":comments,
            "likes":likes,
            "DPSrc":DPSrc,
            "link":"#",
            "MainData":obj
            }
    
    @staticmethod
    def isFollowed(user1,user2):	#is user1 followed by user2
        status, buzzUser = BuzzStatusUpdater.getAuthenticationStatus(user1)
        if status != "":
            return {"result":"error","message":"You aren't using Buzz"}
        
        
        status, buzzUser2 = BuzzStatusUpdater.getAuthenticationStatus(user2)
        if status != "":
            return {"result":"error","message":user2.Nickname + " isn't using Buzz"}
        
        
        profileUserId = None
        try:
            profileUserId = buzzUser2.getProfileDetails()['data']['id']
        except Exception,e:
            return {"result":"error","value":False,"message":"This user isn't using Buzz"}
        
        page = 0
        followers = buzzUser.getFollowers()
        
        
        while followers:
            followers = map(lambda x: x['id'], followers)
            if profileUserId in followers:
                return {"result":"success","value":True}
            page = page + 1
            followers = buzzUser.getFollowers(page)

        return {"result":"success","value":False}
	
    @staticmethod
    def isFollowing(user1,user2):	#is user2 followed by user1
        status, buzzUser = BuzzStatusUpdater.getAuthenticationStatus(user1)
        if status != "":
            return {"result":"error","message":"You aren't using Buzz", "value":False}
        
        
        status, buzzUser2 = BuzzStatusUpdater.getAuthenticationStatus(user2)
        if status != "":
            return {"result":"error","message":user2.Nickname + " isn't using Buzz", "value":False}
        profileUserId = None
        try:
            profileUserId = buzzUser2.getProfileDetails()['data']['id']
        except Exception,e:
            return {"result":"error","value":False,"message":"This user isn't using Buzz"}
        
        page = 0
        following = buzzUser.getFollowing()
        
        while following:	
            following = map(lambda x: x['id'], following)
            if profileUserId in following:
                return {"result":"success","value":True}
            page = page + 1
            following = buzzUser.getFollowing(page)

        return {"result":"success","value":False}

    @staticmethod
    def getUser(user):
        return BuzzStatusUpdater.getAuthenticationStatus(user)[1]

    @staticmethod
    def getUserFeed(user,paging):
        status,usr = BuzzStatusUpdater.getAuthenticationStatus(user)
        if status!= "":
            return None
        return usr.getUserFeed(paging)

    @staticmethod
    def updateStatus(user,statusObj):
        status,usr = BuzzStatusUpdater.getAuthenticationStatus(user)
        if status!= "":
            return None
        return usr.updateStatus(statusObj)
