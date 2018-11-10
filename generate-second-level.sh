#!/bin/bash
# ------------------------------------------------------------------ #
# GENERATE-SECOND-LEVEL
# ------------------------------------------------------------------ #
# Generates an SPM batch script for performing group analysis.
# ------------------------------------------------------------------ #
#
# Usage
# -----
#
#   $ generate-second-level.sh <subj_results_dir> <group_results_dir>
#                              <contrast_file> <subjects_file>
#
# Where:
#   
#   <subj_results_dir> is the name of the folder where the SPM.mat 
#                      file will be placed for each subject (it 
#                      needs to already exist)
#   <group_results_dir> is the name of the folder where the group 
#                       analysis and each contrast's SPM.mat file 
#                       will be placed. It will be created (together
#                       with the appropriate sub-folders) if it does
#                       not exist.
#   <contrast_file> is a file listing all the contrast names and their
#                   vectors, separated by ":" 
#   <subjects_file> is the name of a file containining the list of subjects
#                   and a group identifier for each of them.
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
# The script assumes that the same contrast vector is used for
# each session, and will use SPM's "Replicate&Scale" option when
# generating the contrasts. In some studies, this is not the case,
# so the script cannot be used.
#
# Subjects File
# -------------
# A subjects file is a text file that contains two columns: the 
# list of subjects ID (corresponding to the subjects' data 
# folders) and the group they belong to. One group must always
# be specified, even as a placeholder (e.g., '1' or 'x'). If
# two groups are indicated, the script will model all the
# contrasts within each group, as well as all the group 
# comparsisons within each contrast. A subject file might 
# look like this:
#  
#   11011   Bilingual
#   11012   Monolingual
#   11015   Bilingual
#   ...     ...
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
#  2018-11-10 : * Adapted to handle *.nii nifti files (new standard
#             :   in SPM12).
#
#  2014-05-13 : * File created, as a fork of previous script
#             :   called generate-group-analysis
#
#  2013-07-25 : * Script working and stable.
#
#  2013-07-22 : * File created as generate-group-analysis.
# ------------------------------------------------------------------ #

HLP_MSG="
 Usage
 -----

   $ generate-second-level.sh <subj_results_dir> <group_results_dir>
                              <contrast_file> <subjects_file>

 Where:
   
   <subj_results_dir> is the name of the folder where the SPM.mat 
                      file will be placed for each subject (it 
                      needs to already exist)
   <group_results_dir> is the name of the folder where the group 
                       analysis and each contrast's SPM.mat file 
                       will be placed. It will be created (together
                       with the appropriate sub-folders) if it does
                       not exist.
   <contrast_file> is a file listing all the contrast names and their
                   vectors, separated by ":" 
   <subjects_file> is the name of a file containining the list of subjects
                   and a group identifier for each of them.
 
 Contrast File
 --------------
 A contrast file is a text file that contains contrast names and 
 vector values, one per line, in the form <NAME> : <VECTOR>. For 
 example:
 
   Words > Pictures : 0 0 -0.5 -0.5 0 0.5 0.5 
   Pictures > Words : 0 0 0.5 0.5 0 -0.5 -0.5 
   ....

 The script assumes that the same contrast vector is used for
 each session, and will use SPM's 'Replicate&Scale' option when
 generating the contrasts. In some studies, this is not the case,
 so the script cannot be used.

 Subjects File
 -------------
 A subjects file is a text file that contains two columns: the 
 list of subjects ID (corresponding to the subjects' data 
 folders) and the group they belong to. One group must always
 be specified, even as a placeholder (e.g., '1' or 'x'). If
 two groups are indicated, the script will model all the
 contrasts within each group, as well as all the group 
 comparsisons within each contrast. A subject file might 
 look like this:
  
   11011   Bilingual
   11012   Monolingual
   11015   Bilingual
   ...     ...
 
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

   $ generate-second-level.sh <subj_results_dir> <group_results_dir>
                              <contrast_file> <subjects_file>

"

## ---------------------------------------------------------------- ##
## GENERAL VARIABLES
## ---------------------------------------------------------------- ##
J=0
DIR=`pwd`
#M="${DIR}/group-analysis.m"
#echo "%% Starting... " > ${M}

L1_RESULTS_FOLDER=$1
L2_RESULTS_FOLDER=$2
CONTRAST_FILE=$3      # Contrast file
GROUP_FILE=$4         # Group file

