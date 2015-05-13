import sys, math, os.path
import util
import numpy as np
import matplotlib.pyplot as plt

wfilename = sys.argv[1]
data = util.gettimeseries(wfilename)

ts = util.getts(data, width=0.25)
cents = list(range(-500, 4000, 100))
freqs = [util.tofreq(c) for c in cents]

print len(ts), len(freqs)

origin = 'lower'
#origin = 'upper'

delta = 0.025

X, Y = np.meshgrid(ts, freqs)
Z = X.copy()
for j, k in np.ndindex(X.shape):
	t, freq = X[j,k], Y[j,k]
	Z[j,k] = np.log(util.Awindow(freq, data, t, width=0.05))

nr, nc = Z.shape
X, Y = np.meshgrid(ts, cents)


# We are using automatic selection of contour levels;
# this is usually not such a good idea, because they don't
# occur on nice boundaries, but we do it here for purposes
# of illustration.
CS = plt.contourf(X, Y, Z, 10, # [-1, -0.1, 0, 0.1],
                        #alpha=0.5,
                        cmap=plt.cm.bone,
                        origin="lower")

plt.title(os.path.basename(wfilename))
plt.xlabel("time")
plt.ylabel("frequency (Hz)")

# Make a colorbar for the ContourSet returned by the contourf call.
cbar = plt.colorbar(CS)
cbar.ax.set_ylabel("Instantaneous amplitude")

plt.show()
