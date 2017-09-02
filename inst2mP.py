#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## INST2M3c
## ---------------------------------------------------------------- ##
## A file that calculates the onset of experimental events (grouped
## by condition) in the INST study. Event onsets and durations are
## written to text files specific for each experimental block
## ('session' in SPM lingo)   
## ---------------------------------------------------------------- ##
## History
##
## 2010-11-29 : * Added the extra opposite conjunction (IN + XN >
##            :   2XP).
##
## 2010-09-27 : * Added the extra 'conjunction' contrast (XN >
##            :   IN+XP).
##
## 2010-06-05 : * Excluded the 'Complexty' variable from regressors. 
##
## 2010-05-19 : * Pulled error and outlier trials in a single group
##            : * Fixed a bug on numbering regressors.
##
## 2010-05-16 : * Created a single M-file for all sessions (makes it
##            :   easier to automatically create the session-
##            :   specific .mat files)
##            : * Added calculation of time outliers for encoding
##            :   and execution (T > Mean + 3*SD).
##
## 2010-05-16 : * Added all conditions to contrasts
##
## 2010-01-16 : * Added error trials to the block .m file.
##
## ---------------------------------------------------------------- ##

import sys, os
from operator import add
from math import sqrt

## ---------------------------------------------------------------- ##
## This is a list of imaging-related variables
## ---------------------------------------------------------------- ##

TR     = 2000.0
OFFSET = 2

## ---------------------------------------------------------------- ##
## These are variable that correspond to column indexes in the 
## table file. Trial objects need to access them to find the proper
## slot in a list of information tokens.
## The variables are initialized when initially parsing the eprime 
## file.
## ---------------------------------------------------------------- ## 

FIXATION1_START = 0
FIXATION2_START = 0
COMPLEXITY      = 0
PRACTICED       = 0
ENCODING_START  = 0
ENCODING_RT     = 0
EXECUTION_START = 0
EXECUTION_RT    = 0
PROBE_START     = 0
PROBE_ACC       = 0
PROBE_RT        = 0
BLOCK           = 0
FIXATIONS       = []

## ---------------------------------------------------------------- ##
## Finally, we have some more variables that will be used in the
## script
## ---------------------------------------------------------------- ##

CONDS           = {'NIL':'-', 'T':'+', 'HIGH':'+', 'LOW':'-'}
BLOCKS          = []

CONTRAST_LIST   = ('Enc P+', 'Enc P-', 'Exe P+', 'Exe P-',
                   'Probe', 'Enc', 'Exe', 'P+', 'P-',
                   'Enc > Exe', 'Exe > Enc', 'P+ > P-', 'P- > P+',
                   'P- > P+ | Enc', 'P+ > P- | Enc', 
                   'P- > P+ | Exe', 'P+ > P- | Exe', 
                   'Enc > Exe | P-', 'Enc > Exe | P+',
                   'Exe > Enc | P-', 'Exe > Enc | P+',
                   'd(Exe P+)', 'd(Exe P-)', 'd(Enc P+)', 'd(Enc P-)',
                   'Exe > Enc | P- > P-', '2XN > IN+XP', 'IN+XN > 2XP'
                   )

CONTRASTS       = {
    'Enc P+' : [1, 0, 0, 0, 0],
    'Enc P-' : [0, 1, 0, 0, 0],
    'Exe P+' : [0, 0, 1, 0, 0],
    'Exe P-' : [0, 0, 0, 1, 0],
    'Probe'  : [0, 0, 0, 0, 1],
    
    'Enc' : [0.5, 0.5, 0, 0, 0],
    'Exe' : [0, 0, 0.5, 0.5, 0],

    'P+'  : [0.5, 0, 0.5, 0, 0],
    'P-'  : [0, 0.5, 0, 0.5, 0],
    
    'Enc > Exe' : [0.5, 0.5, -0.5, -0.5, 0],
    'Exe > Enc' : [-0.5, -0.5, 0.5, 0.5, 0],
    
    'P+ > P-'   : [0.5, -0.5, 0.5, -0.5, 0],
    'P- > P+'   : [-0.5, 0.5, -0.5, 0.5, 0],
    
    'P- > P+ | Enc' : [-1, 1, 0, 0, 0],
    'P+ > P- | Enc' : [1, -1, 0, 0, 0],
    'P- > P+ | Exe' : [0, 0, -1, 1, 0],
    'P+ > P- | Exe' : [0, 0, 1, -1, 0],
    
    'Enc > Exe | P-' : [0, 1, 0, -1, 0],
    'Enc > Exe | P+' : [1, 0, -1, 0, 0],
    'Exe > Enc | P-' : [0, -1, 0, 1, 0],
    'Exe > Enc | P+' : [-1, 0, 1, 0, 0],
    
    'd(Enc P+)' : [1, -0.3333, -0.3333, -0.3333, 0],
    'd(Enc P-)' : [-0.3333, 1, -0.3333, -0.3333, 0],
    'd(Exe P+)' : [-0.3333, -0.3333, 1, -0.3333, 0],
    'd(Exe P-)' : [-0.3333, -0.3333, -0.3333, 1, 0],

    'Exe > Enc | P- > P-' : [0.5, -0.5, -0.5, 0.5, 0],
    '2XN > IN+XP' : [0, -0.5, -0.5, 1, 0],
    'IN+XN > 2XP' : [0, 0.5, -1, 0.5, 0],
}


