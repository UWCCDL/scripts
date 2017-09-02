#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## BAR2M
## ---------------------------------------------------------------- ##
## A file that calculates the onset of experimental events (grouped
## by condition) in the BAR study. Event onsets and durations are
## written to text files specific for each experimental block
## ('session' in SPM lingo)   


import sys, os
from operator import add
from math import sqrt

## ---------------------------------------------------------------- ##
## This is a list of contrasts vectors (calculated per session)
## ---------------------------------------------------------------- ##

## ---------------------------------------------------------------- ##
## This is a list of imaging-related variables
## ---------------------------------------------------------------- ##


TR     = 2000.0
OFFSET = 2

DELAY1               = 0
DELAY2               = 0
BLOCK                = 0
TRIAL                = 0
PROBLEM_ONSET       = 0
PROBLEM_RT          = 0
CHOICE_ONSET      = 0
CHOICE_RT         = 0
CHOICE_ACC   = 0
LOGIC = 0
RULES = 0
NUM_OF_RULES = 0
S_PROBLEM_ONSET       = 0
S_PROBLEM_RT          = 0
S_CHOICE_ONSET      = 0
S_CHOICE_RT         = 0
S_CHOICE_ACC   = 0
S_LOGIC = 0
S_RULES = 0
S_NUM_OF_RULES = 0

class Trial:
    """
    An abstract class representing a RITL trail---three phases
    (Encoding, Execution, Response), with associated Onsets and
    Durations (ie. RTs), followed by randomly-varying Delays.
    """
    def __init__(self, tokens):
        """Initializes and catches eventual errors"""
        self.ok = True
        try:
            self.Create(tokens)
            self.Initialize()
        except ValueError as v:
            sys.stderr.write("ValueError: %s\n" % (v))
            # A value error might be a sign of "Special" problems.
            try:
                self.CreateSpecial(tokens)
                self.Initialize()
            except ValueError as v:
                sys.stderr.write("ValueError: %s\n" % (v))
                self.ok = False

        except IndexError:
            sys.stderr.write("IndexError: %s\n" % tokens)
            self.ok = False
        
    def Initialize(self):
        """Sets the proper fields once the values have been read"""
        self.acc = self.choiceAcc
        self.blockBegin = 0

        # Reset the durations of problems and choices 
        # that timed out 
        
        if self.problemRt == 0:
            self.problemRt = 30000

        if self.choiceRt == 0:
            self.choiceRt = 4000

        self.onsets = {'Problem'  : self.problemOnset,
                       'Choice' : self.choiceOnset}

        self.rts = {'Problem'  : self.problemRt,
                    'Choice' : self.choiceRt}


    def Create(self, tokens):
        """Performs the necessary initialization"""
        
        self.delay1       = int(tokens[DELAY1])
        self.delay2       = int(tokens[DELAY2])
        self.block        = int(tokens[BLOCK])
        self.problemOnset = int(tokens[PROBLEM_ONSET])
        self.problemRt    = int(tokens[PROBLEM_RT])
        self.choiceOnset  = int(tokens[CHOICE_ONSET])
        self.choiceRt     = int(tokens[CHOICE_RT])
        self.choiceAcc    = int(tokens[CHOICE_ACC])

        self.logic        = tokens[LOGIC]
        self.rules        = tokens[RULES]
        self.numrules     = int(tokens[NUM_OF_RULES])

    def CreateSpecial(self, tokens):
        """Performs the necessary initialization"""
        self.block        = 2 # By default, the second block
        self.problemOnset = int(tokens[S_PROBLEM_ONSET])
        self.problemRt    = int(tokens[S_PROBLEM_RT])
        self.choiceOnset  = int(tokens[S_CHOICE_ONSET])
        self.choiceRt     = int(tokens[S_CHOICE_RT])
        self.choiceAcc    = int(tokens[S_CHOICE_ACC])

        self.logic        = tokens[S_LOGIC]
        self.rules        = tokens[S_RULES]
        self.numrules     = int(tokens[S_NUM_OF_RULES])
        
    def RelativeTime(self, val):
        "Time since the beginning of the block"
        return (float(val) - float(self.blockBegin))/1000.0
        
    def __str__(self):
        return "<BAR:%d/%d (%.2f), P:%s>" % (self.block, self.trial, self.RelativeTime(self.encodingOnset), self.practiced)

    def __repr__(self):
        return self.__str__()


