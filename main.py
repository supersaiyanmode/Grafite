from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from LoginPage import LoginPage
from UserService import UserService
from UserHomePage import UserHomePage
from UserHomePage import UserProfilePage
from FacebookService import FacebookService
from BuzzService import BuzzService
from TwitterService import TwitterService
from StatusService import StatusService
from XMPPService import MyXmppHandler
from ReminderService import ReminderService
from StatisticsService import StatisticsService
from ImageServer import ImageServer
from RegisterService import RegisterService
from ForumPage import ForumPage
from HelpService import HelpService
from ApiAccess import ApiAccessService
from ShoutBox import ShoutBoxService

l = []
l.append(('/_ah/xmpp/message/chat/', MyXmppHandler))
l.append(('/',UserHomePage))
l.append(('/login',LoginPage))
l.append(('/register', RegisterService))
l.append(('/forum',ForumPage))
l.append(('/account',UserService))
l.append(('/userHome',UserHomePage))
l.append(('/shout',ShoutBoxService))
l.append(('/dp/(.*?)/',ImageServer))
l.append(('/api/(.*)', ApiAccessService))
l.append(('/statistics',StatisticsService))
l.append(('/users/(.*?)/?',UserProfilePage))
l.append(('/facebook/(.*?)/.*',FacebookService))
l.append(('/buzz/(.*?)/.*', BuzzService))
l.append(('/twitter/(.*?)/.*',TwitterService))
l.append(('/status',StatusService))
l.append(('/help',HelpService))
l.append(('/reminder',ReminderService))
application = webapp.WSGIApplication(l,debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