GMS=1 # 1 = No GMS, 2 = proportional, 3 = ANCOVA
VAR=1 # 0 = Equal variance, 1 = unequal variance

if [ $# -ne 4 ]; then
    IFS=''
    echo -e $HLP_MSG >&2
    unset IFS
    exit
fi

#GROUPS=`awk '{print $2}' ${GROUP_FILE} | sort | uniq`
#echo $GROUPS, $GROUP_FILE
if [ ! -d ${DIR}/${L2_RESULTS_FOLDER} ]; then
    echo "Warning: Creating '${L2_RESULTS_FOLDER}' folder" >&2
    /bin/mkdir ${L2_RESULTS_FOLDER}
fi

# --------------------------------------------------------------------
# Part 1 --- Full analysis with all subjects 
# --------------------------------------------------------------------

if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/all ]; then
    echo "Warning: Creating 'all' folder" >&2
    cd ${L2_RESULTS_FOLDER}
    mkdir all
    cd ..
fi

# Reset the contrast counter
C=0


while read contrast; do
    # Generates a different subfolder for each contrast
    C=$((C+1))
    contrast_name=`echo $contrast | cut -f1 -d':'`
    contrast_name=`echo ${contrast_name}`
    contrast_dir=${contrast_name// /_}     # Subtitute spaces with '_'
    if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/all/${contrast_dir} ]; then
	echo "Warning: Creating '${contrast_dir}' folder"  >&2
	cd ${L2_RESULTS_FOLDER}/all
	mkdir ${contrast_dir}
	cd ../..
    fi

    J=$((J+1))

    echo "matlabbatch{${J}}.spm.stats.factorial_design.dir = {'${DIR}/${L2_RESULTS_FOLDER}/all/${contrast_dir}/'};" 
    echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t1.scans = {" 
    
    while read subject; do
	subject_folder=`echo $subject | awk '{print $1}'`
	contrast_file=con_`printf "%04d" ${C}`
	
	if [ ! -e ${DIR}/${subject_folder}/do-not-include.txt ]; then
	    if [ -e ${DIR}/${subject_folder}/${L1_RESULTS_FOLDER}/${contrast_file}.img ]; then
		echo "'${DIR}/${subject_folder}/${L1_RESULTS_FOLDER}/${contrast_file}.img,1'"
	    elif [ -e ${DIR}/${subject_folder}/${L1_RESULTS_FOLDER}/${contrast_file}.nii ]; then
		echo "'${DIR}/${subject_folder}/${L1_RESULTS_FOLDER}/${contrast_file}.nii,1'"
	    else
		echo "No contrast file ${contrast_file} for ${subject_folder}: Subject excluded" >&2
	    fi
	else
	    echo "Excluding subject ${subject_folder} (do-not-include file found)"  >&2
	fi
    done < ${GROUP_FILE}
    
    echo "};" 
    
    echo "matlabbatch{${J}}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});" 
    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.tm.tm_none = 1;" 
    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.im = 1;" 
    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.em = {''};" 
    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalc.g_omit = 1;" 
    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;" 
    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.glonorm = ${GMS};" 

    # ----------------------------------------------------------------
    # Estimate the Group-Level Contrast
    # ----------------------------------------------------------------
    
    J=$((J+1))
    
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1) = cfg_dep;" 
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tname = 'Select SPM.mat';" 
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).name = 'filter';" 
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).value = 'mat';" 
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).name = 'strtype';" 
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).value = 'e';" 
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).sname = 'Factorial design specification: SPM.mat File';" 
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" 
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_output = substruct('.','spmmat');" 
    echo "matlabbatch{${J}}.spm.stats.fmri_est.method.Classical = 1;" 

    # ----------------------------------------------------------------
    # Create the "Contrast" (A simple '1' vector)
    # ----------------------------------------------------------------

    J=$((J+1))

    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1) = cfg_dep;" 
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tname = 'Select SPM.mat';" 
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).name = 'filter';" 
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).value = 'mat';" 
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).name = 'strtype';" 
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).value = 'e';" 
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).sname = 'Model estimation: SPM.mat File';" 
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" 
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_output = substruct('.','spmmat');" 
    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.name = '${contrast_name}';" 
    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.convec = 1;" 
    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.sessrep = 'none';" 
    echo "matlabbatch{${J}}.spm.stats.con.delete = 1;" 
done < ${CONTRAST_FILE}

