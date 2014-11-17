import time
import urllib2
from datetime import datetime
from cpredict import quick_find, quick_predict

def tle(norad_id):
    res = urllib2.urlopen("http://tle.nanosatisfi.com/%s" % str(norad_id))
    if res.getcode() != 200:
        raise urllib2.HTTPError("Unable to retrieve TLE from tle.nanosatisfi.com. HTTP code(%s)" % res.getcode())
    return res.read().rstrip()

class Observer():
    def __init__(self, tle, qth=None):
        self.tle = tle.rstrip().split('\n')
        self.qth = qth

    def observe(self, at = time.time()):
        if self.qth:
            return quick_find(self.tle, at, self.qth)
        else:
            return quick_find(self.tle, at)

    # Returns a generator of passes occuring between start_time and end_time
    def passes(self, start_time = time.time(), end_time = None):
        crs = start_time
        while True:
            p = Transit(quick_predict(*filter(None, [self.tle, crs, self.qth])))
            if (p.start_time() < start_time):
                continue
            yield p
            if (end_time and p.end_time() > end_time):
                break
            # Need to advance time cursor sufficiently far so predict doesn't yield same pass
            crs = p.end_time() + 60 #seconds seems to be sufficient

# Transit is a thin wrapper around the array of dictionaries returned by cpredict.quick_predict
class Transit():
    def __init__(self, observations):
        self.points = observations

    def start_time(self):
        return self.points[0]['epoch']

    def end_time(self):
        return self.points[-1]['epoch']

    # TODO: Verify quick_predict returns observation at peak of transit
    def max_elevation(self):
        return max([p['elevation'] for p in self.points])

    def __getitem__(self, key):
        return self.points[key]

    def __str__(self):
        return "Transit(from: %s to: %s, max elevation: %s)" % (self.start_time(), self.end_time(), self.max_elevation())
