#!/bin/bash
# ------------------------------------------------------------------ #
# GENERATE-CORRELATION-ANALYSIS
# ------------------------------------------------------------------ #
# Generates an SPM batch script for performing individual differences
# analysis across subjects.
# ------------------------------------------------------------------ #
#
# Usage
# -----
#
#   $ generate-correlation-analysis.sh <subj_results_dir> 
#                                      <group_results_dir>
#                                      <contrast_file>
#                                      <subjects_file>
#                                      <measures_file>
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
#   <subjects_file> is a file listing all the subjects used in the
#                   analysis.
#   <measures_file> is the name of a file containining the list of 
#                   subjects and a list of individual measures for 
#                   each of them. It can contain more subjects that 
#                   those listed in the subjects file. The measure
#                   file must have column names, and the first column
#                   must be the subject ID.
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
# Measures file
# -------------
# A measures file is a file that contains a set of individual
# measures for each participant. These measures will be used as
# covariates against fMRI data in a linear regression analysis.
# Each measure needs to be a number (obviously), and needs to
# be separated by spaces.
# The file is organized as a named matrix (something like a 
# 'dataframe' in R), where each colum represents a variable and 
# each row represents a subject. The first row must contain the
# column names. Finally, the first column MUST contain the subject
# names.  For example:
#
#   Subject IQ   OpSpan ReadSpan
#   11011   200  29     34
#   11012   150  70     48
#   11015   100  68     68
#   ...     ...  ...    ...
#
# ------------------------------------------------------------------ #
# History
# -------
#
#  2015-07-22 : * Extended the script to create summary PS files 
#                 with glass brains of the results.
#
#  2014-07-24 : * File created, as a fork of the old script 
#             :   called generate-group-analysis
#
# ------------------------------------------------------------------ #

B=`tput bold`
UB=`tput sgr0`
HLP_MSG="
${B}Usage${UB}
-----

  $ generate-correlation-analysis.sh <subj_results_dir> 
                                     <group_results_dir>
                                     <contrast_file>
                                     <subjects_file>
                                     <measures_file>
Where:
  
  ${B}subj_results_dir${UB} is the name of the folder where the SPM.mat 
                     file will be placed for each subject (it 
                     needs to already exist)
  ${B}group_results_dir${UB} is the name of the folder where the group 
                      analysis and each contrast's SPM.mat file 
                      will be placed. It will be created (together
                      with the appropriate sub-folders) if it does
                      not exist.
  ${B}contrast_file${UB} is a file listing all the contrast names and their
                  vectors, separated by ":" 
  ${B}subjects_file${UB} is a file listing all the subjects used in the
                  analysis.
  ${B}measures_file${UB} is the name of a file containining the list of 
                  subjects and a list of individual measures for 
                  each of them. It can contain more subjects that 
                  those listed in the subjects file. The measure
                  file must have column names, and the first column
                  must be the subject ID.

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

Measures file
-------------
A measures file is a file that contains a set of individual
measures for each participant. These measures will be used as
covariates against fMRI data in a linear regression analysis.
Each measure needs to be a number (obviously), and needs to
be separated by spaces.
The file is organized as a named matrix (something like a 
'dataframe' in R), where each colum represents a variable and 
each row represents a subject. The first row must contain the
column names. Finally, the first column MUST contain the subject
names.  For example:

  Subject IQ   OpSpan ReadSpan
  11011   200  29     34
  11012   150  70     48
  11015   100  68     68
  ...     ...  ...    ...

Summary
-------

  $ generate-correlation-analysis.sh <subj_results_dir> 
                                     <group_results_dir>
                                     <contrast_file>
                                     <subjects_file>
                                     <measures_file>
"

# ------------------------------------------------------------------ #
# SETUP
# ------------------------------------------------------------------ #

L1_RESULTS_FOLDER=$1
L2_RESULTS_FOLDER=$2
CONTRAST_FILE=$3      # Contrast file
SUBJECTS_FILE=$4
MEASURES_FILE=$5      # Measures file

