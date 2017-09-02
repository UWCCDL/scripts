#! /usr/bin/env python
## ---------------------------------------------------------------- ##
## PARSE REPORT                                                     ##
## ---------------------------------------------------------------- ##
## Parses an XjView/SPM report on active clusters into a printable  ##
## table that you can copy and paste into Word.                     ##
## ---------------------------------------------------------------- ##
## -- History --                                                    ##
##                                                                  ##
## 2014-01-03 : Added list of AAL labels (and percentages)          ##
## 2010-09-24 : Version 1.0 up and running.                         ##
## 2010-09-23 : File created                                        ##
##                                                                  ##
## ---------------------------------------------------------------- ##


import sys, os, types
from operator import add
from decimal import Decimal, getcontext, setcontext, Context

AAL= {"Precentral_L" : "Precental gyrus",
      "Precentral_R" : "Precental gyrus",
      "Frontal_Sup_L" : "Superior frontal gyrus, dorsolateral",
      "Frontal_Sup_R" : "Superior frontal gyrus, dorsolateral",
      "Frontal_Sup_Orb_L" : "Superior frontal gyrus, orbital part",
      "Frontal_Sup_Orb_R" : "Superior frontal gyrus, orbital part",
      "Frontal_Mid_L" : "Middle frontal gyrus",
      "Frontal_Mid_R" : "Middle frontal gyrus",
      "Frontal_Mid_Orb_L" : "Middle frontal gyrus, orbital part",
      "Frontal_Mid_Orb_R" : "Middle frontal gyrus, orbital part",
      "Frontal_Inf_Oper_L" : "Inferior frontal gyrus, opercular part",
      "Frontal_Inf_Oper_R" : "Inferior frontal gyrus, opercular part",
      "Frontal_Inf_Tri_L" : "Inferior frontal gyrus, triangular part",
      "Frontal_Inf_Tri_R" : "Inferior frontal gyrus, triangular part",
      "Frontal_Inf_Orb_L" : "Inferior frontal gyrus, orbital part",
      "Frontal_Inf_Orb_R" : "Inferior frontal gyrus, orbital part",
      "Rolandic_Oper_L" : "Rolandic operculum",
      "Rolandic_Oper_R" : "Rolandic operculum",
      "Supp_Motor_Area_L" : "Supplementary motor area",
      "Supp_Motor_Area_R" : "Supplementary motor area",
      "Olfactory_L" : "Olfactory cortex",
      "Olfactory_R" : "Olfactory cortex",
      "Frontal_Sup_Medial_L" : "Superior frontal gyrus, medial",
      "Frontal_Sup_Medial_R" : "Superior frontal gyrus, medial",
      "Frontal_Mid_Orb_L" : "Superior frontal gyrus, medial orbital",
      "Frontal_Mid_Orb_R" : "Superior frontal gyrus, medial orbital",
      "Rectus_L" : "Gyrus rectus",
      "Rectus_R" : "Gyrus rectus",
      "Insula_L" : "Insula",
      "Insula_R" : "Insula",
      "Cingulum_Ant_L" : "Anterior cingulate and paracingulate gyri",
      "Cingulum_Ant_R" : "Anterior cingulate and paracingulate gyri",
      "Cingulum_Mid_L" : "Median cingulate and paracingulate gyri",
      "Cingulum_Mid_R" : "Median cingulate and paracingulate gyri",
      "Cingulum_Post_L" : "Posterior cingulate gyrus",
      "Cingulum_Post_R" : "Posterior cingulate gyrus",
      "Hippocampus_L" : "Hippocampus",
      "Hippocampus_R" : "Hippocampus",
      "ParaHippocampal_L" : "Parahippocampal gyrus",
      "ParaHippocampal_R" : "Parahippocampal gyrus",
      "Amygdala_L" : "Amygdala",
      "Amygdala_R" : "Amygdala",
      "Calcarine_L" : "Calcarine fissure and surrounding cortex",
      "Calcarine_R" : "Calcarine fissure and surrounding cortex",
      "Cuneus_L" : "Cuneus",
      "Cuneus_R" : "Cuneus",
      "Lingual_L" : "Lingual gyrus",
      "Lingual_R" : "Lingual gyrus",
      "Occipital_Sup_L" : "Superior occipital gyrus",
      "Occipital_Sup_R" : "Superior occipital gyrus",
      "Occipital_Mid_L" : "Middle occipital gyrus",
      "Occipital_Mid_R" : "Middle occipital gyrus",
      "Occipital_Inf_L" : "Inferior occipital gyrus",
      "Occipital_Inf_R" : "Inferior occipital gyrus",
      "Fusiform_L" : "Fusiform gyrus",
      "Fusiform_R" : "Fusiform gyrus",
      "Postcentral_L" : "Postcentral gyrus",
      "Postcentral_R" : "Postcentral gyrus",
      "Parietal_Sup_L" : "Superior parietal gyrus",
      "Parietal_Sup_R" : "Superior parietal gyrus",
      "Parietal_Inf_L" : "Inferior parietal, but supramarginal and angular gyri",
      "Parietal_Inf_R" : "Inferior parietal, but supramarginal and angular gyri",
      "SupraMarginal_L" : "Supramarginal gyrus",
      "SupraMarginal_R" : "Supramarginal gyrus",
      "Angular_L" : "Angular gyrus",
      "Angular_R" : "Angular gyrus",
      "Precuneus_L" : "Precuneus",
      "Precuneus_R" : "Precuneus",
      "Paracentral_Lobule_L" : "Paracentral lobule",
      "Paracentral_Lobule_R" : "Paracentral lobule",
      "Caudate_L" : "Caudate nucleus",
      "Caudate_R" : "Caudate nucleus",
      "Putamen_L" : "Lenticular nucleus, putamen",
      "Putamen_R" : "Lenticular nucleus, putamen",
      "Pallidum_L" : "Lenticular nucleus, pallidum",
      "Pallidum_R" : "Lenticular nucleus, pallidum",
      "Thalamus_L" : "Thalamus",
      "Thalamus_R" : "Thalamus",
      "Heschl_L" : "Heschl gyrus",
      "Heschl_R" : "Heschl gyrus",
      "Temporal_Sup_L" : "Superior temporal gyrus",
      "Temporal_Sup_R" : "Superior temporal gyrus",
      "Temporal_Pole_Sup_L" : "Temporal pole: superior temporal gyrus",
      "Temporal_Pole_Sup_R" : "Temporal pole: superior temporal gyrus",
      "Temporal_Mid_L" : "Middle temporal gyrus",
      "Temporal_Mid_R" : "Middle temporal gyrus",
      "Temporal_Pole_Mid_L" : "Temporal pole: middle temporal gyrus",
      "Temporal_Pole_Mid_R" : "Temporal pole: middle temporal gyrus",
      "Temporal_Inf_L" : "Inferior temporal gyrus",
      "Temporal_Inf_R" : "Inferior temporal gyrus"}

