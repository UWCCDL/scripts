#!/bin/bash
## ---------------------------------------------------------------- ##
## EXTRACT-DCM-DATA.SH
## ---------------------------------------------------------------- ##
## Extract VOI data
## ---------------------------------------------------------------- ##
## History 
## ---------------------------------------------------------------- ##
##
## 2018-08-16 : Fixed documentation.
##
## 2016-05-14 : Added DCM folder as second parameter
##
## 2013-07-10 : Added code to record the number of voxels as well
##            : as the spatial coordinates. 
##
## ---------------------------------------------------------------- ##

NL="
"   # new line

HELP_MSG="extract-voi-data
 --------------------------------------
 This program extracts the various VOI
 information for a specific VOI. 
  
 Usage
 --------------------------------------
 $ extract-voi-data.sh <voi> <dir> 
                       <sub1> ... <subN>
 
 where:
   <voi>   is the VOI name 
          (without the leading 'VOI' or
          the trailing '_1.mat')

   <dir>   is the subject folder where
          the VOI is located (e.g., 
          'DCM')

   <subX>   is the [list of] of subject
          folders.

 Notes
 --------------------------------------
 * The script must be run from the root
   folder, where all the subjects 
   folders are located
 * Each subject folder must have a 'DCM'
   directory where the VOI is located
 * At least two arguments need to be 
   provided (VOI and at least one 
   subject)
" 

if [ $# -lt 2 ]; then
    echo "$HELP_MSG"
    exit
fi

VOI=$1
DCM_DIR=$2

shift
shift


echo "VOI $VOI, DCM_DIR $DCM_DIR"

MFILE=`pwd`/extract_${VOI}_data_`date +%Y_%m_%d_%H%M`.m
BASE_DIR="`pwd`"

echo "% Extracting VOI data for $@" > $MFILE
#echo "resA_file=fopen('${BASE_DIR}/${subj}/${MODEL}_data_A.txt', 'a');" >> $MFILE
#echo "resB_file=fopen('${BASE_DIR}/${subj}/${MODEL}_data_B.txt', 'a');" >> $MFILE
#echo "resC_file=fopen('${BASE_DIR}/${subj}/${MODEL}_data_C.txt', 'a');" >> $MFILE
#echo "resD_file=fopen('${BASE_DIR}/${subj}/${MODEL}_data_D.txt', 'a');" >> $MFILE

echo "res_file  = fopen('${BASE_DIR}/${VOI}_xyz.txt', 'w');" >> $MFILE
echo "names = {'Subject', 'VOI', 'x', 'y', 'z', 'Size'};" >> $MFILE
echo "fprintf(res_file, '%s\t', names{:});" >> $MFILE
echo "fprintf(res_file, '\n');" >> $MFILE

for subj in $@; do
    echo "disp('Extracting VOI ${VOI} data for ${subj}');" >> $MFILE
    echo "subj_file = fopen('${BASE_DIR}/${subj}/${DCM_DIR}/${subj}_${VOI}_xyz.txt', 'w');" >> $MFILE
    echo "res_file  = fopen('${BASE_DIR}/${VOI}_xyz.txt', 'a');" >> $MFILE
    echo "load(fullfile('${BASE_DIR}', '${subj}', '$DCM_DIR', 'VOI_${VOI}_1.mat'), 'xY');" >> $MFILE

    echo "fprintf(subj_file, '%s\t', names{2:end});" >> $MFILE
    echo "fprintf(subj_file, '\n');" >> $MFILE
    echo "fprintf(subj_file, '%s\t', xY.name);" >> $MFILE
    echo "fprintf(subj_file, '%f\t', xY.xyz');" >> $MFILE
    echo "fprintf(subj_file, '%f\t', length(xY.s));" >> $MFILE
    echo "fprintf(subj_file, '\n');" >> $MFILE

    echo "fprintf(res_file, '%s\t', '${subj}');" >> $MFILE
    echo "fprintf(res_file, '%s\t', xY.name);" >> $MFILE
    echo "fprintf(res_file, '%f\t', xY.xyz');" >> $MFILE
    echo "fprintf(res_file, '%f\t', length(xY.s));" >> $MFILE
    echo "fprintf(res_file, '\n');" >> $MFILE

    echo "${NL}%------------------------------------${NL}" >> $MFILE
done
