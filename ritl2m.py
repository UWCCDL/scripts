#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## RITL2M
## ---------------------------------------------------------------- ##
## A file that calculates the onset of experimental events (grouped
## by condition) in the INST study. Event onsets and durations are
## written to text files specific for each experimental block
## ('session' in SPM lingo)   


import sys, os
from operator import add
from math import sqrt

## ---------------------------------------------------------------- ##
## This is a list of imaging-related variables
## ---------------------------------------------------------------- ##

TR     = 2000.0
OFFSET = 2

DELAY1             = 0
DELAY2             = 0
BLOCK              = 0
TRIAL              = 0
PRACTICED          = 0
FIXATION_ONSET     = 0
ENCODING_ONSET     = 0
ENCODING_RT        = 0
EXECUTION_ONSET    = 0
EXECUTION_RT       = 0
PROBE_ONSET        = 0
PROBE_RT           = 0
PROBE_ACC          = 0

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
        except ValueError:
            print "ValueError: %s" % tokens
            self.ok = False
        except IndexError:
            print "IndexError: %s" % tokens
            self.ok = False

    def Create(self, tokens):
        """Performs the necessary initialization"""
        self.delay1 = int(tokens[DELAY1])
        self.delay2 = int(tokens[DELAY2])
        self.block = int(tokens[BLOCK])
        self.trial = int(tokens[TRIAL])
        self.practiced = tokens[PRACTICED]
        self.fixationOnset = int(tokens[FIXATION_ONSET])
        self.encodingOnset = int(tokens[ENCODING_ONSET])
        self.encodingRt = int(tokens[ENCODING_RT])
        self.executionOnset = int(tokens[EXECUTION_ONSET])
        self.executionRt = int(tokens[EXECUTION_RT])
        self.probeOnset = int(tokens[PROBE_ONSET])
        self.probeRt = int(tokens[PROBE_RT])
        self.probeAcc = int(tokens[PROBE_ACC])
        self.acc = int(tokens[PROBE_ACC])
        self.blockBegin = 0

        # In case of RTs that are 0s, one needs to apply
        # a correction. In particular, one needs to estimate
        # the correct duration of each phase.
        if self.encodingRt == 0:
            d = self.executionOnset - self.encodingOnset - self.delay1 - 2000
            #print "Trial %d, EncodingRT=0, estimated as %d" % (self.trial, d) 
            self.encodingRt = d

        if self.executionRt == 0:
            d = self.probeOnset - self.executionOnset - self.delay2 - 1000
            #print "Trial %d, ExecutionRT=0, estimated as %d, probe=%d, exec=%d, delay2=%d" % (self.trial, d, self.probeOnset, self.executionOnset, self.delay2) 
            self.executionRt = d

        # If, after the correction, we have negative RTs, that means
        # that we are dealing with aborted trials (in the newer version 
        # of the Eprime script). They need to be removed.
        
        if self.executionRt <= 0 or self.encodingRt <= 0:
            print "*** Excluding trial %d --- out of time ***" % self.trial
            # The current probe RT belongs to the previous trial, so it must
            # be overwritten.
            self.executionRt = -1 # Override (in case only Encoding was detected)
            self.probeRt     = -1 # Override
            self.probeAcc    =  0
            self.acc         =  0

        self.onsets = {'Encoding'  : self.encodingOnset,
                       'Execution' : self.executionOnset,
                       'Probe'     : self.probeOnset}

        self.rts = {'Encoding'  : self.encodingRt,
                    'Execution' : self.executionRt,
                    'Probe'     : self.probeRt}
        
    def RelativeTime(self, val):
        return (float(val) - float(self.blockBegin))/1000.0
        
    def __str__(self):
        return "<RITL:%d/%d (%.2f), P:%s>" % (self.block, self.trial, self.RelativeTime(self.encodingOnset), self.practiced)

    def __repr__(self):
        return self.__str__()