class Cluster:
    def __init__(self, number):
        self.number = number
        self.labels = []
        self.regions = []

    def __str__(self):
        return "<Cluster %d, %s, %d, %s>" % (self.number, self.MNI, self.size, self.peak)

    def __repr__(self):
        return self.__str__()

    def findBA(self):
        "Finds the cluster's Brodmann Areas (if one exists)"
        onlyBAs = [x for x in self.regions if x.find('brodmann') > 0]
        if len(onlyBAs) == 0:
            return '-'
        else:
            res = ""
            for x in onlyBAs:
                res += "BA%s (%.2f%%); " % (x.split()[3], (float(x.split()[0])*100.0)/float(self.size))
            return res[0:-1] # Trims the last space
    
    def findAAL(self):
        "Finds the cluster's AAL labels (if any)"
        onlyAALs = [x for x in self.regions if x.find('(aal)') > 0]
        if len(onlyAALs) == 0:
            return '-'
        else:
            res = ""
            for x in onlyAALs:
                aal_name = x.split()[1]
                
                if aal_name in AAL.keys():
                    real_name = AAL[ x.split()[1] ]
                else:
                    real_name = aal_name

                if aal_name.endswith("_L"):
                    real_name = "Left " + real_name
                elif aal_name.endswith("_R"):
                    real_name = "Right " + real_name
                    
                res += "%s (%.2f%%); " % (real_name, (float(x.split()[0])*100.0)/float(self.size))
            return res[0:-1] # Trims the last space
    


def Parse(filename):
    "Fuck My Life..."
    report = file(filename, 'r')
    
    lines = report.readlines()
    clusters = []
    current  = None

    for line in lines:
        if line.strip().startswith('Cluster'):
            tokens = line.split()
            current = Cluster(int(tokens[1]))

        elif line.startswith('----'):
            clusters.append(current)

        elif line.startswith("Peak MNI coordinate:"):
            current.MNI = [int(x) for x in line.split(':')[1].split()]

        elif line.startswith("Peak MNI coordinate region:"):
            current.labels = [x.strip() for x in line.split(':')[1].split('//')]

        elif line.startswith("Number of voxels:"):
            current.size = int(line.split(':')[1])

        elif line.startswith("Peak intensity:"):
            current.peak = Decimal(line.split(':')[1])

        elif line.strip().split()[0].isdigit():
            current.regions.append(line.strip())
        else:
            pass

    if clusters[-1] is not current:
        clusters.append(current)
        
    return clusters

def isCoordinates(element):
    if type(element) == types.ListType and len(element) == 3:
        return len([x for x in element if type(x) == types.IntType]) == 3
    else:
        return False

def isLabels(element):
    if type(element) == types.ListType:
        return len([x for x in element if type(x) == types.StringType])==len(element)
    else:
        return False

def Table(clusters):
    print "Index\tMNI (Peak)\tPeak Anatomical Location\tBrodmann Areas\tAAL Locations\tSize (voxels)\tPeak intensity"
    for c in clusters:
        for element in (c.number, c.MNI, c.labels, c.findBA(), c.findAAL(), c.size, c.peak):
            if isCoordinates(element):
                a,b,c = element
                print "%s, %s, %s\t" % (a, b, c),

            elif isLabels(element):
                filtered = [x for x in element if x != 'undefined']
                print "%s\t" % filtered[-1],
            
            elif type(element) == Decimal:
                print element.quantize(Decimal('.01')),
                
            else:
                print "%s\t" % element,
        print "\n",
    
if __name__ == "__main__":
    filename = sys.argv[1]
    clusters = Parse(filename)
    Table(clusters)
