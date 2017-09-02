#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## DESK2M
## ---------------------------------------------------------------- ##
## A file that calculates the onset of experimental events (grouped
## by condition) in the DESK study. Event onsets and durations are
## written to text files specific for each experimental block
## ('session' in SPM lingo)   


import sys, os
from operator import add
from math import sqrt
from numpy import mean, std

## ---------------------------------------------------------------- ##
## This is a list of imaging-related variables
## ---------------------------------------------------------------- ##

TR     = 2000.0   # The study's TR
OFFSET = 1        # The number of scans that separate the beginnig
                  # Of a Session from the first recorded event. 

## ---------------------------------------------------------------- ##
## This is a list of imaging-related variables
## ---------------------------------------------------------------- ##

BLOCK = 0
TRIAL = 0
CONDITION = 0
STIMULUS_ONSET = 0
STIMULUS_RT = 0
STIMULUS_ACC = 0
INCONGRUENT_INSTRUCTIONS_ONSET = 0
CONGRUENT_INSTRUCTIONS_ONSET = 0
DONE = 0

class Block:
    """
    A blocks is a collection of trials
    """
    def __init__(self, trials):
        self.trials = trials
        self.CheckConsistency()

    def CheckConsistency(self):
        """Makes sure a block contains homogeneous stimuli"""
        onsets = list(set(x.instructionsOnset for x in self.trials))
        conditions = list(set(x.condition for x in self.trials))
        done = list(set(x.done for x in self.trials))

        if len(onsets) != 1 or len(conditions) != 1 or len(done) != 1:
            raise ValueError("Inconsistent block")
        else:
            self.onset = onsets[0]
            self.condition = conditions[0]
            self.done = done[0]
        
    def AbsoluteOnset(self):
        """
        The block begins with the instructions 
        """
        return self.onset

    def RelativeOnset(self):
        return ( self.AbsoluteOnset() - self.trials[0].begin ) / 1000.0

    def Condition(self):
        return self.condition

    def Duration(self):
        return (self.done - self.AbsoluteOnset() ) / 1000.0

    def MeanRT(self):
        return mean([x.stimulusRt for x in self.trials if x.stimulusAcc == 1])

    def Accuracy(self):
        return mean([x.stimulusAcc for x in self.trials])
    
    def __str__(self):
        return "<DeSK Block: %s, N=%d, %s>" % (self.Condition(),
                                               len(self.trials),
                                               self.Duration())

    def __repr__(self):
        return self.__str__()

class Trial:
    """
    An abstract class representing a Simon Task 
    """
    def __init__(self, tokens):
        """Initializes and catches eventual errors"""
        try:
            self.Create(tokens)
            self.Initialize()
            self.ok = True
        except ValueError as v:
            sys.stderr.write("ValueError: %s; Skipping\n" % (v))
            self.ok = False

        
    def Initialize(self):
        """Sets the proper fields once the values have been read"""
        pass
        

    def Create(self, tokens):
        """Performs the necessary initialization"""
        global BEGIN
        self.block        = int(tokens[BLOCK])
        #print self.block
        self.trial        = int(tokens[TRIAL])
        #print self.trial
        self.stimulusOnset = int(tokens[STIMULUS_ONSET])
        #print self.stimulusOnset
        self.stimulusRt    = int(tokens[STIMULUS_RT])
        self.stimulusAcc   = int(tokens[STIMULUS_ACC])
        self.condition     = tokens[CONDITION]
        self.done          = int(tokens[DONE])
        
        self.instructionsBegin = 0
        if self.condition == "Congruent":
            self.instructionsOnset = int(tokens[CONGRUENT_INSTRUCTIONS_ONSET])
        elif self.condition == "Incongruent":
            self.instructionsOnset = int(tokens[INCONGRUENT_INSTRUCTIONS_ONSET])
        


    def RelativeTime(self, val):
        "Time since the beginning of the block"
        return (float(val) - float(self.begin))/1000.0
        
    def __str__(self):
        return "<DeSK:%d/%d (%.2f), %s>" % (self.block, self.trial, self.RelativeTime(self.stimulusOnset), self.condition)

    def __repr__(self):
        return self.__str__()

