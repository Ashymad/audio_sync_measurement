#!/usr/bin/env python3
from matplotlib import pyplot as ppl
import numpy as np
from cycler import cycler
import probscale

files = ["./offset_netjack.h5.npy", "./offset_piwfs.h5.npy",
         "./offset_piwfs_tuned.h5.npy", "./offset_ravenna+jack.h5.npy",
         "./offset_snapcast.h5.npy"]

labels = ["NetJack2", "PiWFS", "PiWFS (tuned)", "RAVENNA", "Snapcast"]

monochrome = (cycler('color', ['0.0', '0.3', '0.5', '0.6', '0.85']) +
              cycler('marker', ['.', 'o', 'x', '+', 's']))
ax = ppl.subplot()
ax.set_prop_cycle(monochrome)

for ind, fl in enumerate(files):
    dat = np.abs(np.load(fl))
    perc, offs = probscale.plot_pos(dat)
    ppl.plot(perc*100, offs, lw=0)
ppl.xticks(range(0,110,10))
ppl.xlabel("Percentile")
ppl.ylabel("Offset [us]")
ppl.gca().spines['top'].set_visible(False)
ppl.gca().spines['right'].set_visible(False)
ppl.yscale('log')
ppl.grid(True, 'both', 'both')
ppl.legend(labels)
ppl.show()
