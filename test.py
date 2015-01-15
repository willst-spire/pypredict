#!/usr/bin/env python

import unittest, time
import predict
from cpredict import quick_find, quick_predict, PredictException

# fetched from http://tle.nanosatisfi.com/40044
TLE = "0 LEMUR 1\n1 40044U 14033AL  15013.74135905  .00002013  00000-0  31503-3 0  6119\n2 40044 097.9584 269.2923 0059425 258.2447 101.2095 14.72707190 30443"
QTH = "fuze-sfgs\n37.7727\n122.4070\n25"
STEP = 15
# T1_IN_TRANSIT is inside the transit that starts after T2_NOT_IN_TRANSIT
T1_IN_TRANSIT     = 1421214440.07
T2_NOT_IN_TRANSIT = 1421202456.13

# predict.transits(['0 LEMUR 1', '1 40044U 14033AL  15014.69256446  .00001985  00000-0  31062-3 0  6148', '2 40044 097.9586 270.2249 0059407 255.0811 104.3815 14.72710828 30589'],time.struct_time(tm_year=2015, tm_mon=1, tm_mday=15, tm_hour=6, tm_min=15, tm_sec=40, tm_wday=3, tm_yday=15, tm_isdst=0),(37.7727, 122.407, 25))

def transit_to_tuple(transit):
  return (transit.start, transit.duration(), transit.peak(), transit.qth, transit.tle)

class TestPredict(unittest.TestCase):

  def test_transit_prediction_from_within_and_outside_start_time(self):
    tle = predict.massage_tle(TLE)
    qth = predict.massage_qth(QTH.split("\n")[-3:])
    
    at  = T1_IN_TRANSIT
    obs = predict.observe(tle, qth, at=at)
    self.assertTrue(obs['elevation'] > 0)

    t1t = next(predict.transits(tle, qth, ending_after=at))

    at  = T2_NOT_IN_TRANSIT
    obs = predict.observe(tle, qth, at=at)
    self.assertTrue(obs['elevation'] < 0)

    # should not raise a StopIteration
    t2t = next(predict.transits(tle, qth, ending_after=at))
    
    # t1_transit and t2_transit should be the same transit
    self.assertAlmostEqual(t1t.start, t2t.start, delta=1)
    self.assertAlmostEqual(t1t.peak()['elevation'], t2t.peak()['elevation'], delta=0.01)

    # manually construct a transit whose peak is at the end of the transit to verify 
    # transit.peak code is working
    t3t = predict.Transit(tle, qth, t1t.start, t1t.peak()['epoch'])
    self.assertAlmostEqual(t1t.peak()['elevation'], t3t.peak()['elevation'])

  def test_specific_error_case(self):
    tle   = ['0 FLOCK 1B 18', '1 40139U 98067FE  15014.85270610  .03916854  11853-4  20858-2 0  3781', '2 40139 051.6205 115.5329 0008014 321.4719 038.6063 16.19156275 20601']
    qth   = (37.7727, 122.407, 25)
    begin = 1421305422
    end   = 1421391822

    list(predict.transits(tle, qth, ending_after=begin, ending_before=end))
    # This throws the following exception:
    # PredictException: Start must be within one year of current date.

    # Replacing `predict.py:42` with the following shows the last element from quick_predict 
    # (out of 10) has an `epoch` that is before the previous observation. Like ~40 years before the
    # previous observation and when it gets fed back into quick_predict it throws an error
    # try:
    #     transit = quick_predict(tle, ts, qth)
    # except Exception:
    #     raise Exception("\n%s\n\n%s" % (transit[-2],transit[-1]))

    # {'decayed': 0, 'elevation': 1.6884189649385142, 'name': '0 FLOCK 1B 18', 'norad_id': 40139, 'altitude': 192.68465500269485, 'orbit': 2085, 'longitude': 252.69172189088326, 'sunlit': 0, 'geostationary': 0, 'footprint': 3096.859496275198, 'epoch': 1421400944.2215364, 'doppler': -2281.8683039505977, 'visibility': 'N', 'azimuth': 65.24555413517756, 'latitude': 42.006605977814004, 'orbital_model': 'SGP4', 'orbital_phase': 64.36780098891919, 'eclipse_depth': 40.64436817301017, 'slant_range': 1403.1693586159604, 'has_aos': 1, 'orbital_velocity': 28066.692734541226}

    # {'decayed': 0, 'elevation': nan, 'name': '0 FLOCK 1B 18', 'norad_id': 40139, 'altitude': nan, 'orbit': 136502, 'longitude': nan, 'sunlit': 1, 'geostationary': 0, 'footprint': nan, 'epoch': 315446400.0, 'doppler': nan, 'visibility': 'D', 'azimuth': nan, 'latitude': nan, 'orbital_model': 'SGP4', 'orbital_phase': nan, 'eclipse_depth': nan, 'slant_range': nan, 'has_aos': 1, 'orbital_velocity': nan}

if __name__ == '__main__':

  tests = [
    TestPredict
  ]

  for test in tests:
    suite = unittest.TestLoader().loadTestsFromTestCase(test)
    unittest.TextTestRunner(verbosity=2).run(suite)