def set_variables(colNames):
    """
    Identifies the colums corresponding to specific variables in a list
    of column names
    """
    global BLOCK
    global TRIAL
    global CONDITION
    global STIMULUS_ONSET
    global STIMULUS_RT
    global STIMULUS_ACC
    global INCONGRUENT_INSTRUCTIONS_ONSET
    global CONGRUENT_INSTRUCTIONS_ONSET
    global DONE

    try:
        BLOCK  = colNames.index("Block")
    except ValueError as e:
        sys.stderr.write("Cannot find 'Block' info. Aborting\n")
        sys.exit(0)

    try:
        TRIAL  = colNames.index("Trial")
    except ValueError as e:
        sys.stderr.write("Cannot find 'Trial' info. Aborting\n")
        sys.exit(0)

    try:
        CONDITION  = colNames.index("Procedure[Block]")
    except ValueError as e:
        sys.stderr.write("Cannot find 'Procedure' info. Aborting\n")
        sys.exit(0)

    try:
        STIMULUS_ONSET  = colNames.index("Stimulus.OnsetTime[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Stimulus.OnsetTime' info at 'Trial' level\n")
        STIMULUS_ONSET  = colNames.index("Stimulus.OnsetTime")
        
    try:
        STIMULUS_RT     = colNames.index("Stimulus.RT[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Stimulus.RT' info at 'Trial' level\n")
        STIMULUS_RT     = colNames.index("Stimulus.RT")

    try:
        STIMULUS_ACC     = colNames.index("Stimulus.ACC[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Stimulus.ACC' info at 'Trial' level\n")
        STIMULUS_ACC     = colNames.index("Stimulus.ACC")        
    
    try:
        CONGRUENT_INSTRUCTIONS_ONSET = \
          colNames.index("CongruentInstructions.OnsetTime[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'CongruentINstructions.OnsetTime' info at 'Trial' level\n")
        CONGRUENT_INSTRUCTIONS_ONSET = colNames.index("CongruentInstructions.OnsetTime")

    try:
        INCONGRUENT_INSTRUCTIONS_ONSET = \
          colNames.index("IncongruentInstructions.OnsetTime[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'IncongruentINstructions.OnsetTime' info at 'Trial' level\n")
        INCONGRUENT_INSTRUCTIONS_ONSET = colNames.index("IncongruentInstructions.OnsetTime")

    try:
        DONE = colNames.index("Done.OnsetTime[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Done.OnsetTime' info at 'Trial' level\n")
        DONE = colNames.index("Done.OnsetTime")


def parse_file(filename):
    """Parses a Table-format logfile"""
    fin      = open(filename, 'rU')
    lines    = fin.readlines()
    fin.close()
    
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]

    
    set_variables( colNames )
     
    # Transforming rows into trials and returning them
    
    trials = [Trial(r) for r in rows]
    trials = [t for t in trials if t.ok]   # Excludes warmup trials

    return trials


def process_trials(trials):
    """
    Processes the trials read by parse_file
    """
    for t in trials:
        t.begin = trials[0].instructionsOnset - (OFFSET * TR)

    # Grouping trials based on blocks

    currentBlockTrials = []
    blocks = []
    #print trials
    for t in trials:
        if len( currentBlockTrials ) == 0 \
            or t.block == currentBlockTrials[ -1 ].block:
            currentBlockTrials.append(t)
        else:
            blocks.append( Block( currentBlockTrials ))
            currentBlockTrials = [t]
    # The last set of trials
    if len(currentBlockTrials) > 0:
        blocks.append( Block( currentBlockTrials ))

    create_matlab_file( blocks )
    create_stats_file( blocks )

    
def create_matlab_file( blocks, filename="sessions.m" ):
    """
    Analyzes the blocks and creates a Matlab session file for SPM
    """
    # Now create the files.
    fout = open(filename, 'w')

    # List all the conditions

    fout.write("names=cell(1,2);\n")
    fout.write("onsets=cell(1,2);\n")
    fout.write("durations=cell(1,2);\n")
    
    i = 0   # Cell index counter

    for condition in ['Congruent', 'Incongruent']:
        i += 1
        appropriate = [b for b in blocks if b.condition == condition ]

        onsets = "%s" % [round(a.RelativeOnset()) for a in appropriate]
        durations = "%s" % [a.Duration() for a in appropriate]
        fout.write("names{%d} = '%s';\n" % (i, condition))
        fout.write("onsets{%d} = %s;\n" % (i, onsets))
        fout.write("durations{%d} = %s;\n" % (i, durations))
        
    fout.write("save('session1.mat', 'names', 'onsets', 'durations');\n")
    fout.flush()
    fout.close()

    
def create_stats_file( blocks, filename="behavioral_results.txt"):
    """
    Analyzes the blocks and reports the stats
    """
    fout = open(filename, 'w')
    fout.write("Block\tMean_RT\tAccuracy\n")
    j = 0

    for b in blocks:
        j += 1
        fout.write("%d\t%s\t%0.3f\t%0.3f\n" % ( j, b.Condition(), b.MeanRT(), b.Accuracy() ))

    for condition in ['Congruent', 'Incongruent']:
        subset = [b for b in blocks if b.condition == condition ]
        mean_rt = mean( [s.MeanRT() for s in subset] )
        mean_acc = mean( [s.Accuracy() for s in subset] )
        fout.write("%s\t%s\t%0.3f\t%0.3f\n" % ( "Overall", condition, mean_rt, mean_acc))

    fout.flush()
    fout.close()

if __name__ == "__main__":
    filename=sys.argv[1]
    process_trials( parse_file( filename ) )
    
