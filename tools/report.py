# Generate a report of the given wave file

import sys
import util

wfilename = sys.argv[1]
data = util.gettimeseries(wfilename)

freq0 = util.getfundamental(data)
print freq0
print util.tocents(freq0)
print util.Aspectrum(freq0, data)


