import time
from cpredict import quick_find, quick_predict, PredictException

def load_tle(source):
    try:
        if hasattr(source, 'tle'):
            source = source.tle() if callable(source.tle) else source.tle
        if isinstance(source, basestring):
            source = source.rstrip().split('\n')
        assert len(source) == 3, "TLE must be exactly 3 lines: %s" % source
        return source
        #TODO: print a warning if TLE is 'too' old
    except Exception as e:
        raise PredictException(e)

def load_qth(source):
    try:
        if hasattr(source, 'qth'):
            source = source.qth() if callable(source.qth) else source.qth
        assert len(source) == 3, "%s does not match: (lat(N), long(W), alt(m))" % source
        return (float(source[0]), float(source[1]), int(source[2]))
    except ValueError as e:
        raise PredictException("Unable to convert '%s' (%s)" % (source, str(e)))
    except Exception as e:
        raise PredictException(e)

def observe(sat, site, at=None):
    tle = load_tle(sat)
    qth = load_qth(site)
    if at is None:
        at = time.time()
    return quick_find(tle, at, qth)

def transits(sat, site, ending_after=None, ending_before=None):
    tle = load_tle(sat)
    qth = load_qth(site)
    if ending_after is None:
        ending_after = time.time()
    ts = ending_after
    while True:
        transit = quick_predict(tle, ts, qth)
        start = transit[0]['epoch']
        end = transit[-1]['epoch']
        t = Transit(sat, site, start, end, manual_tle=tle, manual_qth=qth)
        if (ending_before != None and t.end > ending_before):
            break
        if (t.end > ending_after):
            yield t
        # Need to advance time cursor so predict doesn't yield same pass
        ts = t.end + 60     #seconds seems to be sufficient

# Transit is a convenience class representing a pass of a satellite over a groundstation.
class Transit():
    def __init__(self, sat, site, start, end, manual_tle=None, manual_qth=None):
        self.sat = sat
        self.site = site
        self.tle = manual_tle or load_tle(sat)
        self.qth = manual_qth or load_qth(site)
        self.start = start
        self.end = end

    # return observation within epsilon seconds of maximum elevation
    # NOTE: Assumes elevation is strictly monotonic or concave over the [start,end] interval
    def peak(self, epsilon=0.1):
        ts =  (self.end + self.start)/2
        step = (self.end - self.start)
        while (step > epsilon):
            step /= 4
            # Ascend the gradient at this step size
            direction = None
            while True:
                mid   = observe(self.tle, self.qth, ts)['elevation']
                left  = observe(self.tle, self.qth, ts - step)['elevation']
                right = observe(self.tle, self.qth, ts + step)['elevation']
                # Break if we're at a peak
                if (left <= mid >= right):
                    break
                # Ascend up slope
                slope = -1 if (left > right) else 1
                # Break if we stepped over a peak (switched directions)
                if direction is None:
                    direction = slope
                if direction != slope:
                    break
                # Break if stepping would take us outside of transit
                next_ts = ts + (direction * step)
                if (next_ts < self.start) or (next_ts > self.end):
                    break
                # Step towards the peak
                ts = next_ts
        return self.at(ts)

    # Return portion of transit above a certain elevation
    def above(self, elevation):
        return self.prune(lambda ts: self.at(ts)['elevation'] >= elevation)

    # Return section of a transit where a pruning function is valid.
    # Currently used to set elevation threshold, could also be used for site-specific horizon masks.
    # fx must either return false everywhere or true for a contiguous period including the peak
    def prune(self, fx, epsilon=0.1):
        peak = self.peak()['epoch']
        if not fx(peak):
            return Transit(self.tle, self.qth, peak, peak)
        if fx(self.start):
            start = self.start
        else:
            left, right = self.start, peak
            while ((right - left) > epsilon):
                mid = (left + right)/2
                if fx(mid):
                    right = mid
                else:
                    left = mid
            start = right
        if fx(self.end):
            end = self.end
        else:
            left, right = peak, self.end
            while ((right - left) > epsilon):
                mid = (left + right)/2
                if fx(mid):
                    left = mid
                else:
                    right = mid
            end = left
        return Transit(self.tle, self.qth, start, end)

    def duration(self):
        return self.end - self.start

    def at(self, t):
        if t < self.start or t > self.end:
            raise PredictException("time %f outside transit [%f, %f]" % (t, self.start, self.end))
        return observe(self.tle, self.qth, t)
        