if [ $# -ne 5 ]; then
    IFS=''
    echo -e $HLP_MSG >&2
    unset IFS
    exit
fi

J=0
C=0
DIR=`pwd`
VARIABLES=`head -1 $MEASURES_FILE`
VARIABLES=(${VARIABLES})

# ------------------------------------------------------------------ #
# CREATING THE BATCH FILE
# ------------------------------------------------------------------ #

if [ ! -d ${DIR}/${L2_RESULTS_FOLDER} ]; then
    echo "Warning: Creating '${L2_RESULTS_FOLDER}' folder" >&2
    /bin/mkdir ${L2_RESULTS_FOLDER}
fi

while read contrast; do
         
    # Generates a different subfolder for each contrast
    C=$((C+1))
    contrast_name=`echo $contrast | cut -f1 -d':'`
    contrast_name=`echo ${contrast_name}`
    #echo "$contrast_name" >&2
    contrast_dir=${contrast_name// /_}     # Subtitute spaces with '_'
    if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/${contrast_dir} ]; then
	echo "Warning: Creating '${contrast_dir}' folder" >&2
	cd ${L2_RESULTS_FOLDER}
	mkdir ${contrast_dir}
	cd ..
    fi

    # Generates a different folder for each independent predictor. If there is more than
    # one variable, must also generate an "all_predictors" folder with multiple covariates.

    V=1   # The first entry is going to be the subject name, so that must not be counted

    for variable in "${VARIABLES[@]:1}"; do
	V=$((V+1))
	variable_name=`echo ${variable}`
	variable_dir=${variable_name// /_}                    # Subtitute spaces with '_'
	variable_dir="${contrast_dir}_and_${variable_dir}"     

	#echo "${DIR}/${L2_RESULTS_FOLDER}/${contrast_dir}/${variable_dir}" >&2
	if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/${contrast_dir}/${variable_dir} ]; then
	    echo "Warning: Creating '${variable_dir}' folder" >&2
	    cd ${L2_RESULTS_FOLDER}/${contrast_dir}
	    mkdir ${variable_dir}
	    cd ../..
	fi

	## -----------------------------------------------------------
	## 1. Generate the first part of the code, to set up 
	##    properly the regression.
	##    For each contrast and variable, we create a new 
	##    Factorial Design of type "Regression"
	## -----------------------------------------------------------

	J=$((J+1))
	
	echo "matlabbatch{${J}}.spm.stats.factorial_design.dir = {'${DIR}/${L2_RESULTS_FOLDER}/${contrast_dir}/${variable_dir}'};"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.mreg.scans = {"

	## -----------------------------------------------------------
	## 2. Here we list the scans for each subject specified in
	##    the subject file.  We also begin creating a new covariate
	##    vector, which is initially an empty string
	## -----------------------------------------------------------

	covariate="" # Empty covariate vector string

	while read subj; do
	    subject=`echo $subj | awk '{print $1}'`
	    #echo "------> Subject $subject" >&2
	    contrast_file=con_`printf "%04d" ${C}`.img

	    if [ ! -e ${DIR}/${subject}/do-not-include.txt ]; then
		if [ -e ${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file} ]; then
		    subj_measures_num=`grep "\b${subject}\b" $MEASURES_FILE | wc -l`
		    
		    if [ $subj_measures_num -eq 1 ]; then
			
			echo "'${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file},1'"
		    
		        ## Step 2.1
                        ## 2.1. While listing the scans, identify the value in MEASURES (index $V), and
	                ##       add it to a string that is progressively increased
			measure=`grep "\b${subject}\b" $MEASURES_FILE | tail -1 | awk -v x=${V} '{print $x}'`
			covariate="${covariate} ${measure}"

		    # Now some error messages if there are more or less measures than expected.
		    elif [ $subj_measures_num -eq 0 ]; then
			echo "No measures found for subject ${subject}: Skipping">&2
		    else
			echo "Multiple records found for subject ${subject}: Skipping">&2
		    fi
	       
		else
		    # If we don't have a contrast image for that subject, we skip
		    echo "No contrast file ${contrast_file} for ${subject_folder}: Subject excluded"
		fi
	    else
		# If there is a do-not-include.txt file, we skip.
		echo "Excluding subject ${subject_folder} (do-not-include file found)"
	    fi
	done < $SUBJECTS_FILE
	    
	echo "};"

	## 3. Add the string as a covariate.
	
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.mreg.mcov.c = [${covariate}];"

	## 4. And now, the rest of the Factorial Design Specification

	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.mreg.mcov.cname = '$variable';"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.mreg.mcov.iCC = 1;"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.mreg.incint = 1;"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.tm.tm_none = 1;"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.im = 1;"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.em = {''};"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.globalc.g_omit = 1;"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;"
	echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.glonorm = 1;"
	
	## -----------------------------------------------------------
	## MODEL ESTIMATION
	## -----------------------------------------------------------
	
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


	## -----------------------------------------------------------
	## CONTRAST MANAGER
	## -----------------------------------------------------------
	## For each regression, we need to create two contrasts, 
	## one for testing the positive regression and one for testing
	## the negative.
	## -----------------------------------------------------------

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
	
	echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.name = 'Pos corr btwn ${contrast_name} & ${variable}';"
	echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.convec = [0 1];"
	echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.sessrep = 'none';"
	echo "matlabbatch{${J}}.spm.stats.con.consess{2}.tcon.name = 'Neg corr btwn ${contrast_name} & ${variable}';"
	echo "matlabbatch{${J}}.spm.stats.con.consess{2}.tcon.convec = [0 -1];"
	echo "matlabbatch{${J}}.spm.stats.con.consess{2}.tcon.sessrep = 'none';"
	echo "matlabbatch{${J}}.spm.stats.con.delete = 0;"
	
	## -----------------------------------------------------------
	## Shows the results (for later printing)
	## -----------------------------------------------------------

	SPM_ID=$J
	K=0

	for ContrastName in Pos Neg; do  # Contrasts 1 and 2, Pos and Neg correls
	    K=$((K+1))
	    

	    J=$((J+1))

	    echo "matlabbatch{$J}.spm.stats.results.spmmat(1) = cfg_dep;"
	    echo "matlabbatch{$J}.spm.stats.results.spmmat(1).tname = 'Select SPM.mat';"
	    echo "matlabbatch{$J}.spm.stats.results.spmmat(1).tgt_spec{1}(1).name = 'filter';"
	    echo "matlabbatch{$J}.spm.stats.results.spmmat(1).tgt_spec{1}(1).value = 'mat';"
	    echo "matlabbatch{$J}.spm.stats.results.spmmat(1).tgt_spec{1}(2).name = 'strtype';"
	    echo "matlabbatch{$J}.spm.stats.results.spmmat(1).tgt_spec{1}(2).value = 'e';"
	    echo "matlabbatch{$J}.spm.stats.results.spmmat(1).sname = 'Contrast Manager: SPM.mat File';"
	    echo "matlabbatch{$J}.spm.stats.results.spmmat(1).src_exbranch = substruct('.','val', '{}',{${SPM_ID}}, '.','val', '{}',{1}, '.','val', '{}',{1});"
	    echo "matlabbatch{$J}.spm.stats.results.spmmat(1).src_output = substruct('.','spmmat');"
	    
	    echo "matlabbatch{$J}.spm.stats.results.conspec(1).titlestr = '${ContrastName} corr btwn ${contrast_name} & ${variable}';"
	    echo "matlabbatch{$J}.spm.stats.results.conspec(1).contrasts = ${K};"
	    echo "matlabbatch{$J}.spm.stats.results.conspec(1).threshdesc = 'none';"
	    echo "matlabbatch{$J}.spm.stats.results.conspec(1).thresh = 0.005;"
	    echo "matlabbatch{$J}.spm.stats.results.conspec(1).extent = 0;"
	    echo "matlabbatch{$J}.spm.stats.results.conspec(1).mask = struct('contrasts', {}, 'thresh', {}, 'mtype', {});"
	
	    echo "matlabbatch{$J}.spm.stats.results.units = 1;"
	    echo "matlabbatch{$J}.spm.stats.results.print = false;"

	    # --------------------------------------------------------
	    # Change folder
	    # --------------------------------------------------------
	 
	    J=$((J+1))
	    
	    echo "matlabbatch{$J}.cfg_basicio.cfg_cd.dir = {'${DIR}/$L2_RESULTS_FOLDER'};"

	    # --------------------------------------------------------
	    # Print from the SPM window
	    # --------------------------------------------------------
	    
	    J=$((J+1))

	    echo "matlabbatch{$J}.spm.util.print.fname = '${L2_RESULTS_FOLDER}_Summary.ps';"
	    echo "matlabbatch{$J}.spm.util.print.fig.fighandle = Inf;"
	    echo "matlabbatch{$J}.spm.util.print.opts.opt = {"
            echo "  '-dpsc2'"
            echo "  '-append'"
            echo "};"
	    echo "matlabbatch{$J}.spm.util.print.opts.append = true;"
	    echo "matlabbatch{$J}.spm.util.print.opts.ext = '.ps';"
	done
    done
done < $CONTRAST_FILE
