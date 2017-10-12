#!/usr/bin/env python

import scipy.io as io
import sys

HLP_MSG = """
Usage:

   count_art_regressors.py <art_file>

Where:
   
   *  <art_file> is one of the .mat files produced by the
      ART software, which contain various outliers.

The scripts prints out the number of outliers included in
the file.
"""

def count_outliers(artfile):
    """Counts the number of ourliers in an art file"""
    D = io.loadmat(artfile)
    return D["R"].shape[1]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(HLP_MSG)
    else:
        filename = sys.argv[1]
        print(count_outliers(filename))
