print "Content Type: text/html"
print ""
f = open("html/home.html","r")
for x in f:
    print x
f.close()
