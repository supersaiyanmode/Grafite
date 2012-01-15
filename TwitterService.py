from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.api.urlfetch import fetch as urlfetch, GET, POST
from google.appengine.ext import db
from wsgiref.handlers import CGIHandler
from google.appengine.ext import webapp
from google.appengine.ext.webapp.template import render
from django.utils import simplejson as json
import httplib
from random import getrandbits

import uuid
import logging
import time
import os
import urllib
import hmac
from hashlib import sha1
from UserService import UserService,GrafiteUser
import ShortLink
try:
    from urlparse import parse_qsl
except:
    from cgi import parse_qsl

class LongerTweet(db.Model):
    user = db.ReferenceProperty(GrafiteUser)
    text = db.TextProperty()



class InvalidTwitterResponseException(Exception):
    def __init__(self, msg):
        self.msg = msg

class BlankCredentialsException(Exception):
    pass

class WrongCredentialsException(Exception):
    pass
class LongStatusException(Exception):
    pass

def encode(text):
    return urllib.quote(str(text), '')

def getBaseString(method, url, obj):
    return '&'.join(map(encode, [
        method.upper(), url, '&'.join('%s=%s' % (encode(k), encode(obj[k])) for k in sorted(obj))]))

class TwitterStatusUpdater():
    def __init__(self,user):
        self.twitter_consumer_key    = 'Rrt8lb8f8lTOAHTxxkVg6Q'
        self.twitter_consumer_secret = 'sY4cnmrCOkZXP8Xlq22CUeR9Fsp3YzDy7ybOyIT3sM'
        self.redirect_uri = "http://grafiteapp.appspot.com/twitter/authenticated/"
        self.user = user
        try:
            self.config = json.loads(user.twitter)
        except Exception,e:
            pass
    
    def requestAuthenticationURL(self):
        obj =         {
                    'oauth_callback':self.redirect_uri,
                    'oauth_consumer_key':self.twitter_consumer_key,
                    'oauth_nonce': getrandbits(64),
                    'oauth_signature_method':'HMAC-SHA1',
                    'oauth_timestamp':int(time.time()),
                    'oauth_version':'1.0'
                }
        s = getBaseString("POST","https://api.twitter.com/oauth/request_token",obj)
        key = self.twitter_consumer_secret + "&"
        obj['oauth_signature'] = hmac.new(key, s, sha1).digest().encode('base64')[:-1]
        
        for x in obj:
            obj[x] = encode(obj[x])
        
        authHeader = "OAuth oauth_nonce=\"" + obj['oauth_nonce'] + "\", oauth_callback=\"" + obj['oauth_callback']
        authHeader+= "\", oauth_signature_method=\"" + obj['oauth_signature_method'] + "\", oauth_timestamp=\""
        authHeader+= obj['oauth_timestamp'] + "\", oauth_consumer_key=\"" + obj['oauth_consumer_key']
        authHeader+= "\", oauth_signature=\"" + obj['oauth_signature'] + "\", oauth_version=\""
        authHeader+= obj['oauth_version'] + "\""
        result = urlfetch(url='https://api.twitter.com/oauth/request_token',
                        method=POST,
                        headers={'Authorization': authHeader})
        if str(result.status_code) != '200':
            return None
        res = {}
        for x in result.content.split('&'):
            obj = x.split('=')
            res[obj[0]] = obj[1]
        self.user.twitter = json.dumps(res)
        self.user.put()
        return "https://api.twitter.com/oauth/authorize?oauth_token="+res['oauth_token']
        
    def setCredentials(self,verifier):
        objC = json.loads(self.user.twitter)
        objC['oauth_verifier'] = verifier
        obj =         {
                    'oauth_consumer_key':self.twitter_consumer_key,
                    'oauth_nonce': getrandbits(64),
                    'oauth_signature_method':'HMAC-SHA1',
                    'oauth_token':objC['oauth_token'],
                    'oauth_timestamp':int(time.time()),
                    'oauth_verifier':verifier,
                    'oauth_version':'1.0'
                }
        s = getBaseString("POST","https://api.twitter.com/oauth/access_token",obj)
        key = self.twitter_consumer_secret + "&" + objC['oauth_token_secret']
        obj['oauth_signature'] = hmac.new(key, s, sha1).digest().encode('base64')[:-1]
        
        for x in obj:
            obj[x] = encode(obj[x])
        
        authHeader = "OAuth oauth_consumer_key=\"" + obj['oauth_consumer_key'] + "\", oauth_nonce=\"" + obj['oauth_nonce']
        authHeader+= "\", oauth_signature_method=\"" + obj['oauth_signature_method'] + "\", oauth_token=\""
        authHeader+= obj['oauth_token'] + "\", oauth_timestamp=\"" + obj['oauth_timestamp']
        authHeader+= "\", oauth_verifier=\"" + obj['oauth_verifier'] + "\", oauth_version=\""
        #authHeader+= obj['oauth_version'] + "\""
        authHeader+= obj['oauth_version'] + "\", oauth_signature=\""+obj['oauth_signature']+"\""
        result = urlfetch(url='https://api.twitter.com/oauth/access_token',
                        method=POST,
                        headers={'Authorization': authHeader})
        if str(result.status_code) == '200':
            res = {}
            for x in result.content.split('&'):
                obj = x.split('=')
                res[obj[0]] = obj[1]
            objC.update(res)
            self.user.twitter = json.dumps(objC)
            self.user.put()
            return result.content
        return False
        
    def updateStatus(self,statusObj):
        #self.login()
        statusText = unicode(statusObj['status']).encode('utf-8')
        
        objC = json.loads(self.user.twitter)
        obj =         {
                    'status':statusText,
                    'oauth_consumer_key':self.twitter_consumer_key,
                    'oauth_nonce': getrandbits(64),
                    'oauth_signature_method':'HMAC-SHA1',
                    'oauth_token':objC['oauth_token'],
                    'oauth_timestamp':int(time.time()),
                    'oauth_version':'1.0'
                }
        s = getBaseString("POST","http://api.twitter.com/1/statuses/update.json",obj)
        #return {"result":s}
        key = self.twitter_consumer_secret + "&" + objC['oauth_token_secret']
        obj['oauth_signature'] = hmac.new(key, s, sha1).digest().encode('base64')[:-1]
        
        for x in obj:
            obj[x] = encode(obj[x])
        
        authHeader = "OAuth oauth_consumer_key=\"" + obj['oauth_consumer_key'] + "\", oauth_nonce=\"" + obj['oauth_nonce']
        authHeader+= "\", oauth_signature_method=\"" + obj['oauth_signature_method'] + "\", oauth_token=\""
        authHeader+= obj['oauth_token'] + "\", oauth_timestamp=\"" + obj['oauth_timestamp']
        authHeader+= "\", oauth_version=\"" + obj['oauth_version'] + "\", oauth_signature=\""+obj['oauth_signature']+"\""

        
        res = urlfetch(url='http://api.twitter.com/1/statuses/update.json',
                        payload="status="+encode(statusText),
                        method=POST,
                        headers={'Authorization': authHeader})
        if str(res.status_code)=='200':
            obj = json.loads(res.content)
            objC['total_statuses'] = objC['total_statuses']+1 if 'total_statuses' in objC else 1
            objC['latest_status_id'] = obj['id_str']
            self.user.twitter= json.dumps(objC)
            self.user.put()
            obj['result'] = "success"
            return obj
        else:
            return  {'result':"error",'status':res.status_code, 'message':res.content,"status":statusText}

    def verifyCredentials(self):
        if self.getFeed() is None:
            raise WrongCredentialsException()
        return True

    def getDPSrc(self):
        if self.checkUserCredentials():
            return self.getFeed()['profile_image_url']
        return ""
    def checkUserCredentials(self):
        if not hasattr(self, 'config'):
            return False
        return self.config['oauth_token'] != "" and self.config['oauth_token_secret']!= ""

    def login(self):
        if not self.checkUserCredentials():
            raise BlankCredentialsException()
        self.verifyCredentials()

    def getProfileDetails(self):
        return self.getFeed()['data'][0]['user'] # #######VERIFYY###

    def getFeed(self,feedName='user_timeline'):
        objC = json.loads(self.user.twitter)
        obj = {
                    'include_entities':'true',
                    'oauth_consumer_key':self.twitter_consumer_key,
                    'oauth_nonce': getrandbits(64),
                    'oauth_signature_method':'HMAC-SHA1',
                    'oauth_token':objC['oauth_token'],
                    'oauth_timestamp':int(time.time()),
                    'oauth_version':'1.0'
                }
        url = "http://api.twitter.com/1/statuses/%s.json"%feedName
        s = getBaseString("GET",url,obj)
        key = self.twitter_consumer_secret + "&" + objC['oauth_token_secret']
        obj['oauth_signature'] = hmac.new(key, s, sha1).digest().encode('base64')[:-1]
        
        for x in obj:
            obj[x] = encode(obj[x])
        
        authHeader = "OAuth oauth_consumer_key=\"" + obj['oauth_consumer_key'] + "\", oauth_nonce=\"" + obj['oauth_nonce']
        authHeader+= "\", oauth_signature_method=\"" + obj['oauth_signature_method'] + "\", oauth_token=\""
        authHeader+= obj['oauth_token'] + "\", oauth_timestamp=\"" + obj['oauth_timestamp']
        authHeader+= "\", oauth_version=\"" + obj['oauth_version'] + "\", oauth_signature=\""+obj['oauth_signature']+"\""

        result = urlfetch(url=url+"?include_entities=true",
                        method=GET,
                        headers={'Authorization': authHeader})
        if str(result.status_code) == '200':
            return {"result":"success","data":json.loads(result.content)}
        return {"result":"error","message":json.loads(result.content)}

    @staticmethod
    def getAuthenticationStatus(user):
        tt = TwitterStatusUpdater(user)
        try:
            tt.login()
            return "",tt
        except BlankCredentialsException, e:
            return "blank credentials",None
        except WrongCredentialsException, e:
            return "wrong credentials",None
        except Exception, e:
            return "Unknown Error",None
    
    def followUser(self,tUser2):
        url = 'http://api.twitter.com/1/friendships/create.json'
        user2Id = tUser2.getProfileDetails()['id']
        objC = json.loads(self.user.twitter)
        obj =         {
                    'user_id': user2Id,
                    'oauth_consumer_key':self.twitter_consumer_key,
                    'oauth_nonce': getrandbits(64),
                    'oauth_signature_method':'HMAC-SHA1',
                    'oauth_token':objC['oauth_token'],
                    'oauth_timestamp':int(time.time()),
                    'oauth_version':'1.0'
                }
        s = getBaseString("POST",url,obj)
        key = self.twitter_consumer_secret + "&" + objC['oauth_token_secret']
        obj['oauth_signature'] = hmac.new(key, s, sha1).digest().encode('base64')[:-1]
        
        for x in obj:
            obj[x] = encode(obj[x])
        
        authHeader = "OAuth oauth_consumer_key=\"" + obj['oauth_consumer_key'] + "\", oauth_nonce=\"" + obj['oauth_nonce']
        authHeader+= "\", oauth_signature_method=\"" + obj['oauth_signature_method'] + "\", oauth_token=\""
        authHeader+= obj['oauth_token'] + "\", oauth_timestamp=\"" + obj['oauth_timestamp']
        authHeader+= "\", oauth_version=\"" + obj['oauth_version'] + "\", oauth_signature=\""+obj['oauth_signature']+"\""

        result = urlfetch(url=url,
                        payload="user_id="+encode(str(user2Id)),
                        method=POST,
                        headers={'Authorization': authHeader})
        if str(result.status_code) == '200':
            return {"result":"success","data":json.loads(result.content)}
        return {"result":"error","error_code":result.status_code, "content":result.content}

    def unfollowUser(self,tUser2):
        url = 'http://api.twitter.com/1/friendships/destroy.json'
        user2Id = tUser2.getProfileDetails()['id']
        objC = json.loads(self.user.twitter)
        obj =         {
                    'user_id':user2Id,
                    'oauth_consumer_key':self.twitter_consumer_key,
                    'oauth_nonce': getrandbits(64),
                    'oauth_signature_method':'HMAC-SHA1',
                    'oauth_token':objC['oauth_token'],
                    'oauth_timestamp':int(time.time()),
                    'oauth_version':'1.0'
                }
        s = getBaseString("POST",url,obj)
        key = self.twitter_consumer_secret + "&" + objC['oauth_token_secret']
        obj['oauth_signature'] = hmac.new(key, s, sha1).digest().encode('base64')[:-1]
        
        for x in obj:
            obj[x] = encode(obj[x])
        
        authHeader = "OAuth oauth_consumer_key=\"" + obj['oauth_consumer_key'] + "\", oauth_nonce=\"" + obj['oauth_nonce']
        authHeader+= "\", oauth_signature_method=\"" + obj['oauth_signature_method'] + "\", oauth_token=\""
        authHeader+= obj['oauth_token'] + "\", oauth_timestamp=\"" + obj['oauth_timestamp']
        authHeader+= "\", oauth_version=\"" + obj['oauth_version'] + "\", oauth_signature=\""+obj['oauth_signature']+"\""

        result = urlfetch(url=url,
                        method=POST,
                        payload="user_id=" + encode(str(user2Id)),
                        headers={'Authorization': authHeader})
        if str(result.status_code) == '200':
            return {"result":"success","data":json.loads(result.content)}
        return {"result":"error","error_code":result.status_code, "content":result.content}

    def getRelationship(self,tUser2):
        url = 'http://api.twitter.com/1/friendships/show.json?source_id=%s&target_id=%s'%(self.getProfileDetails()['id_str'], tUser2.getProfileDetails()['id_str'])

        objC = json.loads(self.user.twitter)
        obj =         {
                    'oauth_consumer_key':self.twitter_consumer_key,
                    'oauth_nonce': getrandbits(64),
                    'oauth_signature_method':'HMAC-SHA1',
                    'oauth_token':objC['oauth_token'],
                    'oauth_timestamp':int(time.time()),
                    'oauth_version':'1.0'
                }
        s = getBaseString("GET",url,obj)
        key = self.twitter_consumer_secret + "&" + objC['oauth_token_secret']
        obj['oauth_signature'] = hmac.new(key, s, sha1).digest().encode('base64')[:-1]
        
        for x in obj:
            obj[x] = encode(obj[x])
        
        authHeader = "OAuth oauth_consumer_key=\"" + obj['oauth_consumer_key'] + "\", oauth_nonce=\"" + obj['oauth_nonce']
        authHeader+= "\", oauth_signature_method=\"" + obj['oauth_signature_method'] + "\", oauth_token=\""
        authHeader+= obj['oauth_token'] + "\", oauth_timestamp=\"" + obj['oauth_timestamp']
        authHeader+= "\", oauth_version=\"" + obj['oauth_version'] + "\", oauth_signature=\""+obj['oauth_signature']+"\""

        result = urlfetch(url=url,
                        method=GET,
                        headers={'Authorization': authHeader})
        if str(result.status_code) == '200':
            return json.loads(result.content)
        return None

