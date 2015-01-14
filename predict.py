import os
import time
import urllib2
from os import path
from cpredict import quick_find, quick_predict, PredictException

def massage_tle(tle):
    try:
        # TLE may or may not have been split into lines already
        if isinstance(tle, basestring):
            tle = tle.rstrip().split('\n')
        assert len(tle) == 3, "TLE must be 3 lines, not %d: %s" % (len(tle), tle)
        return tle
        #TODO: print a warning if TLE is 'too' old
    except Exception as e:
        raise PredictException(e)

def massage_qth(qth):
    try:
        assert len(qth) == 3, "%s must consist of exactly three elements: (lat(N), long(W), alt(m))" % qth
        return (float(qth[0]), float(qth[1]), int(qth[2]))
    except ValueError as e:
        raise PredictException("Unable to convert '%s' (%s)" % (qth, str(e)))
    except Exception as e:
        raise PredictException(e)

def observe(tle, qth, at=None):
    tle = massage_tle(tle)
    qth = massage_qth(qth)
    if at is None:
        at = time.time()
    return quick_find(tle, at, qth)

def transits(tle, qth, ending_after=None, ending_before=None):
    tle = massage_tle(tle)
    qth = massage_qth(qth)
    if ending_after is None:
        ending_after = time.time()
    ts = ending_after
    while True:
        transit = quick_predict(tle, ts, qth)
        t = Transit(tle, qth, start=transit[0]['epoch'], end=transit[-1]['epoch'])
        if (ending_before != None and t.end > ending_before):
            break
        if (t.end > ending_after):
            yield t
        # Need to advance time cursor so predict doesn't yield same pass
        ts = t.end + 60     #seconds seems to be sufficient

# Return a value x that's within epsilon of the value that maximizes the concave
# or strictly monotonic function fx over the interval [a,b]
# Used primarily to find the peak of a transit
def maximize_concave(f, start, end, epsilon=0.1):
    x = float(start+end)/2
    step = float(end-start)
    while (step > epsilon):
        step /= 4
        direction = None
        while True:
            w = max(x - step, start)
            y = min(x + step, end)
            next_x = max((f(w), w), (f(y), y))[1]
            if x == new_x:
                break
            # break if we've switched directions at this step size
            if (direction is not None) and (direction * (new_x - x) < 0):
                break
            direction = new_x - x
            x = new_x

# Transit is a convenience class representing a pass of a satellite over a groundstation.
class Transit():
    def __init__(self, tle, qth, start, end):
        self.tle = massage_tle(tle)
        self.qth = massage_qth(qth)
        self.start = start
        self.end = end

    # return observation within epsilon seconds of maximum elevation
    # NOTE: Assumes elevation is strictly monotonic or concave over the [start,end] interval
    def peak(self, epsilon=0.1):
        ts = maximize_concave(lambda x: self.at(x)['elevation'], self.start, self.end, epsilon)
        return self.at(ts)

    def duration(self):
        return self.end - self.start

    def at(self, t):
        if t < self.start or t > self.end:
            raise PredictException("time %f outside transit [%f, %f]" % (t, self.start, self.end))
        return observe(self.tle, self.qth, t)
        