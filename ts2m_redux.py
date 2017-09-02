#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## TS2M.py
## ---------------------------------------------------------------- ##
## A file that calculates the onset of experimental events (grouped
## by condition) in the INST study. Event onsets and durations are
## written to text files specific for each experimental block
## ('session' in SPM lingo)   


import sys, os, random
from operator import add
from math import sqrt

## ---------------------------------------------------------------- ##
## This is a list of imaging-related variables
## ---------------------------------------------------------------- ##

TR     = 2000.0
OFFSET = 2

BLOCK_NUM          = 0
LANGUAGE_CONDITION = 0
TASK_CONDITION     = 0
STIMULUS_ONSET     = 0
STIMULUS_RT        = 0
STIMULUS_ACC       = 0

SELECTED_LRTR      = [32,  38,  44,  18,  23,  37,  8,   29,    # Block 1
                      85,  66,  87,  91,  77,  95,  79,  70,    # Block 2 
                      100, 113, 122, 110, 125, 143, 104, 141,   # Block 3
                      150, 156, 190, 163, 186, 169, 183, 167]   # Block 4

class Trial:
    def __init__(self, tokens):
        """Inits a trial from a tokenized Eprime row"""
        self.block             = int(tokens[BLOCK_NUM])
        self.languageCondition = tokens[LANGUAGE_CONDITION]
        self.taskCondition     = tokens[TASK_CONDITION]
        self.onset             = int(tokens[STIMULUS_ONSET])
        self.rt                = int(tokens[STIMULUS_RT])
        self.acc               = int(tokens[STIMULUS_ACC])
        self.trial             = int(tokens[TRIAL])
        self.blockBegin        = 0

    def RelativeTime(self):
        return (self.onset-self.blockBegin)/1000.0

    def __str__(self):
        return "<TS:%d (%d), L:%s, T:s>" % (self.block, self.trial, self.onset, self.languageCondition, self.taskCondition)

    def __repr__(self):
        return self.__str__()

def Parse(filename):
    """Parses an Eprime table file"""
    global BLOCK_NUM
    global LANGUAGE_CONDITION
    global TASK_CONDITION
    global STIMULUS_ONSET
    global STIMULUS_RT
    global STIMULUS_ACC
    global TRIAL

    fin       = open(filename, 'rU')
    lines    = fin.readlines()
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]
    print "Rows", len(rows)

    ## New let's read the proper column indexes from the file
    ## header line, and set the appropriate variables.
    
    BLOCK_NUM          = colNames.index('BlockNum')
    LANGUAGE_CONDITION = colNames.index('LanguageCondition')
    TASK_CONDITION     = colNames.index('TaskCondition')
    STIMULUS_ONSET     = colNames.index('StimPresentation.OnsetTime')
    STIMULUS_RT        = colNames.index('StimPresentation.RT')
    STIMULUS_ACC       = colNames.index('StimPresentation.ACC')
    TRIAL              = colNames.index('Stimuli.Sample')

    trials = [Trial(r) for r in rows] 
    FIRST_TRIALS = [t for t in trials if (t.trial % 49) == 1]
    
    for f in FIRST_TRIALS:
        subset = [t for t in trials if t.block == f.block]
        for s in subset:
            s.blockBegin = f.onset - 4000

    print [t.onset-t.blockBegin for t in trials]

    BLOCKS = set(t.block for t in trials)
    BLOCKS = list(BLOCKS)
    BLOCKS.sort()
    print BLOCKS

    for b in BLOCKS:
        fout    = open("redux_session%d.m" % b, 'w')
        subset  = [t for t in trials if t.block == b]
        correct = [s for s in subset if s.acc == 1]
        errors  = [s for s in subset if s.acc == 0]
        
        if subset[0] not in errors:
            errors = [subset[0]]+errors
        
        nc      = 4     # num of conditions
        i       = 1     # counter

        fout.write("names=cell(1,%d);\n" % nc)
        fout.write("onsets=cell(1,%d);\n" % nc)
        fout.write("durations=cell(1,%d);\n" % nc)

        for lc in ['Repetition', 'Switch']:
            for tc in ['Repetition', 'Switch']:
                appropriate = [c for c in correct if c.languageCondition == lc and c.taskCondition == tc]
                
                # Selects only 1/3 of the Rep/Rep trials to balance the numbers
                if lc == 'Repetition' and tc == 'Repetition':
                    
                    #subset = random.sample(appropriate, 8)
                    subset = [x for x in appropriate if x.trial in SELECTED_LRTR]
                    others = [x for x in appropriate if x not in subset]
                    errors+=others
                    appropriate=subset
                    
                fout.write("names{%d}='Language%s/Task%s';\n" % (i, lc, tc))
                onsets = "%s;\n" % [a.RelativeTime() for a in appropriate]
                durations = "%s;\n" % [a.rt/1000.0 for a in appropriate]
                fout.write("onsets{%d}=%s" % (i, onsets.replace(";", "")))
                fout.write("durations{%d}=%s" % (i, durations.replace(";", "")))
                
                i += 1
        
        if len(errors) > 0:
            fout.write("names{%d}='Errors';\n" % i)
            onsets = "%s;\n" % [e.RelativeTime() for e in errors]
            durations = "%s;\n" % [e.rt/1000.0 for e in errors]
            fout.write("onsets{%d}=%s" % (i, onsets.replace(";", "")))
            fout.write("durations{%d}=%s" % (i, durations.replace(";", "")))
        
        fout.write("save('redux_session%d.mat', 'names', 'onsets', 'durations')\n" % b)
        fout.flush()
        fout.close()


if __name__ == "__main__":
    Parse(sys.argv[1])
