#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## WORDS
## ---------------------------------------------------------------- ##
## A file that calculates the onset of experimental events (grouped
## by condition) in the Words study. Event onsets and durations are
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

CHOICE_ONSET = 0
CHOICE_RT    = 0
CHOICE_ACC   = 0
CHOICE_RESP  = 0
CONDITION    = 0
CHOICE1 = 0
CHOICE2 = 0

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
        self.choiceOnset = int(tokens[CHOICE_ONSET])
        self.choiceRt = int(tokens[CHOICE_RT])
        self.acc = int(tokens[CHOICE_ACC])
        self.resp = tokens[CHOICE_RESP]
        self.condition = tokens[CONDITION]
        self.choice1 = tokens[CHOICE1]   # Left option
        self.choice2 = tokens[CHOICE2]   # Right option

        # Now set up all the other values, based on the Choice values.

        self.primeOnset = self.choiceOnset - 4000
        self.primeRt = 2000
        
        self.blockBegin = 0

        ## Delete the following line if you want real RTs in
        ## the model
        self.choiceRt = 2000

        # Reset the durations of problems and choices 
        # that timed out 
        
        self.onsets = {'Prime'  : self.primeOnset,
                       'Choice' : self.choiceOnset,}

        self.rts = {'Prime'  : self.primeRt,
                    'Choice' : self.choiceRt,}

        # A dictionary to translate Chantel and Justin's stupid
        # names with more meaningful ones.
        CHOSEN_OPTIONS = {"MetRel" : "MetChosen",
                          "LitRel" : "LitChosen"}

        if self.condition == "MetLit":
            # Here we need to analyze the choice made
            self.acc = 1
            chosen = None
            if self.resp == "g":
                chosen = self.choice1
            elif self.resp == "y":
                chosen = self.choice2
            else:
                self.acc = 0
            
            if self.acc == 1:
                self.condition = CHOSEN_OPTIONS[chosen]
            print self.condition

        if self.choiceRt == 0:
            print("Non responded")
            self.Acc = 0
        
    def RelativeTime(self, val):
        "Time since the beginning of the block"
        return (float(val) - float(self.blockBegin))/1000.0
        
    def __str__(self):
        return "<Words:%d (%.2f)>" % (self.Condition, self.RelativeTime(self.sentenceOnset))

    def __repr__(self):
        return self.__str__()

def Parse(filename):
    """Parses a Table-format logfile"""
    global CHOICE_ONSET
    global CHOICE_RT   
    global CHOICE_ACC
    global CHOICE_RESP
    global CONDITION   
    global CHOICE1
    global CHOICE2

    fin      = open(filename, 'rU')
    subject  = filename.split('_')[0]
    lines    = fin.readlines()
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]
    
    CHOICE_ONSET = colNames.index("Choice1.OnsetTime")
    CHOICE_RT    = colNames.index("Choice1.RT")
    CHOICE_ACC   = colNames.index("Choice1.ACC")
    CHOICE_RESP  = colNames.index("Choice1.RESP")
    CONDITION    = colNames.index("Condition")    
    CHOICE1      = colNames.index("Choice1Type")
    CHOICE2      = colNames.index("Choice2Type")

    print(CHOICE_RESP)
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
            s.blockBegin = f.primeOnset - (OFFSET * TR)

    BLOCKS = set(t.block for t in trials)
    BLOCKS = list(BLOCKS)
    BLOCKS.sort()

    fout = open("s%s_sessions.m" % subject, 'w')

    I = 0 # Total of i counters

    for b in BLOCKS:
        subset  = [t for t in trials if t.block == b]

        print("Block %s, %d trials, %d errors" % (b, len (subset), len([x for x in subset if x.acc==0]))) 
        description = ""
                
        i = 1     # counter for cell entries in matlab file
        
        correct = [x for x in subset if x.acc == 1]
        errors = [x for x in subset if x.acc == 0]

        for condition in ['LowLit', 'HighLit', 'MetOnly', 'LitChosen', 'MetChosen']:
            for phase in ['Prime', 'Choice']:
                appropriate = [c for c in correct 
                               if c.condition == condition]
                if len(appropriate) > 0:
                    print "%s, %s, %d" % (condition, phase, len(appropriate))
                    description += "names{%d}='%s %s';\n" % (i, phase, condition) 
                    onsets = "%s" % [round(a.RelativeTime(a.onsets[phase]),0) for a in appropriate]
                    durations = "%s" % [a.rts[phase]/1000.0 for a in appropriate]
                    description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                    description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
                    i += 1
                else:
                    print("*** Attention here! *** No trials for condition %s, %s" % (phase, condition))
                        
        for phase in ['Prime', 'Choice']:
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
    
