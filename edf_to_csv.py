"""
This module is for converting EDF files to CSV files. Before use,
change the path where all the edf files are stored.

usage: python edf_to_csv.py 
"""

import pyedflib
import numpy as np
from os import listdir


def all_edf_files(path):
    """
    Return a list of files with edf suffix under path

    :param path: the path to find all edf files
    :return: a list of all edf files under path
    """
    return [i for i in listdir(path) if i.endswith('.edf')]


def convert_edf_to_txt(path):
    """
    Convert one edf file to a csv file

    :param path: the edf file path
    :return: none - create a csv file with the same name as edf file
    """
    print "start converting " + path
    # get edf reader
    f = pyedflib.EdfReader(path)
    # get signals in the file
    n = f.signals_in_file
    # get labels: channels from BrainAmp
    labels = f.getSignalLabels()
    # create data dict
    data_dict = dict()
    sigbufs = np.zeros((n, f.getNSamples()[0]))
    for i in np.arange(n):
        sigbufs[i, :] = f.readSignal(i)
        data_dict[str(labels[i])] = sigbufs[i]
    # create new txt file
    ff = open(path[:-4] + '.csv', 'w')
    # write header
    ff.write(','.join(data_dict.keys()) + '\n')
    # write data
    data_lst = zip(*[data_dict[i] for i in data_dict.keys()])
    for i in data_lst:
        data = [str(d) for d in i]
        ff.write(','.join(data) + '\n')
    ff.close()
    print "done"

if __name__ == '__main__':
  # Change this to the path you store all edf files
  file_path = "."
  for edf_file in all_edf_files(file_path):
      convert_edf_to_txt(edf_file)
