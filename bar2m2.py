#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## BAR2M2
## ---------------------------------------------------------------- ##
## Calculates the onset of experimental events (grouped
## by condition) in the BAR study. Event onsets and durations are
## written to text files specific for each experimental block
## ('session' in SPM lingo). Differently than in bar2m.py, this 
## also outputs a simplified version of the Eprime text file, and
## calculates problems durations based on median times.
## ---------------------------------------------------------------- ##

import sys, os
from operator import add
from math import sqrt
from numpy import median, mean

## ---------------------------------------------------------------- ##
## This is a list of imaging-related variables
## ---------------------------------------------------------------- ##

TR     = 2000.0
OFFSET = 2

BLOCK          = 0
TRIAL          = 0
PROBLEM_ONSET  = 0
PROBLEM_RT     = 0
CHOICE_ONSET   = 0
CHOICE_RT      = 0
CHOICE_ACC     = 0
LOGIC          = 0
RULES          = 0
NUM_OF_RULES   = 0

# A different set of variables for the "Special" problem,
# which is recorded at the "Block" level (instead of "Trial"
# level).

S_PROBLEM_ONSET = 0
S_PROBLEM_RT    = 0
S_CHOICE_ONSET  = 0
S_CHOICE_RT     = 0
S_CHOICE_ACC    = 0
S_LOGIC         = 0
S_RULES         = 0
S_NUM_OF_RULES  = 0


class Trial:
    """
    An abstract class representing a RITL trail---three phases
    (Encoding, Execution, Response), with associated Onsets and
    Durations (ie. RTs), followed by randomly-varying Delays.
    """
    def __init__(self, tokens, subject=None):
        """Initializes and catches eventual errors"""
        self.ok = True
        self.subject = subject
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

    def AsRow(self):
        format_string = "%s\t%d\t%d\t%s\t%s\t%d\t%d\t%d"
        return format_string % (self.subject, self.block, self.numrules, 
                                self.rules, self.logic, 
                                self.problemRt, self.choiceRt, 
                                self.choiceAcc)


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

    fin      = open(filename, 'rU')
    subject  = filename.split('-')[1]
    lines    = fin.readlines()
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]
    
    # --- Block info ----------------------------------------------- #
    try:
        BLOCK          = colNames.index("BlockNum")
    except ValueError as e:
        sys.stderr.write("Cannot find 'Block' info. Aborting\n")
        sys.exit(0)
        
    # --- Problem onset -------------------------------------------- #
    try:
        PROBLEM_ONSET  = colNames.index("Problem.OnsetTime[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Problem.OnsetTime' info at 'Trial' level\n")
        PROBLEM_ONSET  = colNames.index("Problem.OnsetTime")
        
    # --- Problem RT ----------------------------------------------- #
    try:
        PROBLEM_RT     = colNames.index("Problem.RT[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Problem.RT' info at 'Trial' level\n")
        PROBLEM_RT     = colNames.index("Problem.RT")

    # --- Choice Onset --------------------------------------------- #
    try:
        CHOICE_ONSET   = colNames.index("Choice.OnsetTime[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Choice.Onset' info at 'Trial' level\n")
        CHOICE_ONSET   = colNames.index("Choice.OnsetTime")

    # --- Choice RT ------------------------------------------------ #

    try:
        CHOICE_RT      = colNames.index("Choice.RT[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Choice.RT' info at 'Trial' level\n")
        CHOICE_RT      = colNames.index("Choice.RT")

    # --- Choice Accuracy ------------------------------------------ #

    try:
        CHOICE_ACC     = colNames.index("Choice.ACC[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Choice.ACC' info at 'Trial' level\n")
        CHOICE_ACC     = colNames.index("Choice.ACC")        
    
    # --- Logic ---------------------------------------------------- #
        
    try:
        LOGIC          = colNames.index("Logic[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Logic' info at 'Trial' level\n")
        LOGIC          = colNames.index("Logic")

    # --- Rules ---------------------------------------------------- #
    try:
        RULES          = colNames.index("Rules[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'Rules' info at 'Trial' level\n")
        RULES          = colNames.index("Rules")
    
    # --- NumRules ------------------------------------------------- #
    try:
        NUM_OF_RULES   = colNames.index("NumRules[Trial]")
    except ValueError as e:
        sys.stderr.write("Could not find 'NumRules' info at 'Trial' level\n")
        NUM_OF_RULES   = colNames.index("NumRules")

    # --- Attempts to identify the fields for the Special XOR problem #

    try:
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

    trials = [Trial(r, subject=subject) for r in rows]
    trials = [t for t in trials if t.ok]   # Excludes warmup trials 

    # Preprocess trials and saves data
    behav_file = file("%s_behavioral_data.txt" % subject, "w")
    behav_file.write("Subject\tBlock\tNumRules\tRules\tLogic\tProblem\tChoice\tAccuracy\n")
    for t in trials:
        behav_file.write(t.AsRow() + "\n")
    behav_file.close()

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
    
    fout = open("s%s_sessions_mean_rt.m" % subject, 'w')
    
    I = 0 # Total of i counters

    for b in BLOCKS:
        subset  = [t for t in trials if t.block == b]

        print("Block %s, errors %d" % (b, len([x for x in subset if x.acc==0]))) 
        description = ""
                
        i = 1     # counter for cell entries in matlab file
        j = 0     # counter for condition entries in contrast files

        # Calculate the mean RT for problems
        mean_rt_problems = mean([t.problemRt for t in trials])

        for phase in ['Problem', 'Choice']:
            for logic in ['Non-Logic', 'Logic']:
                for rules in ['Low', 'High']:
                    appropriate = [c for c in subset 
                                   if c.logic == logic and
                                   c.rules == rules]
                    if len(appropriate) > 0:
                        description += "names{%d}='%s/%s/%s';\n" % (i, phase, rules, logic) 
                        onsets = "%s" % [round(a.RelativeTime(a.onsets[phase]),0) for a in appropriate]
                        if phase == "Problem":
                            durations = "[%s]" % (mean_rt_problems/1000.0)
                        else:
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
    
