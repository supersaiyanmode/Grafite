from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from wsgiref.handlers import CGIHandler
from google.appengine.ext import webapp
from google.appengine.ext.webapp.template import render
import os
from UserService import UserService

class LoginPage(webapp.RequestHandler):
    def get(self):
	class temp:
	    pass
	DATA = temp()
	DATA.user = UserService.getCurrentUser(self)
	DATA.to = "/userHome"
	if self.request.get("to") not in (None,""):
	    DATA.to = self.request.get("to")

	path = os.path.join(os.path.dirname(__file__), 'html/login.html')
        self.response.out.write(render(path, {'DATA':DATA}))
