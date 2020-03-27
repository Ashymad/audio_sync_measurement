#!/usr/bin/env python3

import h5py as h5
import numpy as np
from scipy.signal import correlate
from scipy.fft import rfft
from numpy.linalg import lstsq
from collections import deque
import matplotlib
from matplotlib import pyplot as ppl
import probscale
from IPython import embed
from thdn import thdn
import sys
from tqdm import tqdm

matplotlib.use('tkagg')

fs = 1*(10**6)
chunk_size = fs//20
dt = 10**6/fs*np.arange(1-chunk_size, chunk_size)
downsample = 100

freq = int(sys.argv[1])

shifts = deque()
thdns1 = deque()
thdns2 = deque()
ch1ds = deque()
ch2ds = deque()


def normalize(x):
    return (x - x.mean())/x.std()


with h5.File(sys.argv[2], "r") as f:
    data = f["data"]
    for ind in tqdm(np.arange(0, data.shape[1]-chunk_size, chunk_size)):
        #ch1ds.append(data[0, range(ind, ind+chunk_size, downsample)])
        #ch2ds.append(data[1, range(ind, ind+chunk_size, downsample)])
        ch1 = normalize(data[0, ind:(ind+chunk_size)])
        ch2 = normalize(data[1, ind:(ind+chunk_size)])
        #thdns1.append(thdn(ch1, freq, fs))
        #thdns2.append(thdn(ch2, freq, fs))

        xcorr = correlate(ch1, ch2)
        shift = dt[xcorr.argmax()]
        shifts.append(shift)

try:
    #ch1ds = np.concatenate(ch1ds)
    #ch2ds = np.concatenate(ch2ds)
    ppl.figure(0)
    sx = chunk_size*np.arange(0, len(shifts))/fs
    ppl.plot(sx, shifts)

    ppl.figure(1)
    ax = ppl.subplot()
    probscale.probplot(np.abs(shifts), ax=ax, plottype='pp',
                       problabel='Percentile', datalabel='Total Offset [us]',
                       scatter_kws=dict(marker='.', linestyle='none',
                                        label='Offset Amount'))

#    ppl.figure(2)
#    ax = ppl.subplot()
#    probscale.probplot(thdns1, ax=ax, plottype='pp',
#                       problabel='Percentile', datalabel='THD+N',
#                       scatter_kws=dict(marker='.', label='Channel 1'))
#    probscale.probplot(thdns2, ax=ax, plottype='pp',
#                       problabel='Percentile', datalabel='THD+N',
#                       scatter_kws=dict(marker='.', label='Channel 2'))
#
    ppl.show()
finally:
    embed()

