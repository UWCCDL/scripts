#!/usr/bin/env python
# ------------------------------------------------------------------ #
# GENERATE-CONTRASTS
# ------------------------------------------------------------------ #
# Uses Brianna's "inclusion matrix" to generate a sensible sets of 
# contrasts for the TaskSwitchingBlock experiment.
# ------------------------------------------------------------------ #

import numpy as np
import copy, sys

class Contrast():
    """
    A class representing an SPM contrast
    (name and vector)
    """
    def __init__(self, name, vector):
        self.name=name
        self.vector=vector

    def __str__(self):
        v = "%s" % self.vector
        s = ""
        for i in self.vector.reshape(1,self.vector.size)[0,:]:
            s += "%s " % i
        s = s[0:-1].replace(',', '')
        return "%s : %s" % (self.name, s)

    def __repr__(self):
        return self.__str__()


def parse_contrast(line, sep=":"):
    """
    Parses a line into a contrast
    """
    tokens   = line.split(sep)
    name     = tokens[0]
    contrast = tokens[1].split()
    vector   = [float(x) for x in contrast]
    vector   = np.array(vector)
    return Contrast(name, vector.reshape(1, vector.size))

def read_array(file):
    """
    Reads an array from a text file
    """
    f = open(file, 'r')
    L = f.readlines()
    L = [x for x in L if len(x.strip()) > 0]
    T = [x.split() for x in L]
    V = [[float(x) for x in y] for y in T]
    return np.array(V)

def create_global_contrast_vector(inc, vec):
    """
    Creates a Global Contrast Vector given an Inclusion Matrix
    and an ideal contrast vector for an ideal session.
    """
    # First, correct the Inclusion matrix U so that it fits
    # with 5 conditions (including fixation).
    U = inc   # The inclusion matrix
    V = vec   # The (ideal) contrast vector
    B = np.ones((4, 1))
    U = U.reshape(4, U.size/4)
    
    if U.shape == (4, 4):
        U = np.insert(U, 4, 1 ,1)

    # Pad the contrast with zeros
    if V.size < 5:
        for i in range(5 - V.size):
            V = np.insert(V, V.size, 0)
        V = V.reshape(1, V.size)

    # If the vector is still 5
    if V.size == 5:
        V = np.tile(V, 4)
    
    #print(V)
    #print(np.sum(V[V>0]))
    V = V/np.sum(V[V>0])   # Normalizes the contrast vector
    #print(V)
    V = V.reshape(4, V.size/4)

    # Create the proper contrast matrix
    #C = np.dot(B,V)
    C = V

    # Hadamard product matrix
    H = C*U

    h = H.flatten()
    p = np.array([x if x > 0 else 0 for x in h])
    m = np.array([x if x < 0 else 0 for x in h])
    p = p/float(sum(p))
    m = m/float(sum(m))
    return p - m

    # Calculating the column sum (scaling function)
    #S = np.sum(U/4, 0)
    #S = np.sum(V, 0)
    #S = np.sum(V[V>0])
    #print S
    #R = H/S   # Result matrix
    #return R.flatten()   # The Global Contrast Vector
 
def create_global_contrasts(cfile, ifile):
    fin = open(cfile, 'r')     # File containing the ideal contrasts
    inc = read_array(ifile)
    L = [x for x in fin.readlines() if len(x.strip()) > 0]
    C = [parse_contrast(x) for x in L]

    G = [Contrast(x.name, create_global_contrast_vector(inc, x.vector)) \
         for x in C]
    #fout = file(ofile, 'w')
    for g in G:
        print("%s" % g)
    
if __name__ == "__main__":
    create_global_contrasts(sys.argv[1], sys.argv[2])
