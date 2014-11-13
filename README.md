PyPredict
=======

Satellite tracking and pass prediction library for Python.

PyPredict is a C Python extension directly adapted from the ubiquitous [predict](http://www.qsl.net/kd2bd/predict.html) satellite tracking tool.
We aim for result-parity and it should produce identical values on the same inputs.

If you think you've found an error, please include predict's differing output in the bug report.
If you think you've found a bug in predict, please report and we'll coordinate with upstream.
### Installation
```
sudo apt-get install python-dev
sudo python setup.py install
```
## Usage
PyPredict provides a convenient API for exposing exposes underlying functionality as well as providing a slightly convenient API.
#### Convenience API
```
import predict
tle = predict.tle(40044)
o = predict.Observer(tle)
print o.observe()
p = o.passes()
for i in range(1,10):
	np = p.next()
	print("%f\t%f\t%f" % (np.start_time(), np.end_time() - np.start_time(), np.max_elevation()))
```
#### C Implementation
```
predict.quick_find(tle.split('\n'), time.time(), (37.7727, 122.407, 25))
predict.quick_predict(tle.split('\n'), time.time(), (37.7727, 122.407, 25))
```
##API
**`quick_find`**(_tle[, time[, qth]]_)  
&nbsp;&nbsp;&nbsp;&nbsp;_time_ defaults to now  
&nbsp;&nbsp;&nbsp;&nbsp;_qth_ defaults to latitude, longitude, altitude stored in ~/.predict/predict.qth

**`quick_predict`**(_tle[, time[, qth]]_)

**`tle`**(*norad_id*)

**`Observer`**(_tle[, qth]_)

&nbsp;&nbsp;&nbsp;&nbsp;**`observe`**(_[time]_)

&nbsp;&nbsp;&nbsp;&nbsp;**`passes`**(_[time]_)

**`PassGenerator`**(_tle[, time[, qth]]_)

**`Transit`**(_points_)

&nbsp;&nbsp;&nbsp;&nbsp;**`start_time`**()

&nbsp;&nbsp;&nbsp;&nbsp;**`end_time`**()

&nbsp;&nbsp;&nbsp;&nbsp;**`max_elevation`**()

