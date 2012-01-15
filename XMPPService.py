from google.appengine.api import xmpp
from google.appengine.ext import webapp
from UserService import GrafiteUser
import urllib
import logging
import re
from time import time
from FacebookService import FacebookService
from BuzzService import BuzzService
from TwitterService import TwitterService
from StatusService import StatusService
from ShortLink import getShortUrl
from RegisterService import RegisterService
from ReminderService import ReminderService

STR_HELLO = "Hey, hello! :-)\n"
STR_PROMPT_REGISTER = "Please register yourself from grafiteapp.appspot.com/register"
STR_REGISTRATION_SUCCESS = "Thanks for registration. :-)\nJust remember that password. You can login from the website using your Gtalk id and that password."
STR_REGISTRATION_ALREADY_DONE = "Hey, you are already registered!"
STR_REGISTRATION_INVALID_TOKEN = "Umm, can you re-check the code?"
STR_REGISTRATION_FAILURE = "Err.. Something went wrong with the registration :-( Can you retry?"
STR_REGISTRATION_FAILURE_EMAIL_TAKEN = "Umm, this emailId has been registered. Registration failed! :-("
STR_PROMPT_REGISTER_SERVICE = "Please authorize me to fetch the %s details on your behalf. Click this link: %s\n"
STR_UNKNOWN_CMD1 = "Umm, what?"
STR_UNKNOWN_CMD2 = "Grr.. I didnt get what you just said. Type \"help\" to get a list of supported commands\n"
STR_UNKNOWN_CMD3 = "Try 'help', I told you. Type \"help\" to get a list of supported commands\n"
STR_UNKNOWN_CMD4 = "Umm, I guess I should learn your language. Can you please try understanding English? :-P\nType \"help\" to get a list of supported commands\n"
STR_PLEASE_WAIT = "Hey, just hold on.. :-)"
STR_UNABLE_SERVICE = "Unable to retrieve your latest %s! :-("
STR_NO_STATUS_SPECIFIED = "Good try, but I cant make an empty-status update. Check the syntax.. :-)"
STR_NO_LINK_SPECIFIED = "I guess, you forgot to type in the actual URL.. :-)"
STR_WRONG_SYNTAX = "Grr.. I would suggest you to go through the syntaxes once more.."
STR_REMINDER_ADDED = 'Reminder added! :-)'
STR_HELP_MESSAGE = """The following are the commands that I understand.

*help* - Displays this message.

*status* - Displays the latest status updates from the services you subscribed to.

*update <status>* - Updates all your services with the status.

*shorten <url>* - Shortens the given URL using goo.gl

*home* - Shows your Grafite's home page.

*remind in <value> <timeDeltaType> <reminderText>* - Sets a reminder.

Check out the Help section for details here: http://goo.gl/LUDUf.
"""