def mean(vals):
    """Calculates the mean of a set of values"""
    return float(reduce(add, vals))/float(len(vals))

def ss(vals):
    """Calculates the sum of squares"""
    return reduce(add, [x*x for x in vals])

def var(vals):
    """Returns the variance of a list of values"""
    m = mean(vals)
    d = [x - m for x in vals]
    return ss(d)/float(len(d)-1)

def sd(vals):
    """Returns the St Dev of a list of values"""
    return sqrt(var(vals))


## ---------------------------------------------------------------- ##
## TRIAL
## ---------------------------------------------------------------- ##
## An experimental trial is made of three different phases:
##
##  (a) Problem encoding ("instructions")
##  (b) Problem execution
##  (c) Probe presentation, response, and feedback.
##
## ---------------------------------------------------------------- ##
## Here is a visual representation of a trial:
##
## |  +  |    Fixation #1 (pre-encoding)
## +-----+
## |ACxDy|    Problem encoding ("Instructions") self-paced
## +-----+
## | ... |    Within-trial 1st Jitter, need to separate events.
## |     |    Random duration of 2, 4, or 6s + sync to next scan 
## +-----+
## |  *  |    Fixation #2 (pre-execution)
## +-----+
## |#3##2|    Input numbers. Self-paced
## +-----+
## | ... |    Within-trial 2nd jitter, needed to separate events.
## |     |    2, 4, or 6s + sync to next scan
## +-----+ 
## | 20? |    Probe (Y/N response). 2s
## +-----+
## | FB  |    Feedback, 2s
## +-----+
## | ... |    Between-trials jitter
##
## ---------------------------------------------------------------- ##
##
## Each block is preceded by 4s of 'get ready' timer.  
##

class Trial:
    def __init__(self, tokens):
        try:
            self.Block       = int(tokens[BLOCK])
            self.Complexity  = CONDS[tokens[COMPLEXITY]]
            self.Practiced   = CONDS[tokens[PRACTICED]]
            self.Fixation1   = int(tokens[FIXATION1_START])
            self.Fixation2   = int(tokens[FIXATION2_START])
            self.Encoding    = int(tokens[ENCODING_START])
            self.EncodingRT  = int(tokens[ENCODING_RT])
            self.Execution   = int(tokens[EXECUTION_START])
            self.ExecutionRT = int(tokens[EXECUTION_RT])
            self.Probe       = int(tokens[PROBE_START])
            self.ProbeRT     = int(tokens[PROBE_RT])
            self.ProbeACC    = int(tokens[PROBE_ACC])
            self.Offset      = FIXATIONS[self.Block-1] - 4000

        except Exception, e:
            print e
            print "Error: %s" % tokens
            sys.exit()

    def AbsoluteTime(self, time):
        """Returns the absolute time (in ms) since the experiment began"""
        return time - (FIXATIONS[0] - 4000)

    def RelativeTime(self, time):
        """Returns the absolute time from the beginning of the current block"""
        #print time - self.Offset
        return time - self.Offset

    def RelativeScan(self, time):
        """Returns the scan index from the beginning of the block"""
        return round(self.RelativeTime(time)/TR) 

    def AbsoluteScan(self, time):
        """Returns the scan index from the beginning of the experiment"""
        if (self.Block == 1):
            return self.RelativeScan(time)
        else:
            B = self.Block-1
            return self.RelativeScan(time) + reduce(add, BLOCKS[0:B])


def ReadBlocks(filename):
    """Reads the lengths of an experiment blocks from a file"""
    global BLOCKS
    f = open(filename, 'r')
    lines = f.readlines()
    BLOCKS = [int(x) for x in lines]

