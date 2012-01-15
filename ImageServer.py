from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api.urlfetch import fetch as urlfetch
from django.utils import simplejson as json
from google.appengine.ext import db
import logging

class ImageMap(db.Model):
    image = db.BlobProperty(default=None)
    contentType = db.StringProperty()
    
    @staticmethod
    def updateImage(key, url):
        logging.debug("Update request! %s %s"%(key,url))
        #fetch the image
        res = urlfetch(url)
        if res.status_code != 200:
            return {"result":"error","message":"Unable to retrieve URL"}
        contentType = res.headers['Content-Type']
        if contentType[:contentType.find('/')].lower() != 'image':
            return {"result":"error","message":"Invalid Image"}
        record = None
        if ImageMap.exists(key):
            record = ImageMap.get_by_key_name(key)
        else:
            record = ImageMap(key_name=key)

        record.contentType = contentType
        record.image = db.Blob(res.content)
        record.put()
        return {"result":"success","key":key}
                
    @staticmethod
    def exists(key):
        try:
            m = ImageMap.get_by_key_name(key)
            if m:
                return True
            else:
                return False
        except Exception,e:
            return False

class ImageServer(webapp.RequestHandler):
    def get(self,imageId):
        if ImageMap.exists(imageId):
            m = ImageMap.get_by_key_name(imageId)
            self.response.headers['Content-Type'] = m.contentType
            self.response.out.write(m.image)
        else:
            self.error(404)

	