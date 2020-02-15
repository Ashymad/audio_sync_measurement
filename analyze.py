#!/usr/bin/python3

import h5py as h5
import numpy as np
from scipy.signal import correlate
from collections import deque
from matplotlib import pyplot as ppl

fs = 1*(10**6)
chunk_size = fs//10
dt = 10**6/fs*np.arange(1-chunk_size, chunk_size)

shifts = deque()


def normalize(x):
    return (x - x.mean())/x.std()


with h5.File("rec.h5", "r") as f:
    data = f["data"]
    for ind in np.arange(0, data.shape[1]-chunk_size, chunk_size):
        ch1 = normalize(data[0, ind:(ind+chunk_size)])
        ch2 = normalize(data[1, ind:(ind+chunk_size)])

        xcorr = correlate(ch1, ch2)
        shift = dt[xcorr.argmax()]
        shifts.append(shift)

ppl.plot(shifts)
ppl.show()

