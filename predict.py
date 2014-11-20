import time
import urllib2
from os import path
from math import ceil, floor
from datetime import datetime
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
        after = after if after != None else time.time()
        crs = after
        prev_transit_end = None
        while True:
            transit = quick_predict(self.tle, crs, self.qth)
            start = transit[0]['epoch']
            end = transit[-1]['epoch']
            peak = max(transit, key=lambda t:t['elevation'])['elevation']
            t = Transit(self, start, end, peak)
            if (t.start < prev_transit_end):    # None is lower than any integer
                # HACK: predict doesn't reliably yield a new pass if the start time
                #       is 'too' close to the end of the previous pass.
                crs += 1
                continue
            if (t.start > after):
                yield t
            prev_transit_end = t.end
            crs = t.end+1     # Advance the cursor past the end of the calculated transit

# Transit is a convenience class representing a pass of a satellite over a groundstation
class Transit():
    def __init__(self, observer, start, end, peak):
        self.observer = observer
        self.start = start
        self.peak = peak
        self.end = end

    def satellite(self):
        return self.observer.tle[0]

    def groundstation(self):
        return self.observer.name or self.observer.qth

    def max_elevation(self):
        #TODO: Optimize (or at least cache) this.  Also, sub-second granularity?
        return max([self.observer.observe(t)['elevation'] for t in range(int(self.start), int(ceil(self.end)))])

    def at(timestamp):
        # TODO: Throw exception if out of start, end bounds?
        return self.observer.observe(timestamp)

    def __str__(self):
        return "Transit(%s, %s, %s, %s)" % (self.start, self.end, self.max_elevation(), self.peak)
