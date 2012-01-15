from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from google.appengine.ext.webapp.template import render
from google.appengine.ext import db
from wsgiref.handlers import CGIHandler
from google.appengine.ext import webapp
import os
from UserService import UserService

class HelpService(webapp.RequestHandler):
    def get(self):
	class temp:
	    pass
	DATA = temp()
	DATA.user = UserService.getCurrentUser(self)
	
	path = os.path.join(os.path.dirname(__file__), 'html/help/chatbot.html')
        self.response.out.write(render(path, {'DATA':DATA}))