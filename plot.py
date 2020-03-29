#!/usr/bin/env python3
from matplotlib import pyplot as ppl
import numpy as np
from cycler import cycler
import probscale
from scipy import optimize
from scipy.constants import e
import tikzplotlib

files = ["./offset_netjack.h5.npy",
         "./offset_piwfs_tuned.h5.npy", "./offset_ravenna+jack.h5.npy",
         "./offset_snapcast.h5.npy"]

labels = ["NetJack2", "PiWFS", "RAVENNA", "Snapcast" ]

monochrome = (cycler('color', ['0.0', '0.7']) *
              cycler('linestyle', ['-.', '--', ':', '-']))
ax = ppl.subplot()
ax.set_prop_cycle(monochrome)


for ind, fl in enumerate(files):
    dat = np.abs(np.load(fl))
    perc, offs = probscale.plot_pos(dat)
    ppl.plot(perc[0:-1:100]*100, offs[0:-1:100])
ppl.xticks(range(0,110,10))
ppl.xlabel("Percentile")
ppl.ylabel(r"Offset [\si{\micro\second}]")
ppl.gca().spines['top'].set_visible(False)
ppl.gca().spines['right'].set_visible(False)
ppl.yscale('log')
ppl.ylim([1, 10**3])
ppl.grid(True, 'both', 'both')
ppl.legend(labels, loc="lower right")
tikzplotlib.save("offset.tex", axis_width='88mm')
