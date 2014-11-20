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
        at = at if at != None else time.time()
        return quick_find(self.tle, at)

    # Returns a generator of passes occuring entirely between 'after' and 'before' (epoch)
    def passes(self, after=None, before=None):
        at = at if at != None else time.time()
        crs = after
        while True:
            p = quick_predict(self.tle, crs, self.qth)
            start = p[0]['epoch']
            end = p[-1]['epoch']
            t = Transit(self, start, end)
            if (t.start < after):
                continue
            if (before and before < t.end):
                break
            yield t
            # Need to advance time cursor sufficiently far so predict doesn't yield same pass
            crs = p.end_time() + 60 #seconds seems to be sufficient

# Transit is a convenience class representing a pass of a satellite over a groundstation
class Transit():
    def __init__(self, observer, start, end):
        self.observer = observer
        self.start = start
        self.end = end

    def satellite(self):
        return self.observer.tle[0]

    def groundstation(self):
        return self.observer.name or self.observer.qth

    def max_elevation(self):
        #TODO: Optimize (or at least cache) this.  Also, sub-second granularity?
        return max([self.observer.observe(t)['elevation'] for t in range(self.start, self.end)])

    def at(timestamp):
        # TODO: Throw exception if out of start, end bounds?
        return self.observer.observe(timestamp)

    def __str__(self):
        return "Transit(%s, %s, %s)" % (self.start, self.end, self.max_elevation())
