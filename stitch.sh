#!/bin/bash
# ------------------------------------------------------------------ #
# STITCH
# ------------------------------------------------------------------ #
# Stitches together multiple fMRI runs into a single run. Transforms
# all data into Percent Signal Change to remove baseline differences
# across sessions.
# ------------------------------------------------------------------
# Usage
# -----
#
#   $ stitch.sh  <subj1> <subj2>...<subjN>
#
# Where:
#   
#   <subjX> is the name of a subject's data directory.
#
# What it does
# ------------
# The file will use AFNI's tools to transform the data into
# PSC for each session, then merge all sessions together, and
# finally usethe union of all single-sessions masks to mask the
# final timeseries.
#
# Notes
# -----
#
# * The resulting file will be called swa<subID>_psc_masked.nii
# 
# * The old swa* files will be saved into a subfolder called
#   "old_swa"
#
# * Intermedite files (single-session PSC and masks) will be
#   saved into a folder called "intermediate"
#
# * The data is expressed into percentages with an (arbitrary)
#   baseline of 1000; e.g. a 5% increase in signals will record
#   as 1005.
#
# --------------------------------------------------------------------



HLP_MSG="
 Usage
 -----

   $ stitch.sh  <subj1> <subj2>...<subjN>

 Where:
   
   <subjX> is the name of a subject's data directory.

 What it does
 ------------
 The file will use AFNI's tools to transform the data into
 PSC for each session, then merge all sessions together, and
 finally usethe union of all single-sessions masks to mask the
 final timeseries.

 Notes
 -----

 * The resulting file will be called swa<subID>_psc_masked.nii
 
 * The old swa* files will be saved into a subfolder called
   'old_swa'

 * Intermedite files (single-session PSC and masks) will be
   saved into a folder called 'intermediate'

 * The data is expressed into percentages with an (arbitrary)
   baseline of 1000; e.g. a 5% increase in signals will record
   as 1005.
"

if [ $# -lt 1 ]; then
    IFS=''
    echo -e $HLP_MSG >&2
    unset IFS
    exit
fi

PATH=$PATH:/home/stocco/abin   # Make sure you add afni

for folder in "$@"; do
    
    if [ -d $folder ]; then
	
	cd ${folder}/raw

	for session in swa*-d*.nii; do
	    
	    #create mean file
	    subject=`echo $session | cut -f1 -d_`
	    name=`echo $session | cut -f1 -d-`
	    
	    mean=${name}_mean.nii
	    3dTstat -prefix $mean -overwrite $session
	    
	    # Create mask
	    3dAutomask -prefix ${name}_mask.nii -overwrite $session
	    
	    # Percent Signal Change
	    # Modified to add an arbitrary baseline.
	    3dcalc -overwrite \
		   -a $session \
		   -b $mean \
		   -prefix ${name}_psc.nii \
		   -expr '((a-b)*100)/b + 1000'
		
	done
	    
	# Concatenate masks and timeseries 
	3dTcat -overwrite -prefix ${subject}_mask.nii ${name}*_mask*.nii
	3dTcat -overwrite -prefix ${subject}_psc.nii swa*psc.nii 
	
	    
	# Average and binarize mask
	3dTstat -overwrite -prefix swamasks.nii ${subject}_mask.nii
	3dcalc -overwrite -prefix swamask.nii \
	                  -expr 'ispositive(a)' \
	                  -a swamasks.nii
	    
	# Filter out empty space
	3dcalc -overwrite -prefix ${subject}_psc_masked.nii \
	       -expr 'a*b' \
	       -a ${subject}_psc.nii \
	       -b swamask.nii
	    
	    
	# Save the old files and the intermediate files
	    
	if [ ! -d old_swa ]; then
	    mkdir old_swa
	fi
	    
	mv swa*-d[0-9]*.nii old_swa
	
	if [ ! -d intermediate ]; then
	    mkdir intermediate
	fi
	
	mv *_mask.nii *_mean.nii *_psc.nii swamask*.nii intermediate
    else
	echo "Cannot find folder corresponding to subject $folder"
    fi
    
    # Back to base folder
    cd ../..
done