# --------------------------------------------------------------------
# Part 2 --- Analysis of the two groups, separately
# --------------------------------------------------------------------
# This part of the analysis is performed IFF there are at least two
# groups in the 'groups' file.
# -------------------------------------------------------------------- 

# Calculate the number of groups.  There should only be two.
# (this is contrieved but I couldn't make it work with the classic
# ${#array[@]} trick...)

N=`awk '{print $2}' ${GROUP_FILE} | sort | uniq | wc | awk '{print $1}'`

if [ $N == 2 ]; then
    # If we have at least two groups, we need to create individual
    # analysis
    
    for group in `awk '{print $2}' ${GROUP_FILE} | sort | uniq`; do
	if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/${group} ]; then
	    echo "Creating folder for group '${group}'"  >&2
	    cd ${L2_RESULTS_FOLDER}
	    mkdir ${group}
	    cd ..
	fi
	C=0
	while read contrast; do
            # Generates a different subfolder for each contrast
	    C=$((C+1))
	    contrast_name=`echo $contrast | cut -f1 -d':'`
	    contrast_name=`echo ${contrast_name}`
	    contrast_dir=${contrast_name// /_}     # Subtitute spaces with '_'
	    contrast_file=con_`printf "%04d" ${C}`

	    if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/${group}/${contrast_dir} ]; then
		echo "Warning: Creating '${contrast_dir}' folder" >&2
		cd ${L2_RESULTS_FOLDER}/${group}
		mkdir ${contrast_dir}
		cd ../..
	    fi

	    J=$((J+1))

	    echo "matlabbatch{${J}}.spm.stats.factorial_design.dir = {'${DIR}/${L2_RESULTS_FOLDER}/${group}/${contrast_dir}/'};" 
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t1.scans = {" 
    
	    for subject in `grep ${group} ${GROUP_FILE} | awk '{print $1}'`; do
		#echo "   $subject"
		if [ ! -e ${DIR}/${subject}/do-not-include.txt ]; then
		    if [ -e ${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file}.img ]; then
			# This handles Analyze format / SPM5-8
			echo "'${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file}.img,1'"
			
		    elif [ -e ${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file}.nii} ]; then
			# This handles Nifti format / SPM12
			echo "'${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file}.nii,1'"

		    else
			echo "No contrast file ${contrast_file} for ${subject}: Subject excluded" >&2
		    fi
		else
		    echo "Excluding subject ${subject} (do-not-include file found)" >&2
		fi
	    done
    
	    echo "};" 
    
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});" 
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.tm.tm_none = 1;" 
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.im = 1;" 
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.em = {''};" 
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalc.g_omit = 1;" 
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;" 
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.glonorm = ${GMS};" 
	    
            # ----------------------------------------------------------------
            # Estimate the Group-Level Contrast
            # ----------------------------------------------------------------
    
	    J=$((J+1))
    
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1) = cfg_dep;" 
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tname = 'Select SPM.mat';" 
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).name = 'filter';" 
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).value = 'mat';" 
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).name = 'strtype';" 
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).value = 'e';" 
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).sname = 'Factorial design specification: SPM.mat File';" 
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" 
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_output = substruct('.','spmmat');" 
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.method.Classical = 1;" 
	    
            # ----------------------------------------------------------------
            # Create the "Contrast" (A simple '1' vector)
            # ----------------------------------------------------------------

	    J=$((J+1))
	    
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1) = cfg_dep;" 
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tname = 'Select SPM.mat';" 
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).name = 'filter';" 
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).value = 'mat';" 
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).name = 'strtype';" 
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).value = 'e';" 
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).sname = 'Model estimation: SPM.mat File';" 
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" 
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_output = substruct('.','spmmat');" 
	    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.name = '${contrast_name}';" 
	    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.convec = 1;" 
	    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.sessrep = 'none';" 
	    echo "matlabbatch{${J}}.spm.stats.con.delete = 1;" 
	done < ${CONTRAST_FILE}
    done
fi

## -------------------------------------------------------------------
## PART 3: GROUP COMPARISONS
## -------------------------------------------------------------------

