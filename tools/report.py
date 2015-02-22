# Generate a report of the given wave file

import sys
import util

wfilename = sys.argv[1]
data, framerate = util.getwavedata(wfilename)

print util.nearestnote(util.guessfundamental(data, framerate))

