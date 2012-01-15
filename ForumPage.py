from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import RequestHandler, WSGIApplication
from django.utils import simplejson as json
from google.appengine.ext.webapp.template import render
from google.appengine.ext import db
from wsgiref.handlers import CGIHandler
from google.appengine.ext import webapp
from UserService import UserService
from UserService import GrafiteUser
import os
from time import time

class Thread(db.Model):
    user = db.ReferenceProperty(GrafiteUser)
    posts = db.ListProperty(type(0))
    time = db.DateTimeProperty(auto_now_add=True)
    totalPosts = db.IntegerProperty()


class Post(db.Model):
    user = db.ReferenceProperty(GrafiteUser)
    comment = db.TextProperty()
    time = db.DateTimeProperty(auto_now_add=True)
    threadId = db.ReferenceProperty(Thread)


class ForumPage(webapp.RequestHandler):
    def get(self):
        class temp:
            pass
        DATA = temp()
        
        DATA.user = UserService.getCurrentUser(self)
        
        self.response.headers['Content-Type'] = "text/html"
        
        if self.request.get("t") in (None,""):
            DATA.threads = Thread.all().order("-time").fetch(10)
            for thread in DATA.threads:
                thread.posts_expanded = map(Post.get_by_id,thread.posts)
        else:
            obj = Thread.get_by_id(int(self.request.get("t")))
            if obj is None:
                self.error(404)
                return
            DATA.threads = []
            for thread in DATA.threads:
                thread.posts_expanded = map(Post.get_by_id,thread.posts)

        path = os.path.join(os.path.dirname(__file__), 'html/sidebar.html')
        f = open(path,"r")
        DATA.sidebar = f.read()
        f.close()
        path = os.path.join(os.path.dirname(__file__), 'html/forum.html')
        self.response.out.write(render(path, {'DATA':DATA}))

    def post(self):
        user = UserService.getCurrentUserOrRedirect(self)
        if not user:
            return
        typ = self.request.get("type")
        if typ == "CreateThreadPost":
            self.response.headers.add_header("Content-Type","application/json")
            text = self.request.get("text")
            
            p = Post(user=user.key(), comment=text) 
            tp = Thread(user=user.key(),posts=[p.put().id()], totalPosts = 1)
            p.threadId = tp.put()
            p.put()

            path = os.path.join(os.path.dirname(__file__), 'html/forum/CreateNewPost.html')
            html = render(path, {'post':p})

            self.response.out.write(json.dumps({"result":"success",
                "html":html,
                "divId":"divThread_%d"%long(tp.key().id())}))

        elif typ == "ReplyPost":
            self.response.headers.add_header("Content-Type","application/json")
            text = self.request.get("text")
            threadId = long(self.request.get("threadId"))
            thread = Thread.get_by_id(threadId)
            
            p = Post(user=user, comment=text, threadId = thread)
            
            thread.posts.append(p.put().id())
            thread.totalPosts = thread.totalPosts + 1
            thread.put()

            path = os.path.join(os.path.dirname(__file__), 'html/forum/NewReply.html')
            html = render(path, {'post':p})

            self.response.out.write(json.dumps({
            "result":"success",
            "html":html,
            "divId":"rowComment_%d"%long(p.key().id())}))

        elif typ == "DeletePost":
            self.response.headers.add_header("Content-Type","application/json")
            if self.request.get("postId") in (None,""):
                self.response.out.write(json.dumps({"result":"error","message":"Invalid Parameters"}))
                return
            postId = long(self.request.get("postId"))
            post,thread = None,None
            try:
                post = Post.get_by_id(postId)
                thread = post.threadId
                if post.key().id() not in thread.posts:
                    raise Exception("")
            except Exception,e:
                self.response.out.write(json.dumps({"result":"error","message":"Thread or post Id is invalid"}))
                return
            pos = thread.posts.index(post.key().id())
            res = {"result":"success"}
            if not pos:
                res['toDelete'] = "divThread_%d"%long(thread.key().id())
                res['deleteType'] = 'Thread'
                #delete the entire thread!
                for everyPost in map(Post.get_by_id, thread.posts):
                    everyPost.delete()
                thread.delete()
            else:
                res['toDelete'] = "rowComment_%d"%long(post.key().id())
                res['deleteType'] = 'Comment'
                del thread.posts[pos]
                thread.put()
                post.delete()
            self.response.out.write(json.dumps(res))
