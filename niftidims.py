#!/usr/bin/env python

import nibabel as nib
import sys
import os.path

def report( fname ):
    img = nib.load(fname)
    head = img.get_header()
    dims = head.get_data_shape()
    result = ""
    for dim in dims[:-1]:
        result += "%d " % dim
    result += "%d" % dims[-1]
    return result

if __name__ == """__main__""":
    if len(sys.argv) > 1:
        for fname in sys.argv[1:]:
            if os.path.isfile(fname):
                print(report(fname))
            else:
                print("")
    else:
        print("Usage: niftidims.py <file1> <file2> ... <fileN>")
        
