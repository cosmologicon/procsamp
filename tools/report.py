# Generate a report of the given wave file

import sys, math
import util

wfilename = sys.argv[1]
data = util.gettimeseries(wfilename)

#print util.guessfundamental(data)
freq0 = util.getfundamental(data)
#print freq0, util.tocents(freq0)
freq = 4 * freq0
freq = util.fitfrequency(freq, data)
#print freq, util.tocents(freq)
#print nfreq, util.tocents(nfreq)
for t in util.getts(data, width=0.05):
	f, A, A0 = util.freqAwindow(freq, data, t)
	print t, f, util.tocents(f), A, A0
exit()

freqs = [freq * math.exp(d) for d in (-0.05,-0.03,-0.01,0,0.01,0.03,0.05)]
for freq in freqs:
	print freq, util.Aphi(freq, data), util.AdA(freq, data)
exit()
for As in zip(*[util.Abytime(f, data, width=0.05) for f in freqs]):
#for As in zip(*[util.Abytime(freq0*n, data, width=0.05) for n in (1,2,3,4,5,6,7,8)]):
	print " ".join(map(str, As))


