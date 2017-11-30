#!/bin/bash
# ------------------------------------------------------------------ #
# GENERATE-PREPROCESSING
# ------------------------------------------------------------------ #
# Generates a preprocessing SPM/Matlab script, which is output on
# the terminal and can be saved on a .m file.
# ------------------------------------------------------------------
# Usage
# -----
#
#   $ generate-preprocessing.sh [param file] <subj1> <subj2>...<subjN>
#
# Where:
#   
#   [param file] is an optional parameter file (see below);
#   <subjX> is the name of a subject's data directory.
# 
# Parameter File
# --------------
# A parameter file is a text file that contains preprocessing 
# parameters, one per line, in the form <PARAM> = <VALUE>. The 
# following parameters are supported:
# 
#   * TR: the repetition time.  By default, TR = 2.
#
#   * NUM_SLICES: the number of horizontal slices. By default,
#     NUM_SLICES = 36.
#
#   * TA: time from first to last slice. If not specified, it
#     is calculated as TR-TR/NUM_SLICES
#
#   * SLICE_ORDER: The order of slices, from bottom to top. If 
#     not specified, it is calculated as 1:1:SLICE_ORDER. 
#
#   * REFERENCE_SLICE: The reference slice for slice-timing. By 
#     default, REFERENCE_SLICE = 1.
# 
#   * FUNC_FOLDER: The name of the folder where the raw 
#     functional data is stored. By default, FUNC_FOLDER = raw.
#
#   * STRUCT_FOLDER: The name of the folder where the structural
#     images are stored. By default, STRUCT_FOLDER = struct
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
#  3. The raw data is located in the "raw" subfolder, and 
#    stored as 4D nifti files.
#
#  5. The structural data is located in the "struct" subfolder
# ------------------------------------------------------------------ #
#
# History
# -------
#  2017-11-28 : * Replaced FSLInfo with custom-made niftidims.py
#
#  2017-11-25 : * Implemented a new way to read the number of volumes
#             :   In a 4D nifti file (based on FSLinfo).
#
#  2015-06-30 : * Fixed a line of code that was not compatible with
#             :   new release of SPM8 
#  
#  2013-08-08 : * Modified to include error ouput on the console
#             :   (as stderr).
#             : * Modified the reading of parameters from the param
#             :   file, to make sure that only word-params are read
#             :   (and not strings that are part of other param 
#             :   names)
#
#  2013-08-06 : * Modified to include an initial parameter file
# 
#  2013-07-23 : * First version working
#
#  2013-07-22 : * File started.
# ------------------------------------------------------------------ #
# To-do's:                                                           
#                                                                    
#  * 
# ------------------------------------------------------------------ #

HLP_MSG="\n
  Usage                                                             \n
  -----                                                             \n
                                                                    \n
    $ $0 [pfile] <subj1> <subj2>...<subjN>                          \n
                                                                    \n
  Where:                                                            \n
                                                                    \n
    [pfile] is an optional parameter file (see below);              \n
    <subjX> is the name of a subject data directory.                \n
                                                                    \n
  Parameter File                                                    \n
  --------------                                                    \n
  A parameter file is a text file that contains preprocessing       \n
  parameters, one per line, in the form <PARAM> = <VALUE>. The      \n
  following parameters are supported:                               \n
                                                                    \n
    1. TR: the repetition time.  By default, TR = 2.                \n
                                                                    \n
    2. NUM_SLICES: the number of horizontal slices. By default,     \n
      NUM_SLICES = 36.                                              \n
                                                                    \n
    3. TA: time from first to last slice. If not specified, it      \n
      is calculated as TR-TR/NUM_SLICES                             \n
                                                                    \n
    4. SLICE_ORDER: The order of slices, from bottom to top. If     \n
      not specified, it is calculated as 1:1:SLICE_ORDER.           \n
                                                                    \n
    5. REFERENCE_SLICE: The reference slice for slice-timing. By    \n
     default, REFERENCE_SLICE = 1.                                  \n
                                                                    \n
    8.  FUNC_FOLDER: The name of the folder where the raw           \n
     functional data is stored. By default, FUNC_FOLDER = raw.      \n
                                                                    \n
    7. STRUCT_FOLDER: The name of the folder where the structural   \n
     images are stored. By default, STRUCT_FOLDER = struct          \n
