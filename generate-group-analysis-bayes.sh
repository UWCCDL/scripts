#!/bin/bash
# ------------------------------------------------------------------ #
# GENERATE-GROUP-ANALYSIS
# ------------------------------------------------------------------ #
# Generates an SPM batch script for performing group analysis.
# ------------------------------------------------------------------ #

J=0
DIR=`pwd`
M="${DIR}/group-analysis.m"
echo "%% Starting... " > ${M}

L1_RESULTS_FOLDER=$1
L2_RESULTS_FOLDER=$2
CONTRAST_FILE=$3      # Contrast file
GROUP_FILE=$4         # Group file

GMS=3  # 1 = No GMS, 2 = proportional, 3 = ANCOVA
VAR=1 # 0 = Equal variance, 1 = unequal variance

#GROUPS=`awk '{print $2}' ${GROUP_FILE} | sort | uniq`
#echo $GROUPS, $GROUP_FILE

# --------------------------------------------------------------------
# Part 1 --- Full analysis with all subjects 
# --------------------------------------------------------------------

# Reset the contrast counter
C=0


while read contrast; do
    # Generates a different subfolder for each contrast
    C=$((C+1))
    contrast_name=`echo $contrast | cut -f1 -d':'`
    contrast_name=`echo ${contrast_name}`
    contrast_dir=${contrast_name// /_}     # Subtitute spaces with '_'
    
    J=$((J+1))

    echo "matlabbatch{${J}}.spm.stats.factorial_design.dir = {'${DIR}/${L2_RESULTS_FOLDER}/all/${contrast_dir}/'};" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t1.scans = {" >> ${M}
    
    while read subject; do
	subject_folder=`echo $subject | awk '{print $1}'`
	contrast_file=con_`printf "%04d" ${C}`.img
	
	if [ ! -e ${DIR}/${subject_folder}/do-not-include.txt ]; then
	    if [ -e ${DIR}/${subject_folder}/${L1_RESULTS_FOLDER}/${contrast_file} ]; then
		echo "'${DIR}/${subject_folder}/${L1_RESULTS_FOLDER}/${contrast_file},1'" >> ${M}
	    else
		echo "No contrast file ${contrast_file} for ${subject_folder}: Subject excluded"
	    fi
	else
	    echo "Excluding subject ${subject_folder} (do-not-include file found)"
	fi
    done < ${GROUP_FILE}
    
    echo "};" >> ${M}
    
    echo "matlabbatch{${J}}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.tm.tm_none = 1;" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.im = 1;" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.em = {''};" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalc.g_omit = 1;" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.glonorm = ${GMS};" >> ${M}

    # ----------------------------------------------------------------
    # Estimate the Group-Level Contrast
    # ----------------------------------------------------------------
    
    J=$((J+1))
    
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1) = cfg_dep;" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tname = 'Select SPM.mat';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).name = 'filter';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).value = 'mat';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).name = 'strtype';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).value = 'e';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).sname = 'Factorial design specification: SPM.mat File';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_output = substruct('.','spmmat');" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.fmri_est.method.Classical = 1;" >> ${M}

    # ----------------------------------------------------------------
    # Create the "Contrast" (A simple '1' vector)
    # ----------------------------------------------------------------

    J=$((J+1))

    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1) = cfg_dep;" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tname = 'Select SPM.mat';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).name = 'filter';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).value = 'mat';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).name = 'strtype';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).value = 'e';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).sname = 'Model estimation: SPM.mat File';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_output = substruct('.','spmmat');" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.name = '${contrast_name}';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.convec = 1;" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.sessrep = 'none';" >> ${M}
    echo "matlabbatch{${J}}.spm.stats.con.delete = 1;" >> ${M}
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

N=`awk '{print $2}' groups.txt | sort | uniq | wc | awk '{print $1}'`

if [ $N == 2 ]; then
    # If we have at least two groups, we need to create individual
    # analysis
    
    for group in `awk '{print $2}' ${GROUP_FILE} | sort | uniq`; do
	if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/${group} ]; then
	    echo "Creating folder for group '${group}'"
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
	    contrast_file=con_`printf "%04d" ${C}`.img

	    if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/${group}/${contrast_dir} ]; then
		echo "Warning: Creating '${contrast_dir}' folder"
		cd ${L2_RESULTS_FOLDER}/${group}
		mkdir ${contrast_dir}
		cd ../..
	    fi

	    J=$((J+1))

	    echo "matlabbatch{${J}}.spm.stats.factorial_design.dir = {'${DIR}/${L2_RESULTS_FOLDER}/${group}/${contrast_dir}/'};" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t1.scans = {" >> ${M}
    
	    for subject in `grep ${group} ${GROUP_FILE} | awk '{print $1}'`; do
		#echo "   $subject"
		if [ ! -e ${DIR}/${subject}/do-not-include.txt ]; then
		    if [ -e ${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file} ]; then
			echo "'${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file},1'" >> ${M}
		    else
			echo "No contrast file ${contrast_file} for ${subject}: Subject excluded"
		    fi
		else
		    echo "Excluding subject ${subject} (do-not-include file found)"
		fi
	    done
    
	    echo "};" >> ${M}
    
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.tm.tm_none = 1;" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.im = 1;" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.em = {''};" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalc.g_omit = 1;" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.glonorm = ${GMS};" >> ${M}
	    
            # ----------------------------------------------------------------
            # Estimate the Group-Level Contrast
            # ----------------------------------------------------------------
    
	    J=$((J+1))
    
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1) = cfg_dep;" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tname = 'Select SPM.mat';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).name = 'filter';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).value = 'mat';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).name = 'strtype';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).value = 'e';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).sname = 'Factorial design specification: SPM.mat File';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_output = substruct('.','spmmat');" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.fmri_est.method.Classical = 1;" >> ${M}
	    
            # ----------------------------------------------------------------
            # Create the "Contrast" (A simple '1' vector)
            # ----------------------------------------------------------------

	    J=$((J+1))
	    
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1) = cfg_dep;" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tname = 'Select SPM.mat';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).name = 'filter';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).value = 'mat';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).name = 'strtype';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).value = 'e';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).sname = 'Model estimation: SPM.mat File';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_output = substruct('.','spmmat');" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.name = '${contrast_name}';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.convec = 1;" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.sessrep = 'none';" >> ${M}
	    echo "matlabbatch{${J}}.spm.stats.con.delete = 1;" >> ${M}
	done < ${CONTRAST_FILE}
    done