if [ $N == 2 ]; then
    if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/comparisons ]; then
	echo "Warning: Creating 'comparisons' directory" >&2
	cd ${L2_RESULTS_FOLDER}
	mkdir comparisons
	cd ..
    fi

    # Ideally, these two should be identified at the very beginning of the
    # file to avoid inconsistencies if the file is rewritten during
    # the execution of the script.

    group1=`awk '{print $2}' ${GROUP_FILE} | sort | uniq | head -1`
    group2=`awk '{print $2}' ${GROUP_FILE} | sort | uniq | tail -1`

    # Reset contrast counter
    C=0

    while read contrast; do
        # Generates a different subfolder for each contrast
	C=$((C+1))
	contrast_name=`echo $contrast | cut -f1 -d':'`
	contrast_name=`echo ${contrast_name}`
	contrast_dir=${contrast_name// /_}     # Subtitute spaces with '_'
	contrast_file=con_`printf "%04d" ${C}`

	if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/comparisons/${contrast_dir} ]; then
	    echo "Warning: Creating '${contrast_dir}' folder" >&2
	    cd ${L2_RESULTS_FOLDER}/comparisons
	    mkdir ${contrast_dir}
	    cd ../..
	fi

	J=$((J+1))

    
	echo "matlabbatch{${J}}.spm.stats.factorial_design.dir = {'${DIR}/${L2_RESULTS_FOLDER}/comparisons/${contrast_dir}'};" 

	# ------------------------------------------------------------
	# Group 1
	# ------------------------------------------------------------

	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.scans1 = {" 
	
	for subject in `grep ${group1} ${GROUP_FILE} | awk '{print $1}'`; do
	    if [ ! -e ${DIR}/${subject}/do-not-include.txt ]; then
		if [ -e ${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file}.img ]; then
		    echo "'${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file}.img,1'"
		elif [ -e ${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file}.nii ]; then
		    echo "'${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file}.nii,1'"
		else
		    echo "No contrast file ${contrast_file} for ${subject}: Subject excluded" >&2
		fi
	    else
		echo "Excluding subject ${subject} (do-not-include file found)"
	    fi
	done
        echo "};" 

	# ------------------------------------------------------------
	# Group 2
	# ------------------------------------------------------------
	
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.scans2 = {" 
	
	for subject in `grep ${group2} ${GROUP_FILE} | awk '{print $1}'`; do
	    if [ ! -e ${DIR}/${subject}/do-not-include.txt ]; then
		if [ -e ${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file} ]; then
		    echo "'${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file},1'" 
		else
		    echo "No contrast file ${contrast_file} for ${subject}: Subject excluded"  >&2
		fi
	    else
		echo "Excluding subject ${subject} (do-not-include file found)" >&2
	    fi
	done
        echo "};" 
        
	
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.dept = 0;" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.variance = ${VAR};" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.gmsca = 0;" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.ancova = 0;" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.tm.tm_none = 1;" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.im = 1;" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.em = {''};" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.globalc.g_omit = 1;" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;" 
	echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.glonorm = ${GMS};" 

	J=$((J+1))

	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1) = cfg_dep;" 
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tname = 'Select SPM.mat';" 
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).name = 'filter';" 
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).value = 'mat';" 
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).name = 'strtype';" 
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).value = 'e';" 
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).sname = 'Factorial design specification: SPM.mat File';" 
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" 
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_output = substruct('.','spmmat');" 
	echo "matlabbatch{${J}}.spm.stats.fmri_est.method.Classical = 1;" 

	J=$((J+1))

	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1) = cfg_dep;" 
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tname = 'Select SPM.mat';" 
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).name = 'filter';" 
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).value = 'mat';" 
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).name = 'strtype';" 
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).value = 'e';" 
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).sname = 'Model estimation: SPM.mat File';" 
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" 
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_output = substruct('.','spmmat');" 
	echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.name = '${group1} > ${group2}';" 
	echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.convec = [1 -1];" 
	echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.sessrep = 'none';" 
	echo "matlabbatch{${J}}.spm.stats.con.consess{2}.tcon.name = '${group2} > ${group1}';" 
	echo "matlabbatch{${J}}.spm.stats.con.consess{2}.tcon.convec = [-1 1];" 
	echo "matlabbatch{${J}}.spm.stats.con.consess{2}.tcon.sessrep = 'none';" 
	echo "matlabbatch{${J}}.spm.stats.con.delete = 0;" 
    done < ${CONTRAST_FILE}
fi

if [ $N != 2 ]; then
    # If there were more than two groups, then we have only two options:
    # Either we don't have between-group designs (in which case, we exit)
    # or we have more than two groups (in which case, right now, we
    # cannot really do much)
    if [ $N == 1 ]; then
	echo "Only one group found: No group comparisons will be generated" >&2
    else
	echo "Three or more groups found. Cannot do analysis (${GROUPS})." >&2
    fi
fi
