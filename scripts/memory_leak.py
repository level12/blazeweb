import time
import urllib2

url = 'http://antec:5000'

while True:
    usock = urllib2.urlopen(url)
    data = usock.read()
    assert 'index' in data
    time.sleep(0.01)