def Parse(filename):
    """Parses a Table-format logfile"""
    global DELAY1
    global DELAY2
    global BLOCK           
    global TRIAL           
    global PROBLEM_ONSET
    global PROBLEM_RT   
    global CHOICE_ONSET 
    global CHOICE_RT    
    global CHOICE_ACC   
    global LOGIC
    global RULES
    global NUM_OF_RULES

    global S_PROBLEM_ONSET
    global S_PROBLEM_RT   
    global S_CHOICE_ONSET 
    global S_CHOICE_RT    
    global S_CHOICE_ACC   
    global S_LOGIC
    global S_RULES
    global S_NUM_OF_RULES


    fin      = open(filename, 'rU')
    subject  = filename.split('_')[1]
    lines    = fin.readlines()
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]
    
    DELAY1         = colNames.index("Delay1[Trial]")
    DELAY2         = colNames.index("Delay2[Trial]")
    BLOCK          = colNames.index("BlockNum")
    PROBLEM_ONSET  = colNames.index("Problem.OnsetTime[Trial]")
    PROBLEM_RT     = colNames.index("Problem.RT[Trial]")
    CHOICE_ONSET   = colNames.index("Choice.OnsetTime[Trial]")
    CHOICE_RT      = colNames.index("Choice.RT[Trial]")
    CHOICE_ACC     = colNames.index("Choice.ACC[Trial]")
    LOGIC          = colNames.index("Logic[Trial]")
    RULES          = colNames.index("Rules[Trial]")
    NUM_OF_RULES   = colNames.index("NumRules[Trial]")

    # Special marks for the "special" problem(#17)

    S_PROBLEM_ONSET  = colNames.index("Problem.OnsetTime[Block]")
    S_PROBLEM_RT     = colNames.index("Problem.RT[Block]")
    S_CHOICE_ONSET   = colNames.index("Choice.OnsetTime[Block]")
    S_CHOICE_RT      = colNames.index("Choice.RT[Block]")
    S_CHOICE_ACC     = colNames.index("Choice.ACC[Block]")
    S_LOGIC          = colNames.index("Logic[Block]")
    S_RULES          = colNames.index("Rules[Block]")
    S_NUM_OF_RULES   = colNames.index("NumRules[Block]")

    trials = [Trial(r) for r in rows]
    trials = [t for t in trials if t.ok]   # Excludes warmup trials 

    FIRST_TRIALS = []
    previous = None

    for t in trials:
        if previous == None or t.block != previous.block:
            FIRST_TRIALS.append(t)
        previous = t 
        
    for f in FIRST_TRIALS:
        subset = [t for t in trials if t.block == f.block]
        for s in subset:
            s.blockBegin = f.problemOnset - (OFFSET * TR)

    BLOCKS = set(t.block for t in trials)
    BLOCKS = list(BLOCKS)
    BLOCKS.sort()
    print BLOCKS

    P = {'Yes' : 'Practiced', 'No' : 'Novel'}

    
    fout = open("s%s_sessions.m" % subject, 'w')

    I = 0 # Total of i counters

    for b in BLOCKS:
        subset  = [t for t in trials if t.block == b]

        print("Block %s, errors %d" % (b, len([x for x in subset if x.acc==0]))) 
        description = ""
                
        i = 1     # counter for cell entries in matlab file
        j = 0     # counter for condition entries in contrast files

        for phase in ['Problem', 'Choice']:
            for logic in ['Non-Logic', 'Logic']:
                for rules in ['Low', 'High']:
                
                    appropriate = [c for c in subset 
                                   if c.logic == logic and
                                   c.rules == rules]
                    if len(appropriate) > 0:
                        description += "names{%d}='%s/%s/%s';\n" % (i, phase, rules, logic) 
                        onsets = "%s" % [round(a.RelativeTime(a.onsets[phase]),0) for a in appropriate]
                        durations = "%s" % [a.rts[phase]/1000.0 for a in appropriate]
                        description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                        description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
                        i += 1
                        #for c in CONTRAST_LIST:
                            #CV[c] += [len(appropriate)*CONTRAST_VECTORS[c][j]]
                            #CV[c] += [CONTRAST_VECTORS[c][j]]
                    # No matter what, the contrast counter needs to be updated
                    #j += 1


        I += i
        fout.write("names=cell(1,%d);\n" % (i-1))
        fout.write("onsets=cell(1,%d);\n" % (i-1))
        fout.write("durations=cell(1,%d);\n" % (i-1))
        fout.write(description)
        fout.write("save('session%d.mat', 'names', 'onsets', 'durations');\n" % b)
        fout.flush()
    fout.close()
    

if __name__ == "__main__":
    filename=sys.argv[1]
    Parse(filename)
    
