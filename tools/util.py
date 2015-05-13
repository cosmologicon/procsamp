from __future__ import division
import wave, numpy, math, cmath, random, scipy.optimize

tau = 2 * math.pi

REFERENCE_FREQ = 440  # frequency of the reference note in Hz
MIDDLE_C_DELTA = -9  # number of half-steps that middle C is from the reference frequency

DEFAULT_WIDTH = 0.25  # default width for time-varying window, in seconds

class TimeSeries(list):
	def __init__(self, *args, **kwargs):
		self.fsample = kwargs.get("fsample")
		del kwargs["fsample"]
		list.__init__(self, *args, **kwargs)
	def points(self):
		for k, x in enumerate(self):
			yield k / self.fsample, x
	def duration(self):
		return len(self) / self.fsample
	def nyquist(self):
		return 0.5 * self.fsample


def whitenoise(n):
	return [random.uniform(-1, 1) for _ in range(n)]

def bytestofloat(bytes):
	n = len(bytes)
	N = 1 << (n * 8)
	s = sum(ord(byte) << (k * 8) for k, byte in enumerate(bytes))
	return (s if s < (N >> 1) else s - N) / (N >> 1)

def gettimeseries(wfilename):
	"""Extract the audio time series from the given .wav file"""
	w = wave.open(wfilename)
	nchannels = w.getnchannels()  # 1 or 2 for mono or stereo
	assert nchannels == 1
	sampwidth = w.getsampwidth()
	framerate = w.getframerate()
	n = w.getnframes()
	data = w.readframes(-1)
	assert len(data) == n * sampwidth
	data = [bytestofloat(data[sampwidth*i:sampwidth*(i+1)]) for i in range(n)]
	data = TimeSeries(data, fsample=framerate)
	return data

def realfft(data):
	"""The real-valued Fourier transform of the given data."""
	ft0 = map(abs, numpy.fft.fft(data))
	n = (len(data) + 1) // 2
	freqs = [k * data.fsample / len(data) for k in range(n)]
	return list(zip(freqs, ft0[:n]))

def Aspectrum(data):
	"""Amplitude spectrum."""
	return [(f, x * 2 / len(data)) for f, x in realfft(data)]

def guessfundamental(data):
	"""Best guess at the fundamental frequency of the waveform."""
	fft = realfft(data)
	return max([(p, freq) for freq, p in fft])[1]

def fitfrequency(freq0, data, searchwidth=0.1):
	bounds = [(freq0 * math.exp(-searchwidth), freq0 * math.exp(searchwidth))]
	def gdg(args):
		freq, = args
		A, dA = AdA(freq, data)
		return -A, numpy.array([-dA])
	result = scipy.optimize.minimize(gdg, [freq0], method="L-BFGS-B", jac=True)
	return result.x[0]

def getfundamental(data):
	"""Find the local maximum of the frequency that fits the waveform best."""
	freq0 = guessfundamental(data)
	return fitfrequency(freq0, data)

def tocents(freq):
	"""Number of cents relative to middle C."""
	return -100 * MIDDLE_C_DELTA + 1200 * math.log(freq / REFERENCE_FREQ) / math.log(2)

def tofreq(cents):
	return REFERENCE_FREQ * 2 ** ((cents + 100 * MIDDLE_C_DELTA) / 1200)

def nearestnote(freq):
	"""Frequency of nearest note (integer number of half-steps from 440Hz)."""
	return tofreq(round(tocents(freq), -2))

def Aphi(freq, data):
	"""Returns A, phi such that the freq component of the data is A cos(tau freq t + phi)"""
	omega = -1j * tau * freq
	total = sum(a * cmath.exp(omega * t) for t, a in data.points())
	A, phi = cmath.polar(total)
	return A * 2 / len(data), phi

def AdA(freq, data):
	"""Returns amplitude A and dA/df."""
	omega = -1j * tau * freq
	total, dtotal = 0, 0
	for t, a in data.points():
		z = a * cmath.exp(omega * t)
		total += z
		dtotal += z * t
	total *= 2 / len(data)
	dtotal *= (2 / len(data)) * (-1j * tau)
	A = abs(total)
	dA = (total.real * dtotal.real + total.imag * dtotal.imag) / A
	return A, dA

def Hannwindow(width, fsample):
	n = int(round(width * fsample))
	return [(1 - math.cos(tau * k / n)) / width for k in range(n+1)]

def convolve(xs, ys, offset):
	a = max(0, -offset)
	b = min(len(ys), len(xs) - offset)
	return sum(x*y for x,y in zip(xs[a+offset:b+offset], ys[a:b])) if a < b else 0

def getts(data, width=DEFAULT_WIDTH):
	dt = 0.25 * width
	n = int(math.ceil(data.duration() / dt))
	return [k * dt for k in range(n)]

def Abytime(freq, data, ts=None, width=DEFAULT_WIDTH):
	ts = ts or getts(data, width)
	omega = -1j * tau * freq
	zs = [a * cmath.exp(omega * t) for t, a in data.points()]
	window = Hannwindow(width, data.fsample)
	As = []
	for t in ts:
		offset = int(round(t * data.fsample)) - len(window) // 2
		A, _ = cmath.polar(convolve(zs, window, offset))
		As.append(A / (2 * width * data.fsample))
	return As

def Awindow(freq, data, t, width=DEFAULT_WIDTH):
	return Abytime(freq, data, [t], width)[0]

def freqAwindow(freq0, data, t, width=DEFAULT_WIDTH):
	window = Hannwindow(width, data.fsample)
	offset = int(round(t * data.fsample)) - len(window) // 2
	wdata = [data[j] * w if 0 <= j < len(data) else 0 for j, w in enumerate(window, offset)]
	wdata = TimeSeries(wdata, fsample=data.fsample)
	freq = fitfrequency(freq0, wdata)
	A, _ = Aphi(freq, wdata)
	A0, _ = Aphi(freq0, wdata)
	return freq, A, A0

def Aspectrum(freq, data, nmax=None):
	"""Amplitude spectrum, ie, amplitude at n freq for n = 1, 2, 3, ..."""
	if nmax is None:
		nmax = int(data.nyquist() / freq)
	spectrum = [Aphi(n * freq, data)[0] for n in range(1, nmax + 1)]
	return spectrum

if __name__ == "__main__":
	def isnear(x, y):
		return abs(math.log(x / y)) < 0.1
	fsample, n, freq = 3000, 3900, 88
	A0, phi0 = 0.78, 1.44
	ts = [k / fsample for k in range(n)]
	data = [A0 * math.cos(tau * freq * t + phi0) for t in ts]
	data = TimeSeries(data, fsample=fsample)
	A, phi = Aphi(freq, data)
	assert isnear(A, A0)
	assert isnear(phi, phi0)
	assert isnear(guessfundamental(data), freq)

	f, h = 123.45, 0.001
	A, dA = AdA(f, data)
	dA0 = (Aphi(f + h, data)[0] - Aphi(f - h, data)[0]) / (2 * h)
	assert isnear(dA, dA0)
	exit()


	print Abytime(freq, data)
	exit()

	fft = realfft(data)
	assert isnear(max(fft)[0], fsample / 2)
	for f, A in Aspectrum(data):
		print f, A