"

J=1
base=`pwd`

if [ "$#" -lt 1 ]; then
    echo -e $HLP_MSG
    exit
fi

TR=2
NUM_SLICES=36
TA="${TR}-${TR}/${NUM_SLICES}"
SLICE_ORDER="1:1:${NUM_SLICES}"
REFERENCE_SLICE=1
FUNC_FOLDER=raw
STRUCT_FOLDER=struct

if [ -f $1 ]; then
    param_file=$1
    echo "Found parameter file: '$param_file'" >&2
    # If the first argument is a file, it must be a parameter file
    if grep -q "^TR" $param_file; then
	TR=`grep "^TR" ${param_file} | cut -f2 -d= | tail -1 | tr -d ' '`
	echo "  Setting parameter TR = $TR" >&2
    fi

    if grep -q "^NUM_SLICES" $param_file; then
	NUM_SLICES=`grep "^NUM_SLICES" ${param_file} | cut -f2 -d= | tail -1 | tr -d ' '`
	echo "  Setting parameter NUM_SLICES = $NUM_SLICES" >&2
    fi
    
    if grep -q "^TA" $param_file; then
	TA=`grep "^TA" ${param_file} | cut -f2 -d= | tail -1 | tr -d ' '`
	echo "  Setting parameter TA = $TA" >&2
    else
	TA="${TR}-${TR}/${NUM_SLICES}"
	echo "  Recalculating parameter TA = $TA" >&2
    fi

    if grep -q "^SLICE_ORDER" $param_file; then
	SLICE_ORDER=`grep "^SLICE_ORDER" ${param_file} | cut -f2 -d= | tail -1 | tr -d ' '`
	echo "  Setting parameter SLICE_ORDER = $SLICE_ORDER" >&2
    fi

    if grep -q "^REFERENCE_SLICE" $param_file; then
	REFERENCE_SLICE=`grep "^REFERENCE_SLICE" ${param_file} | cut -f2 -d= | tail -1 | tr -d ' '`
	echo "  Setting parameter REFERENCE_SLICE = $REFERENCE_SLICE" >&2
    fi

    if grep -q "^FUNC_FOLDER" $param_file; then
	FUNC_FOLDER=`grep "^FUNC_FOLDER" ${param_file} | cut -f2 -d= | tail -1 | tr -d ' '`
	echo "  Setting parameter FUNC_FOLDER = $FUNC_FOLDER" >&2
    fi

    if grep -q "^STRUCT_FOLDER" $param_file; then
	STRUCT_FOLDER=`grep "^STRUCT_FOLDER" ${param_file} | cut -f2 -d= | tail -1 | tr -d ' '`
	echo "  Setting parameter STRUCT_FOLDER = $STRUCT_FOLDER" >&2
    fi

    # Finally, skip the first argument
    shift
fi

# ================================================================== #
# PROCESSING EACH SUBJECT
# ================================================================== #

