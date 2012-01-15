import urlparse
from urllib import FancyURLopener
from google.appengine.api.urlfetch import fetch as urlfetch, GET, POST
from BeautifulSoup import BeautifulSoup as bs
import re

class LinkFetcher(FancyURLopener): #throws error while constructing!
    def __init__(self, url):
        self.mainURL = url
        self._error_bit = False
        if not urlparse.urlparse(self.mainURL).scheme:
            self.mainURL = "http://" + self.mainURL
        try:
            self._res = urlfetch(self.mainURL)
            if self._res.status_code != 200:
                raise Exception()
            self.soup = bs(self._res.content)
        except Exception,e:
            self._error_bit = True
            raise e
        
    def http_error_default(self,req, fp, code, msg, hdrs):
        self._error_bit = True

    def hasError(self):
        return self._error_bit

    def url(self):
        return self.mainURL

    def title(self):
        title = str(self.soup.head.title)
        if not title:
            title="<title>%s</title>"%self.url()
        rg = re.compile("<title>(.*?)</title>",re.I)
        return rg.search(title).group(1)
    
    def thumbnail(self):
        parsed = list(urlparse.urlparse(self.mainURL))
        thumbnailURL = ""
        images = []
        intRe = re.compile("([0-9]+)")
        for image in self.soup.findAll("img"):
            if image["src"].lower().startswith("http"):
                thumbnailURL = image['src']
            else:
                parsed[2] = image['src']
                thumbnailURL = urlparse.urlunparse(parsed)
            break
            obj = {}
            obj['src'] = image["src"]
            obj['width'] = image['width']
            obj['height'] = image['height']
            images.append(obj)
        return thumbnailURL

    def description(self):
        metas = self.soup.findAll("meta")
        for meta in metas:
            if 'name' in meta and meta['name'].lower() == 'description':
                return meta['content']
        return "Posted via Grafite!"
            
def fetch(url):
    parsed = list(urlparse.urlparse(url))

    for image in soup.findAll("img"):
        print "Image: %(src)s" % image
        filename = image["src"].split("/")[-1]
        parsed[2] = image["src"]
        outpath = os.path.join(out_folder, filename)
        if image["src"].lower().startswith("http"):
            urlretrieve(image["src"], outpath)
        else:
            urlretrieve(urlparse.urlunparse(parsed), outpath)
    