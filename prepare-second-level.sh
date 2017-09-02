#!/bin/bash

HLP_MSG="
Usage:\n
\n
  $ generate-group-analysis <l1-dir> <l2-dir> <contrast_file> <group_file>\n
\n
where:\n
\n
  l1-dir: name of each subject's L1 model folder\n
  l2-dir: name of the L2 results folder (will be created if\n
          not existing)\n
  contrast_file: name of a file containing contrast names for\n
          the L1 models\n
  group_file: name of a file containing subject names and\n
          (eventual) groups.\n
"


J=0
DIR=`pwd`
M="${DIR}/group-analysis.m"
echo "%% Starting... " > ${M}

L1_RESULTS_FOLDER=$1
L2_RESULTS_FOLDER=$2
CONTRAST_FILE=$3      # Contrast file
GROUP_FILE=$4         # Group file


HLP_MSG="
Usage:\n
\n
  $ generate-group-analysis <l1-dir> <l2-dir> <contrast_file> <subj_file>\n
\n
where:\n
\n
  l1-dir: name of each subject's L1 model folder\n
  l2-dir: name of the L2 results folder (will be created if\n
          not existing)\n
  contrast_file: name of a file containing contrast names for\n
          the L1 models\n
  subjects_file: name of a file containing subject names and\n
          (eventual) groups.\n
"


J=0
DIR=`pwd`
M="${DIR}/group-analysis.m"
echo "%% Starting... " > ${M}

L1_RESULTS_FOLDER=$1
L2_RESULTS_FOLDER=$2
CONTRAST_FILE=$3      # Contrast file
GROUP_FILE=$4         # Group file

if [ $# -ne 4 ]; then
    echo -e $HLP_MSG
    exit
fi

if [ ! -d ${DIR}/${L2_RESULTS_FOLDER} ]; then
    echo "Warning: Creating '${L2_RESULTS_FOLDER}' folder"
    /bin/mkdir ${L2_RESULTS_FOLDER}
fi



# Reset the contrast counter
C=0

while read contrast; do
    # Generates a different subfolder for each contrast

    C=$((C+1))
    contrast_name=`echo $contrast | cut -f1 -d':'`
    contrast_name=`echo ${contrast_name}`
    contrast_dir=${contrast_name// /_}     # Subtitute spaces with '_'
    
    if [ ! -d ${DIR}/${L2_RESULTS_FOLDER}/${contrast_dir} ]; then
	echo "Warning: Creating '${contrast_dir}' folder"	
	mkdir ${L2_RESULTS_FOLDER}/${contrast_dir}
    fi
    
    
    while read subject; do
	subject_folder=`echo $subject | awk '{print $1}'`
	contrast_file=con_`printf "%04d" ${C}`
	if [ -e ${DIR}/${subject_folder}/${L1_RESULTS_FOLDER}/${contrast_file}.img ]; then
	    cp ${DIR}/${subject_folder}/${L1_RESULTS_FOLDER}/${contrast_file}.img ${DIR}/${L2_RESULTS_FOLDER}/${contrast_dir}/${subject_folder}_${contrast_file}.img
	    cp ${DIR}/${subject_folder}/${L1_RESULTS_FOLDER}/${contrast_file}.hdr ${DIR}/${L2_RESULTS_FOLDER}/${contrast_dir}/${subject_folder}_${contrast_file}.hdr
	else
	    echo "No contrast files found for subject ${subject_folder}"
	fi
    done < ${GROUP_FILE}

    J=$((J+1))

done < $CONTRAST_FILE