def Parse(filename):
    """Parses a Table-format logfile"""
    global DELAY1
    global DELAY2
    global BLOCK           
    global TRIAL           
    global PRACTICED       
    global FIXATION_ONSET
    global ENCODING_ONSET  
    global ENCODING_RT     
    global EXECUTION_ONSET 
    global EXECUTION_RT    
    global PROBE_ONSET     
    global PROBE_RT        
    global PROBE_ACC       

    fin      = open(filename, 'rU')
    subject  = filename.split('.')[0].split('-')[-1]
    lines    = fin.readlines()
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]

    DELAY1             = colNames.index("Delay1")
    DELAY2             = colNames.index("Delay2")
    BLOCK              = colNames.index("BlockNum")
    TRIAL              = colNames.index("Trials")
    PRACTICED          = colNames.index("Practiced")
    FIXATION_ONSET     = colNames.index("Fixation1.OnsetTime")
    ENCODING_ONSET     = colNames.index("Encoding.OnsetTime")
    ENCODING_RT        = colNames.index("Encoding.RT")
    EXECUTION_ONSET    = colNames.index("Execution.OnsetTime")
    EXECUTION_RT       = colNames.index("Execution.RT")
    PROBE_ONSET        = colNames.index("Probe.OnsetTime")
    PROBE_RT           = colNames.index("Probe.RT")
    PROBE_ACC          = colNames.index("Probe.ACC")

    trials = [Trial(r) for r in rows]
    trials = [t for t in trials if t.ok]   # Excludes trials where values are missing
    FIRST_TRIALS = []
    previous = None

    for t in trials:
        if previous == None or t.block != previous.block:
            FIRST_TRIALS.append(t)
        previous = t 
        
    #FIRST_TRIALS = [t for t in trials if (t.trial % 10) == 1]
    #print FIRST_TRIALS
    
    for f in FIRST_TRIALS:
        subset = [t for t in trials if t.block == f.block]
        for s in subset:
            s.blockBegin = f.fixationOnset - 4000

    #print [t.encodingOnset-t.blockBegin for t in trials]
    #print trials

    BLOCKS = set(t.block for t in trials)
    BLOCKS = list(BLOCKS)
    BLOCKS.sort()
    #print BLOCKS

    P = {'Yes' : 'Practiced', 'No' : 'Novel'}

    fout    = open("s%s_sessions.m" % subject, 'w')
    for b in BLOCKS:
        subset  = [t for t in trials if t.block == b]
        correct = [s for s in subset if s.acc == 1]
        errors  = [s for s in subset if s.acc == 0]

        nc = 5
        
        if len(errors) > 0:
            for phase in ['Encoding', 'Execution', 'Probe']:
                RTs = [e.rts[phase]/1000.0 for e in errors if e.rts[phase]>0]
                if len(RTs) > 0:
                    nc += 1
                

        i = 1     # counter

        fout.write("names=cell(1,%d);\n" % nc)
        fout.write("onsets=cell(1,%d);\n" % nc)
        fout.write("durations=cell(1,%d);\n" % nc)

        # Encoding and Execution, divided by Practice (Yes/No)
        # ------------------------------------------------------------
        for practice in ['Yes', 'No']:
            for phase in ['Encoding', 'Execution']: #, 'Probe']:
                appropriate = [c for c in correct if c.practiced == practice]
                fout.write("names{%d}='%s/%s';\n" % (i, phase, P[practice]))
                onsets = "%s" % [a.RelativeTime(a.onsets[phase]) for a in appropriate]
                durations = "%s" % [a.rts[phase]/1000.0 for a in appropriate]
                fout.write("onsets{%d}=%s;\n" % (i, onsets.replace(";", "")))
                fout.write("durations{%d}=%s;\n" % (i, durations.replace(";", "")))
                
                RTs =  [a.rts[phase]/1000.0 for a in appropriate]
                meanRT = reduce(add, RTs)/len(RTs)

                i += 1
                #print "<%d>, Practiced=%s, Phase=%s, RT=%.3f" % (b, practice, phase, meanRT)

        # Probes, altogether (assumes no effect of practice)
        # ------------------------------------------------------------
        fout.write("names{%d}='Probe';\n" % i)
        onsets = "%s" % [c.RelativeTime(c.onsets['Probe']) for c in correct]
        durations = "%s" % [c.rts['Probe']/1000.0 for c in correct]
        fout.write("onsets{%d}=%s;\n" % (i, onsets.replace(";", "")))
        fout.write("durations{%d}=%s;\n" % (i, durations.replace(";", "")))
        i += 1

        # Error trials
        # ------------------------------------------------------------
        # Note that, in the new design of the experiment, there might
        # be encoding errors only, or encoding/execution errors only,
        # because trials are aborted if one phase times out.
        if len(errors) > 0:
            for phase in ['Encoding', 'Execution', 'Probe']:
                O = [e.RelativeTime(e.onsets[phase]) for e in errors if e.onsets[phase]>0 and e.rts[phase]>0]
                D = [e.rts[phase]/1000.0 for e in errors if e.onsets[phase]>0 and e.rts[phase]>0]
                if len(D) > 0:
                    onsets = "%s" % O
                    durations = "%s" % D
                    fout.write("names{%d}='%s/Error';\n" % (i, phase))
                    fout.write("onsets{%d}=%s;\n" % (i, onsets.replace(";", "")))
                    fout.write("durations{%d}=%s;\n" % (i, durations.replace(";", "")))
                    i += 1

        fout.write("save('session%d.mat', 'names', 'onsets', 'durations');\n" % b)
        fout.flush()
    fout.close()



if __name__ == "__main__":
    filename=sys.argv[1]
    Parse(filename)
    
