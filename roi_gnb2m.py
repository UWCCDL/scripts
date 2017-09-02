#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## ROI_GNB2M
## ---------------------------------------------------------------- ##
## A file that calculates the onset of experimental events (grouped
## by condition) in the ROI study. Event onsets and durations are
## written to text files specific for each experimental block
## ('session' in SPM lingo). The "multiple conditions" matlab file
## is optimized to yield beta maps suitable for MVPA analysis,
## specifically, a single MAP for every encoding event.


import sys, os
from operator import add
from math import sqrt

             
             
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

def expand_contrast_vector(lst, num):
    vec = [0] * num
    for i in lst:
        vec[i] = 1
    return normalize_contrast_vector(vec)

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

    CL = []  # Contrast list
    CV = {}    # The subject's contrast vectors
    #for c in CONTRAST_LIST:
    #    CV[c]=[]
    k = 1  # contrast counter

    fout = open("s%s_sessions_gnb.m" % subject, 'w')
    fcon = open("s%s_contrasts_gnb.txt" % subject, 'w')

    I = 0 # Total of i counters

    C = {'RECALL' : 0, 'ROTATE' : 0}  # Counter for events

    for b in BLOCKS:
        subset  = [t for t in trials if t.block == b]
        correct = [s for s in subset if s.acc == 1]
        errors  = [s for s in subset if s.acc == 0]

        print("Block %s, errors %d" % (b, len(errors)))

        description = ""
                
        i = 1     # counter for cell entries in matlab file
        j = 0     # counter for condition entries in contrast files

        for phase in ['Encoding']:
            for practice in ['Yes', 'No']:
                for optype in ['RECALL', 'ROTATE']:
                    appropriate = [c for c in correct 
                                   if c.practiced == practice and
                                   c.type == optype]
                    if len(appropriate) > 0:
                        for a in appropriate:
                            C[optype] += 1
                            name = "Encoding_%s_%s_%d" % (optype.lower(), P[practice], C[optype])
                            description += "names{%d}='%s';\n" % (i, name)
                            onsets = "[%s]" % (a.RelativeTime(a.onsets['Encoding']))
                            durations = "[%s]" % (a.rts['Encoding']/1000.0)
                            description += "onsets{%d}=%s;\n" % (i, onsets)
                            description += "durations{%d}=%s;\n" % (i, durations)
                            if name in CV.keys():
                                CV[name].append(k)
                            else:
                                CV[name] = [k]
                            
                            k += 1
                            i += 1
                    
        for phase in ['Execution']: #, 'Probe']:
            for practice in ['Yes', 'No']:
                for optype in ['RECALL', 'ROTATE']:
            
                    appropriate = [c for c in correct 
                                   if c.practiced == practice and
                                   c.type == optype]
                    if len(appropriate) > 0:
                        name = "%s/%s/%s" % (optype.lower(), phase, P[practice])
                        description += "names{%d}='%s';\n" % (i, name)
                        onsets = "%s" % [a.RelativeTime(a.onsets[phase]) for a in appropriate]
                        durations = "%s" % [a.rts[phase]/1000.0 for a in appropriate]
                        description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                        description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
                        i += 1
                        
                        if name in CV.keys():
                            print name, CV[name]
                            CV[name].append(k)
                        else:
                            CV[name] = [k]
                        k += 1


            # Probes, altogether (assumes no effect of practice)
            # ------------------------------------------------------------
            appropriate = [c for c in correct if c.type == optype]
            if len(appropriate) > 0:
                    
                name = "%s/Probe" % optype.lower()
                description += "names{%d}='%s';\n" % (i, name)
                onsets = "%s" % [c.RelativeTime(c.onsets['Probe']) for c in appropriate]
                durations = "%s" % [c.rts['Probe']/1000.0 for c in appropriate]
                description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))

                if name in CV.keys():
                    CV[name].append(k)
                else:
                    CV[name] = [k]
                k += 1
                i += 1
            

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
                    name = "%s/Error" % (phase)
                    description += "names{%d}='%s';\n" % (i, name)
                    description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
                    description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))

                    if name in CV.keys():
                        CV[name].append(k)
                    else:
                        CV[name] = [k]
                    k += 1
                    i += 1
                    
        I += i
        fout.write("names=cell(1,%d);\n" % (i-1))
        fout.write("onsets=cell(1,%d);\n" % (i-1))
        fout.write("durations=cell(1,%d);\n" % (i-1))
        fout.write(description)
        fout.write("save('session%d.mat', 'names', 'onsets', 'durations');\n" % b)
        fout.flush()
    fout.close()
    
    
    for condition in sorted(CV.keys()):
        v = "%s" % expand_contrast_vector(CV[condition], k)
        v = v.replace(",", "")
        fcon.write("%s : %s\n" % (condition, v[1:-1]))
    fcon.close()


if __name__ == "__main__":
    filename=sys.argv[1]
    Parse(filename)
    