for subj in $@; do

    # Part 1: Time slice correction

    echo "matlabbatch{$J}.spm.temporal.st.scans = {"
    cd ${subj}/${FUNC_FOLDER}
    echo `pwd` >&2
    # Find the number of sessions
    num_sess=`ls ${subj}[-_]*.nii | wc | awk '{print $1}'`
    if [ $num_sess -eq 0 ]; then
	echo "** Error ** No sessions found for subject ${subj} folder ${FUNCT_FOLDER}" >&2
    else
	echo "Found $num_sess sessions for subject ${subj}" >&2
    fi

    for session in ${subj}[-_]*.nii; do
	echo "% Session $session"
	echo "{"
	#N=`echo $session | cut -f1 -d. | tail -c 4`
	#N=$(#echo $N | sed 's/^0*//')  # Removes leading zeroes
	#N=`fslinfo $session | grep "^dim4" | awk '{print $2}'`
	N=`niftidims.py $session | awk '{print $4}'`
	#echo "N=$N" >&2
	for ((image=1; image<N; ++image)); do 
	    echo "'${base}/${subj}/${FUNC_FOLDER}/${session},${image}'"
	done
	echo "}"
    done
    echo "};"

    # The slice timing correction parameters

    echo "matlabbatch{$J}.spm.temporal.st.nslices = ${NUM_SLICES};"
    echo "matlabbatch{$J}.spm.temporal.st.tr = ${TR};"
    echo "matlabbatch{$J}.spm.temporal.st.ta = ${TA};"
    echo "matlabbatch{$J}.spm.temporal.st.so = [${SLICE_ORDER}];"
    echo "matlabbatch{$J}.spm.temporal.st.refslice = ${REFERENCE_SLICE};"
    echo "matlabbatch{$J}.spm.temporal.st.prefix = 'a';"
    
    J=$((J+1))
    echo -e "\n%% Realignment\n"

    S=1
    for session in ${subj}[-_]*.nii; do
	echo "% Session $S $session"
	echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1) = cfg_dep;"
	echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1).tname = 'Session';"
	echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1).tgt_spec{1}(1).name = 'filter';"
	echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1).tgt_spec{1}(1).value = 'image';"
	echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1).tgt_spec{1}(2).name = 'strtype';"
	echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1).tgt_spec{1}(2).value = 'e';"
	echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1).sname = 'Slice Timing: Slice Timing Corr. Images (Sess ${S})';"
	echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});"
	echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1).src_output = substruct('()',{$S}, '.','files');"
	
	#echo "matlabbatch{$J}.spm.spatial.realign.estwrite.data{$S}(1) = cfg_dep;"
	
	S=$((S+1))
    done

    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.eoptions.quality = 0.9;"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.eoptions.sep = 4;"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.eoptions.fwhm = 5;"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.eoptions.rtm = 1;"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.eoptions.interp = 2;"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.eoptions.wrap = [0 0 0];"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.eoptions.weight = '';"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.roptions.which = [0 1];"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.roptions.interp = 4;"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.roptions.wrap = [0 0 0];"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.roptions.mask = 1;"
    echo "matlabbatch{$J}.spm.spatial.realign.estwrite.roptions.prefix = 'r';"

    J=$((J+1))
    echo -e "\n% Coregistration\n"

    cd ../${STRUCT_FOLDER};
    struct=`ls ${subj}*.nii`

    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.ref(1) = cfg_dep;"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.ref(1).tname = 'Reference Image';"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.ref(1).tgt_spec{1}(1).name = 'filter';"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.ref(1).tgt_spec{1}(1).value = 'image';"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.ref(1).tgt_spec{1}(2).name = 'strtype';"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.ref(1).tgt_spec{1}(2).value = 'e';"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.ref(1).sname = 'Realign: Estimate & Reslice: Mean Image';"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.ref(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1});"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.ref(1).src_output = substruct('.','rmean');"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.source = {'${base}/${subj}/${STRUCT_FOLDER}/${struct},1'};"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.other = {''};"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.eoptions.cost_fun = 'nmi';"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.eoptions.sep = [4 2];"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.eoptions.fwhm = [7 7];"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.roptions.interp = 1;"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.roptions.wrap = [0 0 0];"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.roptions.mask = 0;"
    echo "matlabbatch{$J}.spm.spatial.coreg.estwrite.roptions.prefix = 'r';"

    J=$((J+1))

    echo -e "\n% Normalise: Estimate\n"

    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.source(1) = cfg_dep;"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.source(1).tname = 'Source Image';"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.source(1).tgt_spec{1}(1).name = 'filter';"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.source(1).tgt_spec{1}(1).value = 'image';"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.source(1).tgt_spec{1}(2).name = 'strtype';"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.source(1).tgt_spec{1}(2).value = 'e';"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.source(1).sname = 'Coregister: Estimate & Reslice: Resliced Images';"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.source(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1});"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.source(1).src_output = substruct('.','rfiles');"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.subj.wtsrc = '';"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.eoptions.template = {'/usr/local/var/spm8/templates/T1.nii,1'};"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.eoptions.weight = '';"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.eoptions.smosrc = 8;"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.eoptions.smoref = 0;"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.eoptions.regtype = 'mni';"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.eoptions.cutoff = 25;"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.eoptions.nits = 16;"
    echo "matlabbatch{$J}.spm.spatial.normalise.est.eoptions.reg = 1;"

    J=$((J+1))
    
    echo -e "\n% Normalize: Write\n"

    cd ../${FUNC_FOLDER};
    S=1
    for session in ${subj}[-_]*.nii; do
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).matname(1) = cfg_dep;"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).matname(1).tname = 'Parameter File';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).matname(1).tgt_spec{1}(1).name = 'filter';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).matname(1).tgt_spec{1}(1).value = 'mat';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).matname(1).tgt_spec{1}(2).name = 'strtype';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).matname(1).tgt_spec{1}(2).value = 'e';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).matname(1).sname = 'Normalise: Estimate: Norm Params File (Subj 1)';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).matname(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1});"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).matname(1).src_output = substruct('()',{1}, '.','params');"
	
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).resample(1) = cfg_dep;"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).resample(1).tname = 'Images to Write';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).resample(1).tgt_spec{1}(1).name = 'filter';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).resample(1).tgt_spec{1}(1).value = 'image';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).resample(1).tgt_spec{1}(2).name = 'strtype';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).resample(1).tgt_spec{1}(2).value = 'e';"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).resample(1).sname = 'Realign: Estimate & Reslice: Realigned Images (Sess $S)';"

	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).resample(1).src_exbranch = substruct('.','val', '{}',{$((J-3))}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1});"
	echo "matlabbatch{$J}.spm.spatial.normalise.write.subj($S).resample(1).src_output = substruct('.','sess', '()',{$S}, '.','cfiles');"
	S=$((S+1))
    done

    echo "matlabbatch{$J}.spm.spatial.normalise.write.roptions.preserve = 0;"
    echo "matlabbatch{$J}.spm.spatial.normalise.write.roptions.bb = [-78 -112 -50;"
    echo "                                                          78 76 85];"
    echo "matlabbatch{$J}.spm.spatial.normalise.write.roptions.vox = [2 2 2];"
    echo "matlabbatch{$J}.spm.spatial.normalise.write.roptions.interp = 1;"
    echo "matlabbatch{$J}.spm.spatial.normalise.write.roptions.wrap = [0 0 0];"
    echo "matlabbatch{$J}.spm.spatial.normalise.write.roptions.prefix = 'w';"

    J=$((J+1))

    echo -e "\n% Smoothing\n"
    
    S=1
    for session in ${subj}*.nii; do

	echo "matlabbatch{$J}.spm.spatial.smooth.data(1) = cfg_dep;"
	echo "matlabbatch{$J}.spm.spatial.smooth.data(1).tname = 'Images to Smooth';"
	echo "matlabbatch{$J}.spm.spatial.smooth.data(1).tgt_spec{1}(1).name = 'filter';"
	echo "matlabbatch{$J}.spm.spatial.smooth.data(1).tgt_spec{1}(1).value = 'image';"
	echo "matlabbatch{$J}.spm.spatial.smooth.data(1).tgt_spec{1}(2).name = 'strtype';"
	echo "matlabbatch{$J}.spm.spatial.smooth.data(1).tgt_spec{1}(2).value = 'e';"
	echo "matlabbatch{$J}.spm.spatial.smooth.data(1).sname = 'Normalise: Write: Normalised Images (Subj $S)';"
	echo "matlabbatch{$J}.spm.spatial.smooth.data(1).src_exbranch = substruct('.','val', '{}',{$((J-S))}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1});"
	echo "matlabbatch{$J}.spm.spatial.smooth.data(1).src_output = substruct('()',{$S}, '.','files');"
	echo "matlabbatch{$J}.spm.spatial.smooth.fwhm = [8 8 8];"
	echo "matlabbatch{$J}.spm.spatial.smooth.dtype = 0;"
	echo "matlabbatch{$J}.spm.spatial.smooth.im = 0;"
	echo "matlabbatch{$J}.spm.spatial.smooth.prefix = 's';"
	S=$((S+1))
	J=$((J+1))
    done
    
    # Exit the subject's FUNCT_FOLDER folder, goes back to base
    cd ../..
done