def Parse(filename):
    """Parses an experiment 'table' file""" 

    # Declare global variables to access them

    global FIXATION1_START 
    global FIXATION2_START 
    global COMPLEXITY      
    global PRACTICED       
    global ENCODING_START  
    global ENCODING_RT     
    global EXECUTION_START 
    global EXECUTION_RT    
    global PROBE_START     
    global PROBE_ACC
    global PROBE_RT
    global BLOCK           
    global FIXATIONS
    global BLOCK
    
    #ReadBlocks(filename[0:3]+".blocks.txt")

    ## Read the file lines. The first contains the column names.
    
    f        = open(filename, 'r')
    lines    = f.readlines()
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]
    print "Tokens", len(rows)
    ## New let's read the proper column indexes from the file
    ## header line, and set the appropriate variables.
    
    FIXATION1_START = colNames.index('Fixation1.OnsetTime')
    FIXATION2_START = colNames.index('Fixation2.OnsetTime')
    COMPLEXITY      = colNames.index('Complexity')
    PRACTICED       = colNames.index('Practiced')
    ENCODING_START  = colNames.index('TaskEncoding.OnsetTime')
    ENCODING_RT     = colNames.index('TaskEncoding.RT')
    EXECUTION_START = colNames.index('TaskExecution.OnsetTime')
    EXECUTION_RT    = colNames.index('TaskExecution.RT')
    PROBE_START     = colNames.index('Probe.OnsetTime')
    PROBE_ACC       = colNames.index('Probe.ACC')
    PROBE_RT        = colNames.index('Probe.RT')
    TRIAL           = colNames.index('Trial')
    BLOCK           = colNames.index('Block')
    
    # Identifies the first trials of each block. This is needed to
    # estimate the beginning of each block--A block begings 4s before
    # the fixation.  The block's beginning will be recorded as each
    # trial as the 'offset' time (see Trial object)
    
    firstTrials    = [x for x in rows if int(x[TRIAL]) == 1]
    FIXATIONS      = [int(x[FIXATION1_START]) for x in firstTrials]

    trials         = [Trial(x) for x in rows]

    # get an estimate of the M + 3*SD times for Encoding and Execution

    encodings      = [x.EncodingRT for x in trials if x.ProbeACC == 1]
    executions     = [x.ExecutionRT for x in trials if x.ProbeACC == 1]

    ENCODING_UPPER = mean(encodings)+3*sd(encodings)
    EXECUTION_UPPER= mean(executions)+3*sd(executions)

    print ENCODING_UPPER, EXECUTION_UPPER

    # Create the 'observations' file. This will keep track
    # of the number of correct trials in each block.

    obs            = open(filename[0:3] + ".obs.txt", 'w')

    ## Creates the 'contrast' file. The contrast file contains the
    ## betas for all the conditions of interest.

    cfile           = open(filename[0:3] + ".contrasts.txt", "w") 

    contrasts      = {}
    for x in CONTRAST_LIST:
        contrasts[x] = []

    #mfile  = open(filename[0:3] + "sessions.m", 'w')
    pfile  = open(filename[0:3] + "params.txt", 'w')

    ## All the sessions have exactly 4 blocks of 20 trials each.
    ## Note that what is called a 'block' here is "session" in
    ## SPM and a "run" in AfNI.

    for block in range(1,len(FIXATIONS)+1):
        ##mfile  = open(filename[0:3] + "session%d.m" % block, 'w')
        conds    = open(filename[0:3] + ".session%d.conds.txt" % block, 'w')
        correct  = [x for x in trials if x.Block == block and x.ProbeACC==1]
        errors   = [x for x in trials if x.Block == block and x.ProbeACC==0]
        subset   = [x for x in correct if x.EncodingRT < ENCODING_UPPER
                    and x.ExecutionRT < EXECUTION_UPPER]
        outliers = [x for x in correct if x.EncodingRT >= ENCODING_UPPER
                    or x.ExecutionRT >= EXECUTION_UPPER]
        discard  = errors+outliers
        
        print "Block %d: Errors %d, Outliers %d" % (block, len(errors), len(outliers))
        ## Initializes the cells in the .mat file

        NUM_ROWS = 5
        if len(discard) != 0:
            NUM_ROWS = 8

        tonsets=[]
        tdurations=[]
        ponsets=[]
        pdurations=[]
        parameters=[]
        for trial in subset:
            tonsets.append(round(trial.RelativeTime(trial.Encoding)/1000.0, 1))
            tonsets.append(round(trial.RelativeTime(trial.Execution)/1000.0, 1))
            tdurations.append(round(float(trial.EncodingRT)/1000.0, 1))
            tdurations.append(round(float(trial.ExecutionRT)/1000.0, 1))
            ponsets.append(round(trial.RelativeTime(trial.Probe)/1000.0, 1))
            pdurations.append(round(float(trial.ProbeRT)/1000.0, 1))
            parameters.append(1)
            if trial.Practiced == '-':
                parameters.append(2)
            else:
                parameters.append(1)

        pfile.write("SESSION %d\n" % block)
        z="%s" % tonsets
        pfile.write("TONSETS: %s\n" % z.replace(",", " "))
        z="%s" % tdurations
        pfile.write("TDURATIONS: %s\n" % z.replace(",", " "))
        z="%s" % parameters
        pfile.write("TPARAMS: %s\n" % z.replace(",", " "))
        z="%s" % ponsets
        pfile.write("PONSETS: %s\n" % z.replace(",", " "))
        z="%s" % pdurations
        pfile.write("PDURATIONS: %s\n\n" % z.replace(",", " "))
        pfile.flush()
        
       
    pfile.close()

if __name__ == '__main__':
    filename = sys.argv[1]
    print filename
    Parse(filename)
