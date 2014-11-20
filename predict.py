import time
import urllib2
from datetime import datetime
from os import path
from cpredict import quick_find, quick_predict

def tle(norad_id):
    res = urllib2.urlopen("http://tle.nanosatisfi.com/%s" % str(norad_id))
    if res.getcode() != 200:
        raise urllib2.HTTPError("Unable to retrieve TLE from tle.nanosatisfi.com. HTTP code(%s)" % res.getcode())
    return res.read().rstrip()

def qth(pot=path.expanduser("~/.predict/predict.qth")):
    if isinstance(pot, basestring):
        assert path.isfile(pot), "qth file '%s' does not exist or is not readable." % pot
        pot = [l.strip() for l in open(pot).readlines()]
        assert len(pot) == 4, "qth file '%s' must contain exactly 4 lines (name, lat, long, alt)" % pot
        pot = pot[1:]+pot[:1] # move name last

    # Validate and attempt necessary type conversions
    assert 3 <= len(pot) <= 4, "qth must follow (lat, long, alt[, name])"
    qth = (float(pot[0]), float(pot[1]), int(pot[2]))
    if len(pot) == 4:
        qth = qth + (str(pot[3]),)

    return qth

class Observer():
    def __init__(self, tle, qth=None:
        self.tle = tle.rstrip().split('\n')
        if qth == None:
            default =
            qth = [l.strip() for l in open(pot).readlines()]


    def observe(self, at = time.time()):
        if self.qth:
            return quick_find(self.tle, at, self.qth)
        else:
            return quick_find(self.tle, at)

    # Returns a generator of passes occuring entirely between 'after' and 'before' epoch times
    def passes(self, after=time.time(), before=None):
        crs = after
        while True:
            p = Transit(quick_predict(*filter(None, [self.tle, crs, self.qth])))
            if (p.start_time() < after):
                continue
            if (before and before < p.end_time()):
                break
            yield p
            # Need to advance time cursor sufficiently far so predict doesn't yield same pass
            crs = p.end_time() + 60 #seconds seems to be sufficient

# Transit is a thin wrapper around the array of dictionaries returned by cpredict.quick_predict
class Transit():
    def __init__(self, observer, start, end):
        self.observer = observer
        

    def start_time(self):
        return self.points[0]['epoch']

    def end_time(self):
        return self.points[-1]['epoch']

    # TODO: Verify quick_predict returns observation at peak of transit
    def max_elevation(self):
        return max([p['elevation'] for p in self.points])

    def position(ts):
        return self.calculator(ts)

    def __getitem__(self, key):
        return self.points[key]

    def __str__(self):
        return "Transit(%s, %s, %s)" % (self.start_time(), self.end_time(), self.max_elevation())
