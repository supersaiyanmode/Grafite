from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.api.urlfetch import fetch as urlfetch, GET, POST
from wsgiref.handlers import CGIHandler
from google.appengine.ext import webapp
from django.utils import simplejson as json
import httplib
from random import getrandbits

import uuid
import time
import os
import pickle
import urllib
import hmac
from hashlib import sha1
from UserService import UserService
try:
    from urlparse import parse_qsl
except:
    from cgi import parse_qsl


class InvalidLinkedInResponseException(Exception):
    def __init__(self, msg):
        self.msg = msg

class BlankCredentialsException(Exception):
    pass

class WrongCredentialsException(Exception):
    pass

def encode(text):
    return urllib.quote(str(text), '')

def getBaseString(method, url, obj):
    return '&'.join(map(encode, [
	method.upper(), url, '&'.join('%s=%s' % (encode(k), encode(obj[k])) for k in sorted(obj))]))

class LinkedInStatusUpdater():
    def __init__(self,user):
	self.API_key			= 'dcSueHbGJ-r_tUU2pDe-pDbUzEDRQPzvx0oz6Rgw7kCzpl9e3yjBvSaPtA0kysyr'
	self.secret_key			= 'kNE7IaPH6ZD5zwLQ40ZCCy5oBzS9FFtPOvuRWz1i_CaS22Jdvabrc0lfuRpyO_Le'
	self.redirect_uri 		= "http://grafiteapp.appspot.com/authLinkedIn"
	self.user = user
	try:
	    self.config = json.loads(user.linkedIn)
	except Exception,e:
	    pass
    
    def requestAuthenticationURL(self):
	obj = 	{
		    'oauth_callback':self.redirect_uri,
		    'oauth_consumer_key':self.API_key,
		    'oauth_nonce': getrandbits(64),
		    'oauth_signature_method':'HMAC-SHA1',
		    'oauth_timestamp':int(time.time()),
		    'oauth_version':'1.0'
		}
	s = getBaseString("POST","https://api.linkedin.com/uas/oauth/requestToken",obj)
	key = self.API_key + "&"
	obj['oauth_signature'] = hmac.new(key, s, sha1).digest().encode('base64')[:-1]
	
	for x in obj:
	    obj[x] = encode(obj[x])
	
	authHeader = "OAuth oauth_nonce=\"" + obj['oauth_nonce'] + "\", oauth_callback=\"" + obj['oauth_callback']
	authHeader+= "\", oauth_signature_method=\"" + obj['oauth_signature_method'] + "\", oauth_timestamp=\""
	authHeader+= obj['oauth_timestamp'] + "\", oauth_consumer_key=\"" + obj['oauth_consumer_key']
	authHeader+= "\", oauth_signature=\"" + obj['oauth_signature'] + "\", oauth_version=\""
	authHeader+= obj['oauth_version'] + "\""
	result = urlfetch(url='https://api.linkedin.com/uas/oauth/requestToken',
                        method=POST,
                        headers={'Authorization': authHeader})
	if str(result.status_code) != '200':
	    return result.content
	res = {}
	for x in result.content.split('&'):
	    obj = x.split('=')
	    res[obj[0]] = obj[1]
	self.user.linkedIn = json.dumps(res)
	self.user.put()
	return "https://api.twitter.com/oauth/authorize?oauth_token="+res['oauth_token']
	
    def setCredentials(self,verifier):
	objC = json.loads(self.user.twitter)
	objC['oauth_verifier'] = verifier
	obj = 	{
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
	
    def updateStatus(self,text):
	self.login()
	text = unicode(text).encode('utf-8')
	objC = json.loads(self.user.twitter)
	obj = 	{
		    'status':text,
		    'oauth_consumer_key':self.API_key,
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
			payload="status="+encode(text),
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
	    return  {'result':"error",'status':res.status_code, 'message':res.content}

    def verifyCredentials(self):
	if self.getLastStatusDetails() is None:
	    raise WrongCredentialsException()
	return True

    def checkUserCredentials(self):
	if not hasattr(self, 'config'):
	    return False
	return self.config['oauth_token'] != "" and self.config['oauth_token_secret']!= ""

    def login(self):
	if not self.checkUserCredentials():
	    raise BlankCredentialsException()
	self.verifyCredentials()
	
    def getLastStatusDetails(self):
	objC = json.loads(self.user.twitter)
	obj = 	{
		    'oauth_consumer_key':self.twitter_consumer_key,
		    'oauth_nonce': getrandbits(64),
		    'oauth_signature_method':'HMAC-SHA1',
		    'oauth_token':objC['oauth_token'],
		    'oauth_timestamp':int(time.time()),
		    'oauth_version':'1.0'
		}
	s = getBaseString("GET","http://api.twitter.com/1/account/verify_credentials.json",obj)
	key = self.twitter_consumer_secret + "&" + objC['oauth_token_secret']
	obj['oauth_signature'] = hmac.new(key, s, sha1).digest().encode('base64')[:-1]
	
	for x in obj:
	    obj[x] = encode(obj[x])
	
	authHeader = "OAuth oauth_consumer_key=\"" + obj['oauth_consumer_key'] + "\", oauth_nonce=\"" + obj['oauth_nonce']
	authHeader+= "\", oauth_signature_method=\"" + obj['oauth_signature_method'] + "\", oauth_token=\""
	authHeader+= obj['oauth_token'] + "\", oauth_timestamp=\"" + obj['oauth_timestamp']
	authHeader+= "\", oauth_version=\"" + obj['oauth_version'] + "\", oauth_signature=\""+obj['oauth_signature']+"\""

	result = urlfetch(url='http://api.twitter.com/1/account/verify_credentials.json',
                        method=GET,
                        headers={'Authorization': authHeader})
	if str(result.status_code) == '200':
	    return json.loads(result.content)
	return None

	
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

class AuthenticateLinkedIn(webapp.RequestHandler):
    def get(self):
	print ""
	user = UserService.getCurrentUserOrRedirect(self)
	#print str(user)
	if not user:
	    return

	if self.request.get("oauth_verifier") not in (None,""):
	    b = LinkedInStatusUpdater(user)
	    b.setCredentials(self.request.get("oauth_verifier"))
	    self.redirect('/userHome')
	    self.error(302)
	else:
	    b = LinkedInStatusUpdater(user)
	    self.response.out.write(b.requestAuthenticationURL())
	    #self.error(302)

