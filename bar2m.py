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

LC_BLOCK = 0
LC_PROBLEM_ONSET       = 0
LC_PROBLEM_RT          = 0
LC_CHOICE_ONSET      = 0
LC_CHOICE_RT         = 0
LC_CHOICE_ACC   = 0
LC_LOGIC = 0
LC_RULES = 0
LC_NUM_OF_RULES = 0


class Trial:
    """
    An abstract class representing a RITL trail---three phases
    (Encoding, Execution, Response), with associated Onsets and
    Durations (ie. RTs), followed by randomly-varying Delays.
    """
    def __init__(self, tokens):
        """Initializes and catches eventual errors"""
        self.ok = True
        self.trial = -1
        try:
            self.Create(tokens)
            self.Initialize()
        except ValueError as v:
            sys.stderr.write("ValueError: %s; Trying Special Case\n" % (v))
            # A value error might be a sign of "Special" problems.
            try:
                self.CreateSpecial(tokens)
                self.Initialize()
            except ValueError as v:
                sys.stderr.write("ValueError: %s; Trying Last Chance\n" % (v))
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
        """Performs the necessary initialization for the Special Problem"""
        self.block        = -1 # By default, the second block
        self.problemOnset = int(tokens[S_PROBLEM_ONSET])
        self.problemRt    = int(tokens[S_PROBLEM_RT])
        self.choiceOnset  = int(tokens[S_CHOICE_ONSET])
        self.choiceRt     = int(tokens[S_CHOICE_RT])
        self.choiceAcc    = int(tokens[S_CHOICE_ACC])

        self.logic        = tokens[S_LOGIC]
        self.rules        = tokens[S_RULES]
        self.numrules     = int(tokens[S_NUM_OF_RULES])


    def CreateLastChance(self, tokens):
        """
Performs initialization when the data table is corrupted.
""" 
        self.block        = int(tokens[LC_BLOCK])
        self.problemOnset = int(tokens[LC_PROBLEM_ONSET])
        self.problemRt    = int(tokens[LC_PROBLEM_RT])
        self.choiceOnset  = int(tokens[LC_CHOICE_ONSET])
        self.choiceRt     = int(tokens[LC_CHOICE_RT])
        self.choiceAcc    = int(tokens[LC_CHOICE_ACC])

        self.logic        = tokens[LC_LOGIC]
        self.rules        = tokens[LC_RULES]
        self.numrules     = int(tokens[LC_NUM_OF_RULES])


    def RelativeTime(self, val):
        "Time since the beginning of the block"
        return (float(val) - float(self.blockBegin))/1000.0
        
    def __str__(self):
        return "<BAR:%d/%d (%.2f), L:%s, R:%d>" % (self.block, self.trial, self.RelativeTime(self.problemOnset), self.logic, self.numrules)

    def __repr__(self):
        return self.__str__()


def Parse(filename):
    """Parses a Table-format logfile"""
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

    global LC_BLOCK
    global LC_PROBLEM_ONSET
    global LC_PROBLEM_RT   
    global LC_CHOICE_ONSET 
    global LC_CHOICE_RT    
    global LC_CHOICE_ACC   
    global LC_LOGIC
    global LC_RULES
    global LC_NUM_OF_RULES

    fin      = open(filename, 'rU')
    subject  = filename.split('-')[1]
    lines    = fin.readlines()
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]
    
    # --- Block info
    try:
        BLOCK          = colNames.index("BlockNum")
        #TRIAL          = colNames.index("Trial")
    except ValueError as e:
        sys.stderr.write("Cannot find 'Block' info. Aborting\n")
        sys.exit(0)
        
    # --- Problem onset
    try:
        PROBLEM_ONSET  = colNames.index("Problem.OnsetTime[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Problem.OnsetTime' info at 'Trial' level\n")
        PROBLEM_ONSET  = colNames.index("Problem.OnsetTime")
        
    # --- Problem RT
    try:
        PROBLEM_RT     = colNames.index("Problem.RT[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Problem.RT' info at 'Trial' level\n")
        PROBLEM_RT     = colNames.index("Problem.RT")

    # --- Choice Onset
    try:
        CHOICE_ONSET   = colNames.index("Choice.OnsetTime[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Choice.Onset' info at 'Trial' level\n")
        CHOICE_ONSET   = colNames.index("Choice.OnsetTime")

    # --- Choice RT

    try:
        CHOICE_RT      = colNames.index("Choice.RT[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Choice.RT' info at 'Trial' level\n")
        CHOICE_RT      = colNames.index("Choice.RT")

    # --- Choice Accuracy

    try:
        CHOICE_ACC     = colNames.index("Choice.ACC[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Choice.ACC' info at 'Trial' level\n")
        CHOICE_ACC     = colNames.index("Choice.ACC")        
    
    # --- Logic
        
    try:
        LOGIC          = colNames.index("Logic[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Logic' info at 'Trial' level\n")
        LOGIC          = colNames.index("Logic")

    # --- Rules
    try:
        RULES          = colNames.index("Rules[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Rules' info at 'Trial' level\n")
        RULES          = colNames.index("Rules")
    
    # --- NumRules
    try:
        NUM_OF_RULES   = colNames.index("NumRules[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'NumRules' info at 'Trial' level\n")
        NUM_OF_RULES   = colNames.index("NumRules")

    try:
        # Special marks for the "special" problem(#17)
        S_PROBLEM_ONSET  = colNames.index("Problem.OnsetTime[Block]")
        S_PROBLEM_RT     = colNames.index("Problem.RT[Block]")
        S_CHOICE_ONSET   = colNames.index("Choice.OnsetTime[Block]")
        S_CHOICE_RT      = colNames.index("Choice.RT[Block]")
        S_CHOICE_ACC     = colNames.index("Choice.ACC[Block]")
        S_LOGIC          = colNames.index("Logic[Block]")
        S_RULES          = colNames.index("Rules[Block]")
        S_NUM_OF_RULES   = colNames.index("NumRules[Block]")

    except ValueError as e:
        sys.stderr.write("Cannot find Special Problem, skipping...\n")

    trials = [Trial(r) for r in rows]
    trials = [t for t in trials if t.ok]   # Excludes warmup trials 

    FIRST_TRIALS = []
    previous = None

    # Now we need to add the "Special" problem at the end of the
    
    block_max = max(set([t.block for t in trials]))
    for i in [t for t in trials if t.block == -1]:
        i.block = block_max

    for t in trials:
        if previous == None or t.block != previous.block:
            FIRST_TRIALS.append(t)
        previous = t 

    print len(trials)
        
    for f in FIRST_TRIALS:
        subset = [t for t in trials if t.block == f.block]
        for s in subset:
            print f, s.problemOnset, f.problemOnset
            s.blockBegin = f.problemOnset - (OFFSET * TR)

    BLOCKS = set(t.block for t in trials)
    BLOCKS = list(BLOCKS)
    BLOCKS.sort()
    
    print(FIRST_TRIALS)
    print FIRST_TRIALS[1].problemOnset
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
    
