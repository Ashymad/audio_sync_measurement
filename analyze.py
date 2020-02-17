#!/usr/bin/python3

import h5py as h5
import numpy as np
from scipy.signal import correlate
from scipy.fft import rfft
from numpy.linalg import lstsq
from collections import deque
from matplotlib import pyplot as ppl

fs = 1*(10**6)
chunk_size = fs//10
dt = 10**6/fs*np.arange(1-chunk_size, chunk_size)

shifts = deque()


def normalize(x):
    return (x - x.mean())/x.std()


with h5.File("./rec_weigh+moving_med.h5", "r") as f:
    data = f["data"]
    for ind in np.arange(0, data.shape[1]-chunk_size, chunk_size):
        ch1 = normalize(data[0, ind:(ind+chunk_size)])
        ch2 = normalize(data[1, ind:(ind+chunk_size)])

        xcorr = correlate(ch1, ch2)
        shift = dt[xcorr.argmax()]
        shifts.append(shift)
        print("Reading: {:.2f}%   ".format(100*ind/(data.shape[1]-chunk_size)),
              end='\r')

print('')

sx = np.arange(0, len(shifts))
m, c = lstsq(np.vstack([sx, np.ones(len(sx))]).T, shifts, rcond=None)[0]
ppl.plot(sx, shifts)
ppl.plot(sx, m*sx + c)
ppl.show()

f = fs/chunk_size*np.arange(0, len(shifts)/2)/len(shifts)

ppl.plot(f, np.abs(rfft(shifts)))
ppl.show()

