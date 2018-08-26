#!/usr/bin/env python

import nilearn
from nilearn import plotting
from matplotlib.pyplot import cm
from numpy import linspace
import sys

vois = {}
for filename in sys.argv[1:]:
    
    # Opens file and extract MNI coordinates
    # ----------------------------------------------------------
    
    f = open(filename, "r")
    tokens = [line.split() for line in f.readlines()[1:]]
    coords = [x[2:5] for x in tokens]
    mni = [[float(y) for y in x] for x in coords]
    name = tokens[0][1]
    vois[name] = mni

    
#cols = cm.tab10(linspace(0,1,len(vois.keys())))
cols = cm.rainbow(linspace(0,1,len(vois.keys())))

# Adds transparency
# ----------------------------------------------------------

for c in cols:
    c[3] = 0.7  # Sets alpha


# Plots and saves
# ----------------------------------------------------------

display=plotting.plot_glass_brain(None)
for i, v in enumerate(vois.keys()):
    display.add_markers(vois[v], marker_color=cols[i], marker_size=10, marker="o")

display.savefig("vois.png", dpi=300)
display.close()
