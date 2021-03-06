#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## ROI2M_DCM
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
    'ReI', 'ReX', 'ReR', 
    'RoI', 'RoX', 'RoR',
    ]

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
    An abstract class representing a RITL trial---three phases
    (Encoding, Execution, Response), with associated Onsets and
    Durations (ie. RTs), followed by randomly-varying Delays.
    """
    def __init__(self, tokens):
        """Initializes and catches eventual errors"""
        self.ok = True
        self.adjust = 0   # Adjusts time. Needed for bizarre dcm blocks
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
        return (float(val) - float(self.blockBegin) + float(self.adjust))/1000.0
        
    def __str__(self):
        return "<ROI:%d/ (%.2f), P:%s>" % (self.block, self.RelativeTime(self.encodingOnset), self.practiced)

    def __repr__(self):
        return self.__str__()

class Block(object):
    """An abstract description of a block"""
    def __init__(self, scans, keep=True):
        print(scans, keep)
        self.keep = eval(keep)
        self.scans = int(scans)
        self.tr = TR
        self.offset = 0  # Number of scans before this block

    def __str__(self):
        return "<Block: %d (%s)>" % (self.scans, self.keep)

    def __repr__(self):
        return self.__str__()

def load_block_description(filename="blocks.txt"):
    """Loads a description of the blocks"""
    fin = file(filename, 'r')
    lines = fin.readlines()
    lists = [[y.strip() for y in x.split()] for x in lines]
    blocks = [ Block(x[0], x[1]) for x in lists]
    print blocks
    return blocks


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

    # Now load the block description
    blocks = load_block_description("blocks.txt")  # Somehow.

    # Add a new field on the fly to indicate the block
    # number. It will be helpful later.
    i = 1
    for b in blocks:
        b.number = i
        i += 1
    
    # A simple trick to correct for blocks that are not
    # included: Set their duration (i.e., scans) to zero.
    # In all other cases, remove the last scan from the count
    for b in blocks:
        if not b.keep:
            b.scans = 0
        else:
            b.scans -= 1

    # Now, calculate the block's incrementeal offsets, that is,
    # the number of scans that occurred before them (discarded
    # blocks have already been dealt with in the previous step).

    for i in range(len(blocks)):
        blocks[i].offset = sum([x.scans for x in blocks[0:i]])
    
    for f in FIRST_TRIALS:
        #print f.block
        print f.block
        subset = [t for t in trials if t.block == f.block]
        for s in subset:
            s.blockBegin = f.encodingOnset - (OFFSET * TR)
            if ( f.block > 1):
                #print "New offset:", blocks[ f.block - 1].offset * TR
                s.adjust = (blocks[ f.block - 1].offset * TR)
            else:
                s.adjust = 0.0

    # Now, remove blocks and trials that need to be excluded
    print(len(trials))
    discarded = [x.number for x in blocks if not x.keep]
    print discarded
    trials = [x for x in trials if x.block not in discarded]
    print(len(trials)), set([x.block for x in trials]), set([x.adjust for x in trials])

    fout = open("s%s_dcm_sessions.m" % subject, 'w')

    # Ok, this if the first design. We have six drives total.
    # 
    # We have one stimulus drives:
    #    VisualStimulus
    #
    # And five higher-level ones:
    #  
    #    EncodeRotate
    #    EncodeRecall
    #    ExecuteRotate
    #    ExecuteResponse
    #    Respond
    #   
    # No error trials are modeled.
    #

    fout.write("names=cell(1,5);\n")
    fout.write("onsets=cell(1,5);\n")
    fout.write("durations=cell(1,5);\n")
        
    description = ""
                    
    i = 1     # counter for cell entries in matlab file
    j = 0     # counter for condition entries in contrast files
    
    # The Visual Stimulus
    onsets = []
    durations = []
    for t in trials:
        for phase in ['Encoding', 'Execution', 'Probe']:
            if t.rts[phase] > 0:
                onsets.append(t.RelativeTime(t.onsets[phase]))
                durations.append(t.rts[phase]/1000.0)

    # Now, transform the lists of numbers in corresponding strings
    # (it would be easier to generate the M code)
    
    onsets = "%s" % onsets 
    durations = "%s" % durations
        
    # Add this code to the M file
    description += "names{1}='VisualStimulus';\n" 
    
    description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
    description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
    
    i += 1
        
    # Now the four Phase X Operatiorn combos
    
    for optype in ['RECALL', 'ROTATE']:
        
        # Encoding and Execution, divided by Practice (Yes/No)
        # ------------------------------------------------------------
        appropriate = [t for t in trials if t.type == optype and t.acc == 1]

        for phase in ['Encoding', 'Execution']: # 'Probe']:
            description += "names{%d}='%s_%s';\n" % (i, phase, optype.lower())
            onsets = "%s" % [a.RelativeTime(a.onsets[phase]) for a in appropriate if a.rts[phase] > 0]
            durations = "%s" % [a.rts[phase]/1000.0 for a in appropriate if a.rts[phase] > 0]
            description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
            description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
            i += 1
    
    # Now the probes
    #description += "names{%d}='Response';\n" % (i)
    #onsets = "%s" % [t.RelativeTime(t.onsets['Probe']) for t in trials if t.rts[phase] > 0]
    #durations = "%s" % [t.rts['Probe']/1000.0 for t in trials if t.rts[phase] > 0]
    #description += "onsets{%d}=%s;\n" % (i, onsets.replace(";", ""))
    #description += "durations{%d}=%s;\n" % (i, durations.replace(";", ""))
               

    fout.write(description)
    fout.write("save('dcm_session.mat', 'names', 'onsets', 'durations');\n")
    fout.flush()
    fout.close()

    # Final touch; we need to write down the block regressors. 
    # (the sessions)

    blocks = [x for x in blocks if x.keep]
    fout1 = file("block_regressors.txt", "w")
    fout2 = file("shortform_block_regressors.txt", "w")
    n = sum([x.scans for x in blocks])
    vectors = [[0] * n for b in blocks]
    
    for i in range(len(blocks)):
        start = sum([x.scans for x in blocks[0:i]])
        end = start + blocks[i].scans
        print start, end
        for j in range(start, end):
            vectors[i][j] = 1

    for i in range(n):
        for j in range(len(blocks)):
            fout1.write("%d\t" % vectors[j][i])
        fout1.write("\n")
    
    for i in range(n):
        for j in range(len(blocks) - 1):
            fout2.write("%d\t" % vectors[j][i])
        fout2.write("\n")
    
    fout1.close()
    fout2.close()

if __name__ == "__main__":
    filename=sys.argv[1]
    Parse(filename)
    
