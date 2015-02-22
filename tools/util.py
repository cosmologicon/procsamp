from __future__ import division
import wave, numpy, os, math

REFERENCE_FREQ = 440  # frequency of the reference note in Hz
MIDDLE_C_DELTA = -9  # number of half-steps that middle C is from the reference frequency

def getwavedata(wfilename):
	"""Extract the waveform data from the given .wav file"""
	w = wave.open(wfilename)
	n = w.getnframes()
	framerate = w.getframerate()
	times = [i / framerate for i in range(n)]
	data = w.readframes(-1)
	data = [ord(data[2*i]) + ord(data[2*i+1]) * 256 for i in range(n)]
	data = [(x if x < 32768 else x - 65536) / 32768 for x in data]
	return data, framerate

def realfft(data, framerate):
	"""The real-valued Fourier transform of the given data."""
	ft0 = map(abs, numpy.fft.fft(data))
	n = len(data)
	freqs = [i * framerate / n for i in range(n // 2)]
	return list(zip(freqs, ft0[:n//2]))

def guessfundamental(data, framerate):
	"""Best guess at the fundamental frequency of the waveform."""
	fft = realfft(data, framerate)
	return max([(p, freq) for freq, p in fft])[1]

def tocents(freq):
	"""Number of cents relative to middle C."""
	return -100 * MIDDLE_C_DELTA + 1200 * math.log(freq / REFERENCE_FREQ) / math.log(2)

def tofreq(cents):
	return REFERENCE_FREQ * 2 ** ((cents + 100 * MIDDLE_C_DELTA) / 1200)

def nearestnote(freq):
	"""Frequency of nearest note (integer number of half-steps from 440Hz)."""
	return tofreq(round(tocents(freq), -2))

