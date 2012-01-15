from google.appengine.ext import webapp
from django.utils import simplejson as json
from StatusService import Status,StatusService
from UserService import GrafiteUser,UserService
from ReminderService import ReminderService

class StatisticsService(webapp.RequestHandler):
    def get(self):
        self.response.headers.add_header('Content-Type','application/json')
        res = dict(result="success")
        res['TotalUsers'] = GrafiteUser.all().count()
        user = GrafiteUser.all().order("-dateJoined").fetch(1)[0]
        res['LatestUserHTML'] = '<a href="%s">%s</a>'%(user.profileUrl,user.Nickname)
        obj = GrafiteUser.getOnlineUsers()
        res['OnlineUsersList'] = obj['value']
        res['OnlineUsersCount'] = obj['count']
        res['TotalStatuses'] = Status.getTotalStatuses()
        res['TotalReminders'] = ReminderService.getCount()
        
        user = UserService.getCurrentUser(self)
        if user:
            res['user'] = {}
            res['user']['Statuses'] = StatusService.getUserStatusCount(user)
            res['user']['Reminders'] = ReminderService.getUserCount(user)
        self.response.out.write(json.dumps(res))