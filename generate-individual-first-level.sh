#!/bin/bash
# ------------------------------------------------------------------ #
# GENERATE-INDIVIDUAL-FIRST-LEVEL
# ------------------------------------------------------------------ #
# Generates a 1st level model SPM/Matlab script, which is output on
# the terminal and can be saved on a .m file.
# ------------------------------------------------------------------
# Usage
# -----
#
#   $ generate-first-level.sh [param_file] <results_dir> 
#                             <subj1> <subj2>...<subjN>
#
# Where:
#   
#   [param_file] is an optional parameter file (see below)
#   <results_dir> is the folder where the SPM.mat file will be
#                 placed for each subject (it needs to already exist)
#                 in each subject's folder. 
#   <subjX> is the name of a subject's data directory.
# 
# # Parameter File
# --------------
# A parameter file is a text file that contains preprocessing 
# parameters, one per line, in the form <PARAM> = <VALUE>. The 
# following parameters are read by this script (everything else
# is ignored).
# 
#   * TR: the repetition time.  By default, TR = 2.
#
#   * HPF: Specifies the value of the High-pass filter in SPM 
#     (in seconds). Can be any positive number; by default it is
#     HPF = 128
#
# Contrast File
# --------------
# This scriopt requires a contrast file for each participant, to
# be place in the subject folder and be named 
# "contrasts_<subj>.txt". 
# A contrast file is a text file that contains contrast names and 
# vector values, one per line, in the form <NAME> : <VECTOR>. For 
# example:
# 
#   Words > Pictures : 0 0 -0.5 -0.5 0 0.5 0.5 
#   Pictures > Words : 0 0 0.5 0.5 0 -0.5 -0.5 
#   ....
#
# The script assumes that each subject will have his or her
# own contrast files. For that reason, the contrast will be neither
# rescaled nor repeated per session. 
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
# In addition, the script assumes that 
#   
#  3. the contrast vector can be replicated and scaled across 
#    sessions.
#
# Do not use the script unless all of the above assumptions are true.
# ------------------------------------------------------------------ #
#
# History
# -------
#  2017-11-04 : * Fixed an error in the 'HLP' doc string.
#
#  2017-10-12 : * Generated as a fork of generate-first-level.sh
#
#  2013-12-12 : * Added HPF and MOTION_REGRESSORS to the params.
#
#  2013-08-08 : * Added documentation string.
#             : * Included an initial parameter file
# 
#  2013-07-23 : * First version working
#
#  2013-07-22 : * File started.
# ------------------------------------------------------------------ #

HLP_MSG="
Usage
-----

  $ generate-first-level.sh [param_file] <results_dir> 
                            <subj1> <subj2>...<subjN>

Where:
  
  [param_file] is an optional parameter file (see below)
  <results_dir> is the folder where the SPM.mat file will be
                placed for each subject (it needs to already exist)
                in each subject's folder. 
  <subjX> is the name of a subject's data directory.

# Parameter File
--------------
A parameter file is a text file that contains preprocessing 
parameters, one per line, in the form <PARAM> = <VALUE>. The 
following parameters are read by this script (everything else
is ignored).

  * TR: the repetition time.  By default, TR = 2.

  * HPF: Specifies the value of the High-pass filter in SPM 
    (in seconds). Can be any positive number; by default it is
    HPF = 128

Contrast File
--------------
This scriopt requires a contrast file for each participant, to
be placed in the subject folder and be named 
'contrasts_<subj>.txt'. 
A contrast file is a text file that contains contrast names and 
vector values, one per line, in the form <NAME> : <VECTOR>. For 
example:

  Words > Pictures : 0 0 -0.5 -0.5 0 0.5 0.5 
  Pictures > Words : 0 0 0.5 0.5 0 -0.5 -0.5 
  ....

The script assumes that each subject will have his or her
own contrast files. For that reason, the contrast will be neither
rescaled nor repeated per session.

 Notes
 -----

 The script assumes the data are organized according to the CCDL's 
 standard format,i.e.:

  1. The root folder for each experiment EXP is located in
     /fmri/data/<PROJECT>/<EXP>;
  2. The data for each subject is contained in folder that has
     the same name as the subject;
    
 Do not use the script unless all of the above assumptions are true.

 Summary
 -------

   $ generate-first-level.sh [param_file] <results_dir> 
                             <subj1> <subj2>...<subjN>

"

# ------------------------------------------------------------------ #
# General variabls
# ------------------------------------------------------------------ #

TR=2
CONTRAST_MANAGEMENT=none
HPF=128
MOTION_REGRESSORS=0

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

	# Check the value of HPF
	if grep -q "HPF" $param_file; then
	    HPF=`grep '^HPF' ${param_file} | cut -f2 -d= | tail -1 | tr -d " '"`
	    echo "  Setting HPF to $HPF" >&2 
	fi

	# Check whether to include motion parameters
	if grep -q "MOTION_REGRESSORS" $param_file; then
	    MOTION_REGRESSORS=`grep '^MOTION_REGRESSORS' ${param_file} | cut -f2 -d= | tail -1 | tr -d " '"`
	    echo "  Setting MOTION_REGRESSORS to $MOTION_REGRESSORS" >&2 
	fi


        # Finally, skip the first argument
	shift 1
    fi
fi

# ------------------------------------------------------------------ #
# Print instructions, if not enough args
# ------------------------------------------------------------------ #

