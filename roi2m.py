#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## ROI2M
## ---------------------------------------------------------------- ##
## A file that calculates the onset of experimental events (grouped
## by condition) in the INST study. Event onsets and durations are
## written to text files specific for each experimental block
## ('session' in SPM lingo)   


import sys, os
from operator import add
from math import sqrt

## ---------------------------------------------------------------- ##
## This is a list of contrasts vectors (calculated per session)
## ---------------------------------------------------------------- ##


CONTRAST_LIST = [
    'ReIP', 'ReXP', 'ReIN', 'ReXN', 'ReR', 
    'RoIP', 'RoXP', 'RoIN', 'RoXN', 'RoR',
             
    # Factor 1
    'Re > Ro', 'Ro > Re', 
    
    # Factor 2
    'I > X', 'X > I',

    # Factor 3
    'P > N', 'N > P', 

    # Factor 1 * Factor 2
    'ReI > RoI', 'RoI > ReI', 'ReX > RoX', 'RoX > ReX',
    'ReR > RoR', 'RoR > ReR',
             
    # Factor 2 * Factor 3 
    'IP > XP', 'XP > IP', 'IN > XN', 'XN > IN',
    
    # Factor 1 * Factor 3
    'ReP > ReN', 'ReN > ReP', 'RoP > RoN', 'RoN > RoP',

    # Factor 1 * Factor 2 * Factor 3
    'ReIP > RoIP', 'RoIP > ReIP', 'ReXP > RoXP', 'RoXP > ReXP',
    'ReIN > RoIN', 'RoIN > ReIN', 'ReXN > RoXN', 'RoXN > ReXN',
    'ReIP > ReXP', 'ReXP > ReIP', 'ReIN > ReXN', 'ReXN > ReIN',
    'RoIP > RoXP', 'RoXP > RoIP', 'RoIN > RoXN', 'RoXN > RoIN',
    'ReIP > ReIN', 'ReIN > ReIP', 'ReXP > ReXN', 'ReXN > ReXP',
    'RoIP > RoIN', 'RoIN > RoIP', 'RoXP > RoXN', 'RoXN > RoXP',
    ]