fi

## -------------------------------------------------------------------
## PART 3: GROUP COMPARISONS
## -------------------------------------------------------------------

if [ $N == 2 ]; then
    if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/comparisons ]; then
	echo "Warning: Creating 'comparisons' directory"
	cd ${L2_RESULTS_FOLDER}
	mkdir comparisons
	cd ..
    fi

    # Ideally, these two should be identified at the very beginning of the
    # file to avoid inconsistencies if the file is rewritten during
    # the execution of the script.

    group1=`awk '{print $2}' groups.txt | sort | uniq | head -1`
    group2=`awk '{print $2}' groups.txt | sort | uniq | tail -1`

    # Reset contrast counter
    C=0

    while read contrast; do
        # Generates a different subfolder for each contrast
	C=$((C+1))
	contrast_name=`echo $contrast | cut -f1 -d':'`
	contrast_name=`echo ${contrast_name}`
	contrast_dir=${contrast_name// /_}     # Subtitute spaces with '_'
	contrast_file=con_`printf "%04d" ${C}`.img

	if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/comparisons/${contrast_dir} ]; then
	    echo "Warning: Creating '${contrast_dir}' folder"
	    cd ${L2_RESULTS_FOLDER}/comparisons
	    mkdir ${contrast_dir}
	    cd ../..
	fi

	J=$((J+1))

    
	echo "matlabbatch{${J}}.spm.stats.factorial_design.dir = {'${DIR}/${L2_RESULTS_FOLDER}/comparisons/${contrast_dir}'};" >> ${M}

	# ------------------------------------------------------------
	# Group 1
	# ------------------------------------------------------------

	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.scans1 = {" >> ${M}
	
	for subject in `grep ${group1} ${GROUP_FILE} | awk '{print $1}'`; do
	    if [ ! -e ${DIR}/${subject}/do-not-include.txt ]; then
		if [ -e ${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file} ]; then
		    echo "'${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file},1'" >> ${M}
		else
		    echo "No contrast file ${contrast_file} for ${subject}: Subject excluded"
		fi
	    else
		echo "Excluding subject ${subject} (do-not-include file found)"
	    fi
	done
        echo "};" >> ${M}

	# ------------------------------------------------------------
	# Group 2
	# ------------------------------------------------------------
	
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.scans2 = {" >> ${M}
	
	for subject in `grep ${group2} ${GROUP_FILE} | awk '{print $1}'`; do
	    if [ ! -e ${DIR}/${subject}/do-not-include.txt ]; then
		if [ -e ${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file} ]; then
		    echo "'${DIR}/${subject}/${L1_RESULTS_FOLDER}/${contrast_file},1'" >> ${M}
		else
		    echo "No contrast file ${contrast_file} for ${subject}: Subject excluded"
		fi
	    else
		echo "Excluding subject ${subject} (do-not-include file found)"
	    fi
	done
        echo "};" >> ${M}
        
	
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.dept = 0;" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.variance = ${VAR};" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.gmsca = 0;" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.des.t2.ancova = 0;" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.tm.tm_none = 1;" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.im = 1;" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.masking.em = {''};" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.globalc.g_omit = 1;" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.factorial_design.globalm.glonorm = ${GMS};" >> ${M}

	J=$((J+1))

	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1) = cfg_dep;" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tname = 'Select SPM.mat';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).name = 'filter';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(1).value = 'mat';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).name = 'strtype';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).tgt_spec{1}(2).value = 'e';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).sname = 'Factorial design specification: SPM.mat File';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.fmri_est.spmmat(1).src_output = substruct('.','spmmat');" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.fmri_est.method.Classical = 1;" >> ${M}

	J=$((J+1))

	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1) = cfg_dep;" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tname = 'Select SPM.mat';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).name = 'filter';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(1).value = 'mat';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).name = 'strtype';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).tgt_spec{1}(2).value = 'e';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).sname = 'Model estimation: SPM.mat File';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_exbranch = substruct('.','val', '{}',{$((J-1))}, '.','val', '{}',{1}, '.','val', '{}',{1});" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.spmmat(1).src_output = substruct('.','spmmat');" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.name = '${group1} > ${group2}';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.convec = [1 -1];" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.consess{1}.tcon.sessrep = 'none';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.consess{2}.tcon.name = '${group2} > ${group1}';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.consess{2}.tcon.convec = [-1 1];" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.consess{2}.tcon.sessrep = 'none';" >> ${M}
	echo "matlabbatch{${J}}.spm.stats.con.delete = 0;" >> ${M}
    done < ${CONTRAST_FILE}
fi

if [ $N != 2 ]; then
    # If there were more than two groups, then we have only two options:
    # Either we don't have between-group designs (in which case, we exit)
    # or we have more than two groups (in which case, right now, we
    # cannot really do much)
    if [ $N == 1 ]; then
	echo "No groups found, ending here"
    else
	echo "More than three groups found. Cannot do analysis (${GROUPS})."
    fi
fi