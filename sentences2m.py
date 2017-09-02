#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## SENTENCES2M
## ---------------------------------------------------------------- ##
## A file that calculates the onset of experimental events (grouped
## by condition) in the Discourse study. Event onsets and durations are
## written to text files specific for each experimental block
## ('session' in SPM lingo)   


import sys, os
from operator import add
from math import sqrt

## ---------------------------------------------------------------- ##
## This is a list of imaging-related variables
## ---------------------------------------------------------------- ##


TR     = 1000.0
OFFSET = 0

COMP_ONSET = 0
COMP_ACC   = 0
COMP_RT    = 0
CONDITION  = 0
TRIAL      = 0

class Trial:
    """
    An abstract class representing a sentence trial---two phases
    (Sentence and Comprehension probe), with associated Onsets and
    Durations (ie. RTs), followed by delays.
    """
    def __init__(self, tokens):
        """Initializes and catches eventual errors"""
        self.ok = True
        try:
            self.Create(tokens)
        except ValueError:
            print "ValueError: %s" % tokens
            self.ok = False
        except IndexError:
            print "IndexError: %s" % tokens
            self.ok = False

    def Create(self, tokens):
        """Performs the necessary initialization"""
        self.block = 1
        self.compOnset = int(tokens[COMP_ONSET])
        self.compRt = int(tokens[COMP_RT])
        self.acc = int(tokens[COMP_ACC])
        self.condition = tokens[CONDITION]
        
        # Now set up all the other values, based on the Probe values.

        self.sentenceOnset = self.compOnset - 13000
        self.sentenceRt = 7000
        
        # Shortcut for accuracy
        self.blockBegin = 0

        # Reset the durations of problems and choices 
        # that timed out 
        
        if self.compRt == 0:
            self.compRt = 5000

        self.onsets = {'Sentence'  : self.sentenceOnset,
                       'Comprehension' : self.compOnset,}

        self.rts = {'Sentence'  : self.sentenceRt,
                    'Comprehension' : self.compRt,}
        
    def RelativeTime(self, val):
        "Time since the beginning of the block"
        return (float(val) - float(self.blockBegin))/1000.0
        
    def __str__(self):
        return "<Sentences:%d (%.2f), P:%s>" % (self.block, self.RelativeTime(self.sentenceOnset), self.condition)

    def __repr__(self):
        return self.__str__()



def Parse(filename):
    """Parses a Table-format logfile"""
    global COMP_ONSET
    global COMP_RT   
    global COMP_ACC  
    global CONDITION   

    fin      = open(filename, 'rU')
    subject  = filename.split('_')[0]
    lines    = fin.readlines()
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]
    
    COMP_ONSET = colNames.index("Comp.OnsetTime")
    COMP_RT    = colNames.index("Comp.RT")
    COMP_ACC   = colNames.index("Comp.ACC")
    CONDITION    = colNames.index("Condition")    

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
            s.blockBegin = f.sentenceOnset - (OFFSET * TR)

    BLOCKS = set(t.block for t in trials)
    BLOCKS = list(BLOCKS)
    BLOCKS.sort()

    P = {'Yes' : 'Practiced', 'No' : 'Novel'}

    fout = open("s%s_sessions.m" % subject, 'w')

    I = 0 # Total of i counters

    for b in BLOCKS:
        subset  = [t for t in trials if t.block == b]

        print("Block %s, %d trials, %d errors" % (b, len (subset), len([x for x in subset if x.acc==0]))) 
        description = ""
                
        i = 1     # counter for cell entries in matlab file
        
        correct = [x for x in subset if x.acc == 1]
        errors = [x for x in subset if x.acc == 0]

        for phase in ['Sentence', 'Comprehension']:
            for condition in ['Active', 'Object']:
                appropriate = [c for c in correct 
                               if c.condition == condition]
                if len(appropriate) > 0:
                        description += "names{%d}='%s %s';\n" % (i, phase, condition) 
                        onsets = "%s" % [round(a.RelativeTime(a.onsets[phase]),0) for a in appropriate]
                        durations = "%s" % [a.rts[phase]/1000.0 for a in appropriate]
                        description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                        description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
                        i += 1
                        
        for phase in ['Sentence', 'Comprehension']:
            if len(errors) > 0:
                description += "names{%d}='%s (Error)';\n" % (i, phase) 
                onsets = "%s" % [round(e.RelativeTime(e.onsets[phase]),0) for e in errors]
                durations = "%s" % [e.rts[phase]/1000.0 for e in errors]
                description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
                i += 1

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
    
