#!/bin/bash
# ------------------------------------------------------------------ #
# GENERATE-FIRST-LEVEL
# ------------------------------------------------------------------ #
# Generates a SPM/Matlab script to add new contrasts to existing
# first-level models. The code is output on the terminal and can be 
# saved on a .m file.
# ------------------------------------------------------------------
# Usage
# -----
#
#   $ add-contrast-first-level.sh [param_file] <results_dir> 
#                             <contrast_file>
#                             <subj1> <subj2>...<subjN>
#
# Where:
#   
#   [param_file] is an optional parameter file (see below)
#   <results_dir> is the folder where the SPM.mat file will be
#                 placed for each subject (it needs to already exist)
#                 in each subject's folder. 
#   <contrast_file> is a file listing all the contrast names and their
#                   vectors, separated by ":" 
#   <subjX> is the name of a subject's data directory.
# 
# Parameter File
# --------------
# A parameter file is a text file that contains preprocessing 
# parameters, one per line, in the form <PARAM> = <VALUE>. The 
# following parameters are read by this script (everything else
# is ignored).
# 
#   * TR: the repetition time.  By default, TR = 2.
#
#   * CONTRAST_MANAGMENT: Specifies the way SPM should handle the
#     contrast vector. These are the options:
#
#     1. none   : Will just use the vector. This is the ideal option
#                 when you have special vectors that already span
#                 multiple contrasts.
#     2. repl   : Will replicate the vector across session, but 
#                 *not* scale it.
#     3. replsc : Will replicate AND scale the contrasts across 
#                 multiple sessions (this is the default behavior)
#
# Contrast File
# --------------
# A contrast file is a text file that contains contrast names and 
# vector values, one per line, in the form <NAME> : <VECTOR>. For 
# example:
# 
#   Words > Pictures : 0 0 -0.5 -0.5 0 0.5 0.5 
#   Pictures > Words : 0 0 0.5 0.5 0 -0.5 -0.5 
#   ....
#
# By default, the script assumes that the same contrast vector is 
# used for each session, and will use SPM's 'Replicate&Scale' option when
# generating the contrasts. This behavior can be changed by using
# the parameter file's CONTRAST_MANAGEMENT option.
# 
# ------------------------------------------------------------------ #
# Notes
# -----
# 
# The script assumes the data are organized according to the CCDL's 
# standard format,i.e.:
#
#  1. The root folder for each experiment EXP is located in
#    /fmri/data/<PROJECT>/<EXP>;
#
#  2. The data for each subject is contained in folder that has
#    the same name as the subject;
#    
# Do not use the script unless all of the above assumptions are true.
# ------------------------------------------------------------------ #
#
# History
# -------
#
#  2013-08-08 : * File Created.
#
# ------------------------------------------------------------------ #

HLP_MSG="
 Usage
 -----

   $ add-contrasts-first-level.sh [param_file] <results_dir> 
                             <contrast_file>
                             <subj1> <subj2>...<subjN>

 Where:
   
   [param_file] is an optional parameter file (see below)
   <results_dir> is the folder where the SPM.mat file will be
                 placed for each subject (it needs to already exist)
                 in each subject's folder. 
   <contrast_file> is a file listing all the contrast names and their
                   vectors, separated by ":" 
   <subjX> is the name of a subject's data directory.
 
 Parameter File
 --------------
 A parameter file is a text file that contains preprocessing 
 parameters, one per line, in the form <PARAM> = <VALUE>. The 
 following parameter is read by this script (everything else
 is ignored).
 
   * CONTRAST_MANAGMENT: Specifies the way SPM should handle the
     contrast vector. These are the options:

     1. none   : Will just use the vector. This is the ideal option
                 when you have special vectors that already span
                 multiple contrasts.
     2. repl   : Will replicate the vector across session, but 
                 *not* scale it.
     3. replsc : Will replicate AND scale the contrasts across 
                 multiple sessions (this is the default behavior)

 Contrast File
 --------------
 A contrast file is a text file that contains contrast names and 
 vector values, one per line, in the form <NAME> : <VECTOR>. For 
 example:
 
   Words > Pictures : 0 0 -0.5 -0.5 0 0.5 0.5 
   Pictures > Words : 0 0 0.5 0.5 0 -0.5 -0.5 
   ....

 By default, the script assumes that the same contrast vector is 
 used for each session, and will use SPM's 'Replicate&Scale' option when
 generating the contrasts. This behavior can be changed by using
 the parameter file's CONTRAST_MANAGEMENT option.
 
 ------------------------------------------------------------------ \n
 Notes
 -----
 
 The script assumes the data are organized according to the CCDL's 
 standard format,i.e.:

  1. The root folder for each experiment EXP is located in
     /fmri/data/<PROJECT>/<EXP>;

  2. The data for each subject is contained in folder that has
     the same name as the subject;

 Do not use the script unless all of the above assumptions are true.
"

# ------------------------------------------------------------------ #
# General variabls
# ------------------------------------------------------------------ #

CONTRAST_MANAGEMENT=replsc

# ------------------------------------------------------------------ #
# Load params (if any)
# ------------------------------------------------------------------ #

if [ $# -gt 0 ]; then
    if [ -f $1 ]; then
	param_file=$1
        # If the first argument is a file, it must be a parameter file
	echo "Found parameter file $param_file" >&2

        # Check the TR
	if grep -q "TR" $param_file; then
	    TR=`grep '^TR' ${param_file} | cut -f2 -d= | tail -1 | tr -d " '"`
	    echo "  Setting TR to $TR" >&2 
	fi

	# Check what to do with contrasts
	if grep -q "CONTRAST_MANAGEMENT" $param_file; then
	    CONTRAST_MANAGEMENT=`grep '^CONTRAST_MANAGEMENT' ${param_file} | cut -f2 -d= | tail -1 | tr -d " '"`
	    echo "  Setting CONTRAST_MANAGEMENT to $CONTRAST_MANAGEMENT" >&2 
	fi
   
        # Finally, skip the first argument
	shift 1
    fi
fi

# ------------------------------------------------------------------ #
# Print instructions, if not enough args
# ------------------------------------------------------------------ #

if [ $# -lt 3 ]; then
    IFS=''
    echo -e $HLP_MSG >&2
    unset IFS
    exit
fi

results_dir=$1
c_file=$2
shift 2

base=`pwd`
J=1

for subj in "$@" ; do
    [ -d $subj ] || continue
    echo "matlabbatch{$J}.spm.stats.con.spmmat = {'${base}/${subj}/${results_dir}/SPM.mat'};"
    
    C=1
    while read line; do
	cname=`echo $line | cut -f1 -d:`
	cvector=`echo $line | cut -f2 -d:`
	echo "matlabbatch{$J}.spm.stats.con.consess{$C}.tcon.name = '${cname}';"
	echo "matlabbatch{$J}.spm.stats.con.consess{$C}.tcon.convec = [${cvector}];"
	echo "matlabbatch{$J}.spm.stats.con.consess{$C}.tcon.sessrep = '${CONTRAST_MANAGEMENT}';"
	C=$((C+1))
	
    done < ${c_file}
    echo "matlabbatch{$J}.spm.stats.con.delete = 0;"
    
    J=$((J+1))
done