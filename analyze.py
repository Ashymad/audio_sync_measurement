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
from multiprocessing import Pool
from itertools import zip_longest, islice

def chunkiter(data, chunk_size):
    for it in tqdm(range(0, data.shape[1] - chunk_size, chunk_size)):
        yield [data[0, it:(it+chunk_size)], data[1, it:(it+chunk_size)]]

matplotlib.use('tkagg')

fs = 1*(10**6)
chunk_size = fs//20
dt = 10**6/fs*np.arange(1-chunk_size, chunk_size)

shifts = deque()

def normalize(x):
    return (x - x.mean())/x.std()

def calc_shift(ch):
    return dt[correlate(normalize(ch[0]), normalize(ch[1])).argmax()]

with h5.File(sys.argv[1], "r") as f:
    data = f["data"]
    with Pool(6) as pool:
        for shift in pool.imap(calc_shift, chunkiter(data, chunk_size)):
            shifts.append(shift)

try:
    np.save("offest_{}.npy".format(sys.argv[1]), shifts)
    ppl.figure(0)
    sx = chunk_size*np.arange(0, len(shifts))/fs
    ppl.plot(sx, shifts)

    ppl.figure(1)
    ax = ppl.subplot()
    probscale.probplot(np.abs(shifts), ax=ax, plottype='pp',
                       problabel='Percentile', datalabel='Total Offset [us]',
                       scatter_kws=dict(marker='.', linestyle='none',
                                        label='Offset Amount'))

    ppl.show()
finally:
    embed()