CONTRAST_VECTORS = {
    # Order: ReIP ReXP ReIN ReXN ReR RoIP RoXP RoIN RoXN RoR
    'ReIP' : [1, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
    'ReXP' : [0, 1, 0, 0, 0, 0, 0, 0, 0, 0], 
    'ReIN' : [0, 0, 1, 0, 0, 0, 0, 0, 0, 0], 
    'ReXN' : [0, 0, 0, 1, 0, 0, 0, 0, 0, 0], 
    'ReR'  : [0, 0, 0, 0, 1, 0, 0, 0, 0, 0], 
    'RoIP' : [0, 0, 0, 0, 0, 1, 0, 0, 0, 0], 
    'RoXP' : [0, 0, 0, 0, 0, 0, 1, 0, 0, 0], 
    'RoIN' : [0, 0, 0, 0, 0, 0, 0, 1, 0, 0], 
    'RoXN' : [0, 0, 0, 0, 0, 0, 0, 0, 1, 0], 
    'RoR'  : [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
             
    # Factor 1
    'Re > Ro' : [1, 1, 1, 1, 1, -1, -1, -1, -1, -1], 
    'Ro > Re' : [-1, -1, -1, -1, -1, 1, 1, 1, 1, 1], 
    
    # Factor 2
    'I > X' : [1, -1, 1, -1, 0, 1, -1, 1, -1, 0],
    'X > I' : [-1, 1, -1, 1, 0, -1, 1, -1, 1, 0],

    # Factor 3
    'P > N'  : [1, 1, -1, -1, 0, 1, 1, -1, -1, 0], 
    'N > P'  : [-1, -1, 1, 1, 0, -1, -1, 1, 1, 0], 

    # Factor 1, * Factor 2
    'ReI > RoI'  : [1, 0, 1, 0, 0, -1, 0, -1, 0, 0], 
    'RoI > ReI'  : [-1, 0, -1, 0, 0, 1, 0, 1, 0, 0], 
    'ReX > RoX'  : [0, 1, 0, 1, 0, 0, -1, 0, -1, 0], 
    'RoX > ReX'  : [0, -1, 0, -1, 0, 0, 1, 0, 1, 0],
    'ReR > RoR'  : [0, 0, 0, 0, 1, 0, 0, 0, 0, -1], 
    'RoR > ReR'  : [0, 0, 0, 0, -1, 0, 0, 0, 0, 1],
             
    # Factor 2 * Factor 3 
    'IP > XP' : [1, -1, 0, 0, 0, 1, -1, 0, 0, 0], 
    'XP > IP' : [-1, 1, 0, 0, 0, -1, 1, 0, 0, 0], 
    'IN > XN' : [0, 0, 1, -1, 0, 0, 0, 1, -1, 0], 
    'XN > IN' : [0, 0, -1, 1, 0, 0, 0, -1, 1, 0],
    
    # Factor 1, * Factor 3
    'ReP > ReN' : [1, 1, -1, -1, 0, 0, 0, 0, 0, 0], 
    'ReN > ReP' : [-1, -1, 1, 1, 0, 0, 0, 0, 0, 0], 
    'RoP > RoN' : [0, 0, 0, 0, 0, 1, 1, -1, -1, 0], 
    'RoN > RoP' : [0, 0, 0, 0, 0, -1, -1, 1, 1, 0],

    # Factor 1, * Factor 2 * Factor 3
    'ReIP > RoIP' : [1, 0, 0, 0, 0, -1, 0, 0, 0, 0], 
    'RoIP > ReIP' : [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0], 
    'ReXP > RoXP' : [0, 1, 0, 0, 0, 0, -1, 0, 0, 0], 
    'RoXP > ReXP' : [0, -1, 0, 0, 0, 0, 1, 0, 0, 0],
    'ReIN > RoIN' : [0, 0, 1, 0, 0, 0, 0, -1, 0, 0], 
    'RoIN > ReIN' : [0, 0, -1, 0, 0, 0, 0, 1, 0, 0], 
    'ReXN > RoXN' : [0, 0, 0, 1, 0, 0, 0, 0, -1, 0], 
    'RoXN > ReXN' : [0, 0, 0, -1, 0, 0, 0, 0, 1, 0],
    'ReIP > ReXP' : [1, -1, 0, 0, 0, 0, 0, 0, 0, 0], 
    'ReXP > ReIP' : [-1, 1, 0, 0, 0, 0, 0, 0, 0, 0], 
    'ReIN > ReXN' : [0, 0, 1, -1, 0, 0, 0, 0, 0, 0], 
    'ReXN > ReIN' : [0, 0, -1, 1, 0, 0, 0, 0, 0, 0],
    'RoIP > RoXP' : [0, 0, 0, 0, 0, 1, -1, 0, 0, 0], 
    'RoXP > RoIP' : [0, 0, 0, 0, 0, -1, 1, 0, 0, 0], 
    'RoIN > RoXN' : [0, 0, 0, 0, 0, 0, 0, 1, -1, 0], 
    'RoXN > RoIN' : [0, 0, 0, 0, 0, 0, 0, -1, 1, 0],
    'ReIP > ReIN' : [1, 0, -1, 0, 0, 0, 0, 0, 0, 0], 
    'ReIN > ReIP' : [-1, 0, 1, 0, 0, 0, 0, 0, 0, 0], 
    'ReXP > ReXN' : [0, 1, 0, -1, 0, 0, 0, 0, 0, 0], 
    'ReXN > ReXP' : [0, -1, 0, 1, 0, 0, 0, 0, 0, 0],
    'RoIP > RoIN' : [0, 0, 0, 0, 0, 1, 0, -1, 0, 0], 
    'RoIN > RoIP' : [0, 0, 0, 0, 0, -1, 0, 1, 0, 0], 
    'RoXP > RoXN' : [0, 0, 0, 0, 0, 0, 1, 0, -1, 0], 
    'RoXN > RoXP' : [0, 0, 0, 0, 0, 0, -1, 0, 1, 0],
    }
             
             
def normalize_contrast_vector(v):
    pos = [x for x in v if x > 0]
    if len(pos) > 0:
        total_pos = float(reduce(add, pos)) 
    
    neg = [x for x in v if x < 0]
    if len(neg) > 0:
        total_neg = float(reduce(add, neg)) 

    v2 = []
    for x in v:
        if x == 0:
            v2.append(0)
        elif x > 0:
            v2.append(round(float(x)/total_pos, 2))
        else:
            v2.append(-1*round(float(x)/total_neg, 2))
    return v2

## ---------------------------------------------------------------- ##
## This is a list of imaging-related variables
## ---------------------------------------------------------------- ##

TR     = 2000.0
OFFSET = 2

DELAY1               = 0
DELAY2               = 0
BLOCK                = 0
TRIAL                = 0
PRACTICED            = 0
ENCODING_ONSET       = 0
ENCODING_RT          = 0
EXECUTION_ONSET      = 0
EXECUTION_RT         = 0
RECALL_PROBE_ONSET   = 0
RECALL_PROBE_RT      = 0
RECALL_PROBE_ACC     = 0
ROTATION_PROBE_ONSET = 0
ROTATION_PROBE_RT    = 0
ROTATION_PROBE_ACC   = 0
OPERATOR1            = 0

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
        #self.trial = int(tokens[TRIAL])
        self.practiced = tokens[PRACTICED]
        self.encodingOnset = int(tokens[ENCODING_ONSET])
        self.encodingRt = int(tokens[ENCODING_RT])
        self.executionOnset = int(tokens[EXECUTION_ONSET])
        self.executionRt = int(tokens[EXECUTION_RT])
        self.type = tokens[OPERATOR1]
        
        # In ROI, there are two types of probes: Recalls
        # and Rotations. They need to be considered 
        # separately.
        
        if self.type == "RECALL":
            self.probeAcc = int(tokens[RECALL_PROBE_ACC])
            self.probeRt = int(tokens[RECALL_PROBE_RT])
            self.probeOnset = int(tokens[RECALL_PROBE_ONSET])

        elif self.type == "ROTATE":
            self.probeAcc = int(tokens[ROTATION_PROBE_ACC])
            self.probeRt = int(tokens[ROTATION_PROBE_RT])
            self.probeOnset = int(tokens[ROTATION_PROBE_ONSET])

        else:
            # If type != RECALL | ROTATE, then we have a serious
            # problem and cannot proceed
            print("Incorrect trial type: %s" % self.type)
            sys.exit(0)

        # Shortcut for accuracy
        self.acc = self.probeAcc
        self.blockBegin = 0

        # In case of RTs that are 0s, one needs to apply
        # a correction. In particular, one needs to estimate
        # the correct duration of each phase.
        if self.encodingRt == 0:
            d = self.executionOnset - self.encodingOnset - self.delay1 - 2000
            self.encodingRt = d

        if self.executionRt == 0:
            d = self.probeOnset - self.executionOnset - self.delay2 - 1000
            self.executionRt = d

        # If, after the correction, we have negative RTs, that means
        # that we are dealing with aborted trials. They need to be 
        # removed.
        
        if self.executionRt <= 0 or self.encodingRt <= 0:
            print "*** Excluding trial %s --- out of time ***" % self
            # The current probe RT belongs to the previous trial, 
            # so it must be overwritten.
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
        "Time since the beginning of the block"
        return (float(val) - float(self.blockBegin))/1000.0
        
    def __str__(self):
        return "<ROI:%d/ (%.2f), P:%s>" % (self.block, self.RelativeTime(self.encodingOnset), self.practiced)

    def __repr__(self):
        return self.__str__()



def Parse(filename):
    """Parses a Table-format logfile"""
    global DELAY1
    global DELAY2
    global BLOCK           
    global TRIAL           
    global PRACTICED       
    global ENCODING_ONSET  
    global ENCODING_RT     
    global EXECUTION_ONSET 
    global EXECUTION_RT    
    global RECALL_PROBE_ONSET     
    global RECALL_PROBE_RT        
    global RECALL_PROBE_ACC       
    global ROTATION_PROBE_ONSET     
    global ROTATION_PROBE_RT        
    global ROTATION_PROBE_ACC       
    global OPERATOR1

    fin      = open(filename, 'rU')
    subject  = filename.split('.')[0].split('-')[5]
    lines    = fin.readlines()
    tokens   = [x.split('\t') for x in lines]
    tokens   = [[y.strip() for y in x] for x in tokens]
    colNames = tokens[0]
    rows     = tokens[1:]
    
    DELAY1               = colNames.index("Delay1[Trial]")
    DELAY2               = colNames.index("Delay2[Trial]")
    BLOCK                = colNames.index("BlockNum")
    #TRIAL                = colNames.index("Trials")
    PRACTICED            = colNames.index("Practiced")
    ENCODING_ONSET       = colNames.index("Encoding.OnsetTime")
    ENCODING_RT          = colNames.index("Encoding.RT")
    EXECUTION_ONSET      = colNames.index("Execution.OnsetTime")
    EXECUTION_RT         = colNames.index("Execution.RT")
    RECALL_PROBE_ONSET   = colNames.index("RecallProbe.OnsetTime")
    RECALL_PROBE_RT      = colNames.index("RecallProbe.RT")
    RECALL_PROBE_ACC     = colNames.index("RecallProbe.ACC")
    ROTATION_PROBE_ONSET = colNames.index("RotationProbe.OnsetTime")
    ROTATION_PROBE_RT    = colNames.index("RotationProbe.RT")
    ROTATION_PROBE_ACC   = colNames.index("RotationProbe.ACC")
    OPERATOR1            = colNames.index("Operator1[Trial]")

    trials = [Trial(r) for r in rows]
    trials = [t for t in trials if t.ok]   # Excludes warmup trials 

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
            s.blockBegin = f.encodingOnset - (OFFSET * TR)

    BLOCKS = set(t.block for t in trials)
    BLOCKS = list(BLOCKS)
    BLOCKS.sort()
    print BLOCKS

    P = {'Yes' : 'Practiced', 'No' : 'Novel'}

    
    CV = {}    # The subject's contrast vectors
    for c in CONTRAST_LIST:
        CV[c]=[]

    fout = open("s%s_sessions.m" % subject, 'w')
    fcon = open("s%s_contrasts.txt" % subject, 'w')

    I = 0 # Total of i counters

    for b in BLOCKS:
        subset  = [t for t in trials if t.block == b]
        correct = [s for s in subset if s.acc == 1]
        errors  = [s for s in subset if s.acc == 0]

        print("Block %s, errors %d" % (b, len(errors)))

        description = ""
                
        i = 1     # counter for cell entries in matlab file
        j = 0     # counter for condition entries in contrast files

        
        for optype in ['RECALL', 'ROTATE']:

            # Encoding and Execution, divided by Practice (Yes/No)
            # ------------------------------------------------------------
            for practice in ['Yes', 'No']:
                for phase in ['Encoding', 'Execution']: #, 'Probe']:
                    appropriate = [c for c in correct 
                                   if c.practiced == practice and
                                   c.type == optype]
                    if len(appropriate) > 0:
                        description += "names{%d}='%s/%s/%s';\n" % (i, optype.lower(), phase, P[practice])
                        onsets = "%s" % [a.RelativeTime(a.onsets[phase]) for a in appropriate]
                        durations = "%s" % [a.rts[phase]/1000.0 for a in appropriate]
                        description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                        description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
                        i += 1
                        for c in CONTRAST_LIST:
                            #CV[c] += [len(appropriate)*CONTRAST_VECTORS[c][j]]
                            CV[c] += [CONTRAST_VECTORS[c][j]]
                    # No matter what, the contrast counter needs to be updated
                    j += 1


            # Probes, altogether (assumes no effect of practice)
            # ------------------------------------------------------------
            appropriate = [c for c in correct if c.type == optype]
            if len(appropriate) > 0:
                    
                description += "names{%d}='%s/Probe';\n" % (i, optype.lower())
                onsets = "%s" % [c.RelativeTime(c.onsets['Probe']) for c in appropriate]
                durations = "%s" % [c.rts['Probe']/1000.0 for c in appropriate]
                description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
                for c in CONTRAST_LIST:
                    #CV[c] += [len(appropriate)*CONTRAST_VECTORS[c][j]]
                    CV[c] += [CONTRAST_VECTORS[c][j]]
                #print "Condition: %s,Probe, value %d, index %d, total index %d " % (optype, len(appropriate), j, len(CV[CONTRAST_LIST[0]]))
                i += 1
            j += 1

        # Error trials
        # ------------------------------------------------------------
        # Note that, in the new design of the experiment, there might
        # be encoding errors only, or encoding/execution errors only,
        # because trials are aborted if one phases times out.
        #
        if len(errors) > 0:
            print "Errors, block %d" % b
            for phase in ['Encoding', 'Execution', 'Probe']:
                O = [e.RelativeTime(e.onsets[phase]) for e in errors if e.onsets[phase]>0 and e.rts[phase]>0]
                D = [e.rts[phase]/1000.0 for e in errors if e.onsets[phase]>0 and e.rts[phase]>0]
                if len(D) > 0:
                    print "\tWriting errors for blockj %d" % b
                    onsets = "%s" % O
                    durations = "%s" % D
                    description += "names{%d}='%s/Error';\n" % (i, phase)
                    description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                    description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
                    i += 1
                    print "Adding error to CV: %d ->" % len(CV[CONTRAST_LIST[0]]),
                    for c in CONTRAST_LIST:
                        CV[c] += [0]
                    print len(CV[CONTRAST_LIST[0]])
                #j+=1
        I += i
        fout.write("names=cell(1,%d);\n" % (i-1))
        fout.write("onsets=cell(1,%d);\n" % (i-1))
        fout.write("durations=cell(1,%d);\n" % (i-1))
        fout.write(description)
        fout.write("save('session%d.mat', 'names', 'onsets', 'durations');\n" % b)
        fout.flush()
    fout.close()
    
    for c in CONTRAST_LIST:
        #print(c, len(CV[c]), I)
        v = "%s" % normalize_contrast_vector(CV[c])
        v = v.replace(",", "")
        fcon.write("%s : %s\n" % (c, v))
    fcon.close()


if __name__ == "__main__":
    filename=sys.argv[1]
    Parse(filename)
    