class TwitterService(webapp.RequestHandler):
    def get(self,job):
        if job not in ['authenticate','authenticated','follow','unfollow','longtweet','feed']:
            self.error(404)
            return
            
        user = UserService.getCurrentUser(self)
        if not user:
            if job in ('follow','unfollow'):
                self.response.headers.add_header("Content-Type","application/json")
                self.response.out.write(json.dumps({"result":"error","message":"Unauthenticated User"}))
                return
            UserService.getCurrentUserOrRedirect(self)
            return

        getattr(self,job)(user)
        
    def post(self,job):
        user = UserService.getCurrentUserOrRedirect(self)
        if not user:
            return
        if job not in ['update','status']:
            self.error(404)
            return
        getattr(self,job)(user)

    def longtweet(self,user):
        #res = PermanentAccessCodes.all().filter("user = ",DATA.user).filter("app =",app)
        class temp:
            pass
        DATA = temp()
        if self.request.get("tid") in (None,""):
            self.redirect("/")
            self.error(302)
            return
        tid = self.request.get("tid")
        try:
            DATA.longTweet = LongerTweet.get(db.Key(encoded=tid))
            status,tUser = TwitterStatusUpdater.getAuthenticationStatus(DATA.longTweet.user)
            if status != "":
                raise Exception("Using not authorised Twitter!")
            DATA.userProfile = tUser.getProfileDetails()
        except Exception, e:
            #self.response.out.write(e)
            self.error(404)
            return
        
        path = os.path.join(os.path.dirname(__file__), 'html/longtweet.html')
        self.response.out.write(render(path, {'DATA':DATA}))

    def feed(self,user):
        self.response.headers["Content-Type"] = "application/json"
        t = self.request.get("type") or "user_timeline"
        if t not in 'user_timeline home_timeline mentions public_timeline retweeted_by_me retweets_of_me retweeted_to_user retweeted_by_user'.split():
            self.response.out.write(json.dumps({"result":"error","message":"Invalid Parameter!"}))

        self.response.out.write(json.dumps(TwitterService.getFeed(user,t)))

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
        
        res1, tUser1 = TwitterStatusUpdater.getAuthenticationStatus(user)
        res2, tUser2 = TwitterStatusUpdater.getAuthenticationStatus(user2)
        if res1 != "" or res2 != "":
            self.response.out.write(json.dumps({"result":"error","message":"User hasn't authorised"}))
            return

        res = tUser1.followUser(tUser2)
        res['newState'] = TwitterService.getRelationship(user, user2)
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
        
        res1, tUser1 = TwitterStatusUpdater.getAuthenticationStatus(user)
        res2, tUser2 = TwitterStatusUpdater.getAuthenticationStatus(user2)
        if res1 != "" or res2 != "":
            self.response.out.write(json.dumps({"result":"error","message":"User hasn't authorised"}))
            return

        res = tUser1.unfollowUser(tUser2)
        res['newState'] = TwitterService.getRelationship(user, user2)
        self.response.out.write(json.dumps(res))
        
    def authenticate(self,user):
        if TwitterStatusUpdater.getAuthenticationStatus(user)[0] != "":
            b = TwitterStatusUpdater(user)
            self.redirect(b.requestAuthenticationURL())
            self.error(302)
        else:
            self.redirect('/userHome')
            self.error(302)
            return
    
    def authenticated(self,user):
        if self.request.get("oauth_verifier") not in (None,""):
            b = TwitterStatusUpdater(user)
            b.setCredentials(self.request.get("oauth_verifier"))

        self.redirect('/userHome')
        self.error(302)
    
    def status(self,user):
        self.response.out.write(json.dumps(TwitterService.getStatus(user)))

    @staticmethod
    def getFeed(user,t):
        status,usr = TwitterStatusUpdater.getAuthenticationStatus(user)
        if status!= "":
            return {"result":"error","message":"unauthorised",
            "link":ShortLink.getShortUrl("http://grafiteapp.appspot.com/userHome?access_token=%s&redirect=%s"%
                (user.accessToken,"/twitter/authenticate/"))}
        return usr.getFeed(t)        

    @staticmethod
    def getStatus(user):
        status,usr = TwitterStatusUpdater.getAuthenticationStatus(user)
        if status!= "":
            return {"result":"error","message":"unauthorised",
            "link":ShortLink.getShortUrl("http://grafiteapp.appspot.com/userHome?access_token=%s&redirect=%s"%
                (user.accessToken,"/twitter/authenticate/"))}
        obj = usr.getFeed()
        if not obj:
            return {"result":"error","message":"Unable to retrieve details"}
        retweets = 0
        try:
            retweets = obj['retweet_count']
        except Exception, e:
            pass
        
        try:
            return {"result":"success","status":obj[0]['text'],
                "retweets": retweets,
                "DPSrc":obj[0]['user']['profile_image_url_https'],
                "user":obj[0]['user'],
                "link":"http://www.twitter.com",
                "all":obj
                }
        except Exception, e:
            return {"result":"error","obj":obj}

    @staticmethod
    def getUser(user):
        return TwitterStatusUpdater.getAuthenticationStatus(user)[1]

    @staticmethod
    def updateStatus(user,statusObj):
        status,usr = TwitterStatusUpdater.getAuthenticationStatus(user)
        if status!= "":
            return None
        
        #long tweets
        statusText = statusObj['status']
        if len(str(statusText))>140:
            longTweet = statusText
            lt = LongerTweet()
            lt.text = longTweet
            lt.user = user
            tid = str(lt.put())
            statusText = str(statusText)[:115] + ".. "
            statusText = statusText + ShortLink.getShortUrl("https://grafiteapp.appspot.com/twitter/longtweet/?tid=%s"%tid)
            statusText = unicode(statusText)
            logging.debug("Long Tweet! Shortened URL: %s\nStatus: %s"%("link",statusText))
            statusObj['status'] = statusText
        return usr.updateStatus(statusObj)

    @staticmethod
    def getRelationship(user1, user2):
        status, twitterUser = TwitterStatusUpdater.getAuthenticationStatus(user1)
        if status != "":
            return {"result":"error1","message":"You aren't using Twitter" + status, "value":False}
        
        status, twitterUser2 = TwitterStatusUpdater.getAuthenticationStatus(user2)
        if status != "":
            return {"result":"error2","message":user2.Nickname + " isn't using Twitter", "value":False}
        
        obj = twitterUser.getRelationship(twitterUser2)
        #print ""
        #print repr(obj)
        try:
            return {"result":"success","following":obj['relationship']['source']['following'], "followed":obj['relationship']['source']['followed_by'], "connect":"/twitter/follow/?tUser="+str(user2.key()),
            "disconnect":"/twitter/unfollow/?tUser="+str(user2.key())
            }
        except Exception,e:
            print ""
            print repr(obj)
            

