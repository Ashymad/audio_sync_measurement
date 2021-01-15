#!/usr/bin/env python3

import h5py as h5
import numpy as np
import matplotlib.pyplot as ppl
from cycler import cycler
from scipy import signal
import mplcursors

fs = 1e9/(300*16)

def normalize(x):
    return (x - x.mean())/x.std()

with h5.File("out.h5", "r") as f:
    data = f["dset"]
    filtf = 20e3/fs
    b, a = signal.butter(5, filtf)
    y = np.zeros((len(data), 16));
    for ch in range(0, 16):
        y[:, ch] = (normalize(signal.filtfilt(b, a, data[:,ch])))
    dt = 300*16*(10**(-9))
    t = np.arange(0, dt*(len(data)), dt);
    cm = ppl.get_cmap('gist_rainbow')
    fig = ppl.figure()
    ax = fig.add_subplot(111)
    custom_cycler = (cycler(color=[cm(1.*i/8) for i in range(8)]) *
                     cycler(linestyle=['-', '--']))

    ax.set_prop_cycle(custom_cycler)
    ppl.xlabel("Czas [s]")
    ppl.ylabel("Amplituda [V]")
    ppl.plot(t, y)
    ppl.legend(["{}".format(chan) for chan in range(16)], loc="lower center", ncol=8);
    mplcursors.cursor()
    ppl.show()