class MyXmppHandler(webapp.RequestHandler):
    def _getUserName(self,sender):
        return sender[:sender.find("/")]
	
    def I_dont_understand(self):
        global STR_UNKNOWN_CMD1,STR_UNKNOWN_CMD2,STR_UNKNOWN_CMD3,STR_UNKNOWN_CMD4
        return eval('STR_UNKNOWN_CMD'+str(1+ int(time())%4))

    def post(self):
        msg = xmpp.Message(self.request.POST)
        logging.debug(self.request.body + "$" + str(msg))
        commands = ['status','help','update','home','shorten','remind','verify']
        msgSplit = msg.body.split(' ')
        
        self.user = GrafiteUser.getUser(username=self._getUserName(msg.sender))
        if self.user is None and msgSplit[0].lower() != "verify":
            msg.reply(STR_HELLO + "\n" + STR_PROMPT_REGISTER)
            return
        
        logging.debug("*CHAT*: " + self.user.key().name())
        #login the user!
        if self.user:
            res = GrafiteUser.login(self.user.key().name(), self.user.password, "XMPP")
            self.user.accessToken = res[1]
        elif msgSplit[0].lower() != 'verify':
            msg.reply("Hey, I couldn't really identify who you are! :-( Please register yourself..")
            return
        if msgSplit[0].lower() in commands:
            try:
                getattr(self,"cmd_" + msgSplit[0].lower())(msg)
            except Exception, e:
                msg.reply("Error!\n" + str(e))
                import traceback
                msg.reply(traceback.format_exc())
        else:
            msg.reply(self.I_dont_understand())

    def cmd_remind(self,message):
        text = message.body[len('update '):]
        textSplit = text.split(' ')
        if textSplit[0].lower() != "in":
            message.reply("1" + STR_WRONG_SYNTAX)
            return
        timeVal = 0
        try:
            timeVal = int(textSplit[1])
        except Exception,e:
            #message.reply("2" +STR_WRONG_SYNTAX)
            message.reply(str(e))
            return
        timeType = ""
        if textSplit[2].lower() in ('seconds','minutes','hours','days','weeks'):
            timeType = textSplit[2].lower()
        else:
            #message.reply("3" +STR_WRONG_SYNTAX)
            message.reply(str(e))
            return
        if ReminderService.addReminder(timeVal,timeType,' '.join(textSplit[3:]), self.user):
            message.reply(STR_REMINDER_ADDED)

    def cmd_update(self,message):
        message.reply(STR_PLEASE_WAIT)
        text = message.body[len('update '):]
        if len(str(text)) == 0:
            message.reply(STR_NO_STATUS_SPECIFIED)
            return
	
        res = StatusService.updateStatus(text,self.user)
        if res['result'] == "success":
            message.reply("\n".join(["*%s*:%s"%(s,res['data'][s]['result']) for x,s in enumerate(res)]))
        else:
            message.reply("Oops, something went wrong!")

    def cmd_status(self,message):
        message.reply(STR_PLEASE_WAIT)
        res = ""
	
        for service in ['Facebook','Buzz','Twitter']:
            res = res + '*%s*\n'%service
            obj = eval(service+"Service").getStatus(self.user)
            
            if obj['result'] == 'error':
                if obj['message'] == 'unauthorised':
                    res = res + STR_PROMPT_REGISTER_SERVICE%(service,obj['link'])
                else:
                    res = res + STR_UNABLE_SERVICE%(service + ' status')
            else:
                res = res + "_" + obj['status'] + "_\n\n"
                if 'comments' in obj: #Buzz and FB
                    res = res + str(obj['comments'])+" comments\n"
                    res = res + str(obj['likes'])+" likes\n"
                else: #twitter
                    res = res + str(obj['retweets'])+" retweets\n"
            
            res = res + "\n\n"
        message.reply(res)

    def cmd_help(self,message):
        message.reply(STR_HELP_MESSAGE)
	
    def cmd_home(self,message):
        message.reply(getShortUrl("http://grafiteapp.appspot.com/userHome?access_token=%s&redirect=%s"%
			(self.user.accessToken,'/')))

    def cmd_verify(self,message):
        from RegisterService import GrafiteUserUnregistered
        if self.user is not None:
            message.reply(STR_REGISTRATION_ALREADY_DONE)
            return
        msgSplit = message.body.split(' ')
        if len(msgSplit) != 2:
            message.reply(STR_PROMPT_REGISTER)
            return
        res = GrafiteUserUnregistered.all().filter("verifyToken =",msgSplit[1])
        if not res.count():
            message.reply(STR_REGISTRATION_INVALID_TOKEN)
            return

        newUser = res.fetch(1)[0]
        
        username = self._getUserName(message.sender)
        res,token,t = GrafiteUser.createNewUser(username, newUser.password, "Google Talk")
        if res != "success":
            message.reply(STR_REGISTRATION_ALREADY_DONE)
            return

        user = GrafiteUser.get_by_key_name(username)
        
        if user is None:
            message.reply(STR_REGISTRATION_FAILURE)
            return
        if GrafiteUser.all().filter("emailId =",newUser.emailId).count():
            message.reply(STR_REGISTRATION_FAILURE_EMAIL_TAKEN)
            return
        user.emailId = newUser.emailId
        user.nickname = newUser.nickname
        user.put()
        newUser.delete()
        message.reply(STR_REGISTRATION_SUCCESS)

    def cmd_shorten(self,message):
        url = message.body[len('shorten '):]
        if len(str(url)) == 0:
            message.reply(STR_NO_LINK_SPECIFIED)
            return
        message.reply(getShortUrl(url))

    @staticmethod
    def pingUser(user, text):
        xmpp.send_message(user.key().name(), text)