if [ $# -lt 2 ]; then
    IFS=''
    echo -e $HLP_MSG >&2
    unset IFS
    exit
fi


results_dir=$1
#c_file=$2
shift 1

base=`pwd`
J=1

for subj in "$@" ; do
    c_file=contrasts_${subj}.txt
    echo "Generating model for $subj" >&2
    [ -d $subj ] || continue
    cd ${subj}/raw
    
    echo "matlabbatch{$J}.spm.stats.fmri_spec.timing.units = 'secs';"
    echo "matlabbatch{$J}.spm.stats.fmri_spec.timing.RT = ${TR};"
    echo "matlabbatch{$J}.spm.stats.fmri_spec.timing.fmri_t = 16;"
    echo "matlabbatch{$J}.spm.stats.fmri_spec.timing.fmri_t0 = 1;"
    echo "matlabbatch{$J}.spm.stats.fmri_spec.dir = {'${base}/${subj}/${results_dir}/'}"

    S=1
    
    for session in `ls sw*.nii`; do
	echo "matlabbatch{$J}.spm.stats.fmri_spec.sess($S).scans = {"

	N=`echo $session | cut -f1 -d. | tail -c 4`
	N=$(echo $N | sed 's/^0*//')   # Removed leading zeroes

	for ((image=1; image<N; ++image)); do 
	    echo "'${base}/${subj}/raw/${session},${image}'"
	done

	echo "};"
	echo "matlabbatch{$J}.spm.stats.fmri_spec.sess($S).cond = struct('name', {}, 'onset', {}, 'duration', {}, 'tmod', {}, 'pmod', {});"
	echo "matlabbatch{$J}.spm.stats.fmri_spec.sess($S).multi = {'${base}/${subj}/behav/session${S}.mat'};"
	echo "matlabbatch{$J}.spm.stats.fmri_spec.sess($S).regress = struct('name', {}, 'val', {});"

	# If MOTION_REGRESSORS is true,
	if [ $MOTION_REGRESSORS != 0 ]; then
	    mot_params=`ls rp_*.txt | head -${S} | tail -1`
	    echo "matlabbatch{$J}.spm.stats.fmri_spec.sess($S).multi_reg = {'${base}/${subj}/raw/${mot_params}'};"
	else
	    echo "matlabbatch{$J}.spm.stats.fmri_spec.sess($S).multi_reg = {''};"
	fi	

	echo "matlabbatch{$J}.spm.stats.fmri_spec.sess($S).hpf = ${HPF};"
	
	S=$((S+1))
    done
    echo "matlabbatch{$J}.spm.stats.fmri_spec.fact = struct('name', {}, 'levels', {});"
    echo "matlabbatch{$J}.spm.stats.fmri_spec.bases.hrf.derivs = [0 0];"
    echo "matlabbatch{$J}.spm.stats.fmri_spec.volt = 1;"
    echo "matlabbatch{$J}.spm.stats.fmri_spec.global = 'None';"
    echo "matlabbatch{$J}.spm.stats.fmri_spec.mask = {''};"
    echo "matlabbatch{$J}.spm.stats.fmri_spec.cvi = 'AR(1)';"
    
    cd ../ #../
    J=$((J+1))

    echo -e "\n % Estimate\n"
    
    echo "matlabbatch{$J}.spm.stats.fmri_est.spmmat(1) = cfg_dep;"
    echo "matlabbatch{$J}.spm.stats.fmri_est.spmmat(1).tname = 'Select SPM.mat';"
    echo "matlabbatch{$J}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).name = 'filter';"
    echo "matlabbatch{$J}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).value = 'mat';"
    echo "matlabbatch{$J}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).name = 'strtype';"
    echo "matlabbatch{$J}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).value = 'e';"
    echo "matlabbatch{$J}.spm.stats.fmri_est.spmmat(1).sname = 'fMRI model specification: SPM.mat File';"
    echo "matlabbatch{$J}.spm.stats.fmri_est.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});"
    echo "matlabbatch{$J}.spm.stats.fmri_est.spmmat(1).src_output = substruct('.','spmmat');"
    echo "matlabbatch{$J}.spm.stats.fmri_est.method.Classical = 1;"
    
    J=$((J+1))
    
    echo -e "\n% Contrast manager"
    
    echo "matlabbatch{$J}.spm.stats.con.spmmat(1) = cfg_dep;"
    echo "matlabbatch{$J}.spm.stats.con.spmmat(1).tname = 'Select SPM.mat';"
    echo "matlabbatch{$J}.spm.stats.con.spmmat(1).tgt_spec{1}(1).name = 'filter';"
    echo "matlabbatch{$J}.spm.stats.con.spmmat(1).tgt_spec{1}(1).value = 'mat';"
    echo "matlabbatch{$J}.spm.stats.con.spmmat(1).tgt_spec{1}(2).name = 'strtype';"
    echo "matlabbatch{$J}.spm.stats.con.spmmat(1).tgt_spec{1}(2).value = 'e';"
    echo "matlabbatch{$J}.spm.stats.con.spmmat(1).sname = 'Model estimation: SPM.mat File';"
    echo "matlabbatch{$J}.spm.stats.con.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});"
    echo "matlabbatch{$J}.spm.stats.con.spmmat(1).src_output = substruct('.','spmmat');"
    
    C=1
    while read line; do
	cname=`echo $line | cut -f1 -d:`
	cvector=`echo $line | cut -f2 -d:`
	echo "matlabbatch{$J}.spm.stats.con.consess{$C}.tcon.name = '${cname}';"
	echo "matlabbatch{$J}.spm.stats.con.consess{$C}.tcon.convec = [${cvector}];"
	echo "matlabbatch{$J}.spm.stats.con.consess{$C}.tcon.sessrep = '${CONTRAST_MANAGEMENT}';"
	C=$((C+1))
	
    done < ${c_file}
    echo "matlabbatch{$J}.spm.stats.con.delete = 1;"
    
    J=$((J+1))
    cd ../
done

