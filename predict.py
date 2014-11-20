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

class Observer():
    def __init__(self, tle, qth="~/.predict/predict.qth"):
        ## ETL tle and qth data
        self.tle = tle.rstrip().split('\n') if isinstance(tle, basestring) else tle
        if isinstance(qth, basestring):
            raw = open(path.expanduser(qth)).readlines()
            lines = [l.strip() for l in raw]
            assert len(lines) == 4, "qth file '%s' must contain exactly 4 lines (name, lat, long, alt)" % qth
            qth = lines[1:]+lines[:1] # move name last
        assert 3 <= len(qth) <= 4, "qth must follow (lat, long, alt[, name])"
        # Attempt conversion to format required for predict.quick_find
        self.qth = (float(qth[0]), float(qth[1]), int(qth[2]))
        self.name = qth[3] if len(qth) >= 4 else None
        
    def observe(self, at = None):
        at = at or time.time()
        if self.qth:
            return quick_find(self.tle, at, self.qth)
        else:
            return quick_find(self.tle, at)

    # Returns a generator of passes occuring entirely between 'after' and 'before' (epoch)
    def passes(self, after=None, before=None):
        after = after or time.time()
        crs = after
        while True:
            p = quick_predict(self.tle, crs, self.qth)
            t = Transit(self, p[0]['epoch'], p[-1]['epoch'])
            if (t.start < after):
                continue
            if (before and before < t.end):
                break
            yield t
            # Need to advance time cursor sufficiently far so predict doesn't yield same pass
            crs = p.end_time() + 60 #seconds seems to be sufficient

# Transit is a thin wrapper around the array of dictionaries returned by cpredict.quick_predict
class Transit():
    def __init__(self, observer, start, end):
        self.observer = observer
        self.start = start
        self.end = end

    def satellite(self):
        return self.observer.tle[0]

    def groundstation(self):
        return self.observer.name or self.observer.qth

    # TODO: Verify quick_predict returns observation at peak of transit
    def max_elevation(self):
        # TODO: Implement (binary search? Set at initialization time?)
        return None

    def at(timestamp):
        # TODO: Throw exception if out of start, end bounds?
        return self.observer.observe(timestamp)

    def __str__(self):
        return "Transit(%s, %s, %s)" % (self.start, self.end, self.max_elevation())
