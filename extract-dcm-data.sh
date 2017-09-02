#!/bin/bash

## ---------------------------------------------------------------- ##
## EXTRACT-DCM-DATA.SH
## ---------------------------------------------------------------- ##
## Extract DCMs for the Autism task
## ---------------------------------------------------------------- ##
## History 
## ---------------------------------------------------------------- ##
##
## 2013-05-16 : The matlab code now correctly outputs the size of
##            : each matrix being written.
##
## 2013-05-11 : Added code that checks the consistency between the
##            : size of a parameter matrix and the corresponding
##            : name matrix in Matlab.
##
## 2013-03-14 : Modified the output Matlab code so that it now
##            : adds a header with column names to the output files
##            : (the parameter matrices). Column names are created
##            : from the data of tyhe first DCM model.
##
## 2012-02-07 : Generalized the code. Now takes the model as an 
##            : argument.
##
## 2012-02-02 : File created
## ---------------------------------------------------------------- ##

NL="
"   # new line

HELP_MSG="extract-dcm-data
 --------------------------------------
 This program extracts the various DCM
 matrices for a specific model. It 
 creates files corresponding to each
 matrix for each given participant, as
 well as group matrices with all
 participants.
  
 Usage
 --------------------------------------
 $ extract-dcm-data.sh <model> <sub1> 
                    <sub2> ... <subN>
 
 where:
   <model>  is the DCM model name 
          (without the .mat extension)
   <subX>   is the [list of] of subject
          folders.

 Notes
 --------------------------------------
 * The script must be run from the root
   folder, where all the subjects 
   folders are located
 * Each subject folder must have a 'DCM'
   directory where the model is located
 * At least two arguments need to be 
   provided (model and at least one 
   subject)
" 

if [ $# -lt 2 ]; then
    echo "$HELP_MSG"
    exit
fi

MODEL=$1
shift

MFILE=`pwd`/extract_${MODEL}_data_`date +%Y_%m_%d_%H%M`.m
BASE_DIR="`pwd`"
DCM_DIR="DCM"


echo "% Extracting DCM data for $@" > $MFILE

INIT=0  # Flag to check for the initialized VOI names, which will
        # be used to create the headers for the files containing
        # matrices A, B, C, and D. The VOI names and headers are
        # created after parsing the first subject; after that this
        # flag is set to 1.

for subj in $@; do
    echo "clear DCM;" >> $MFILE
    echo "load(fullfile('${BASE_DIR}', '${subj}', '$DCM_DIR', '${MODEL}.mat'));" >> $MFILE

    if [ $INIT -eq 0 ]; then 
	echo "Not initialized, creating names now"
        # This is the code that creates the name matrices
	echo "vois={DCM.xY.name};"  >> $MFILE  # VOI names
	echo "inputs=DCM.U.name;"   >> $MFILE  # Input names
	echo "nv = DCM.n;"          >> $MFILE  # Number of VOIs
	echo "ni = length(inputs);" >> $MFILE  # Number of inputs
    
	echo "namesA=cell(nv, nv);" >> $MFILE
	echo "namesB=cell(nv, nv, ni);" >> $MFILE
	echo "namesC=cell(nv, ni);" >> $MFILE
	echo "namesD=cell(nv, nv, nv);" >> $MFILE
	echo "for i=1:nv," >> $MFILE
	echo "    for j=1:ni," >> $MFILE
	echo "        namesC{i,j}=strcat(inputs{j},'-to-',vois{i});" >> $MFILE
	echo "    end" >> $MFILE
	echo "    for j=1:nv," >> $MFILE
	echo "        namesA{i,j}=strcat(vois{j},'-to-',vois{i});" >> $MFILE
	echo "        for k=1:ni," >> $MFILE
	echo "            namesB{i,j,k}=strcat(vois{j},'-to-',vois{i}, '-by-', inputs{k});" >> $MFILE
	echo "        end" >> $MFILE
	echo "        for k=1:nv," >> $MFILE
	echo "            namesD{i,j,k}=strcat(vois{j},'-to-',vois{i}, '-by-', vois{k});" >> $MFILE
	echo "        end" >> $MFILE
	echo "    end" >> $MFILE
	echo "end" >> $MFILE

	for matrix in 'A' 'B' 'C' 'D'; do
	    echo "res_file  = fopen('${BASE_DIR}/${MODEL}_data_${matrix}.txt', 'w');" >> $MFILE
	    echo "c=cumprod(size(names${matrix}));" >> $MFILE
	    echo "n=c(end);" >> $MFILE
	    echo "vals=reshape(names${matrix},1,n);" >> $MFILE
	    echo "fprintf(res_file, '%s\t', 'Subject');" >> $MFILE
	    echo "fprintf(res_file, '%s\t', vals{:});" >> $MFILE
	    echo "fprintf(res_file, '\n');" >> $MFILE
	done
	INIT=1
    fi

    echo "${NL}%------------------------------------" >> $MFILE
    echo "disp('Extracting model ${MODEL} data for ${subj}');" >> $MFILE
    echo "${NL}%------------------------------------${NL}" >> $MFILE
    for matrix in 'A' 'B' 'C' 'D'; do
	echo "disp('    Extracting matrix ${matrix}');" >> $MFILE
	echo "subj_file = fopen('${BASE_DIR}/${subj}/DCM/${subj}_${MODEL}_data_${matrix}.txt', 'w');" >> $MFILE
	echo "res_file  = fopen('${BASE_DIR}/${MODEL}_data_${matrix}.txt', 'a');" >> $MFILE
	echo "c = cumprod(size(DCM.Ep.${matrix}));" >> $MFILE
	echo "n = c(end);" >> $MFILE
	echo "fprintf('        (Size: %d)\n', n);" >> $MFILE
	echo "if n ~= 0" >> $MFILE
	echo "    vals = reshape(names${matrix},1,n);" >> $MFILE
	echo "    fprintf(subj_file, '%s\t', vals{:});" >> $MFILE
	echo "    fprintf(subj_file, '%f\t', reshape(DCM.Ep.${matrix}, 1, n)');" >> $MFILE
	echo "    fprintf(res_file, '%s\t', '${subj}');" >> $MFILE
	echo "    fprintf(res_file, '%f\t', reshape(DCM.Ep.${matrix}, 1, n)');" >> $MFILE
	echo "else" >> $MFILE
	echo "    display('    Array of size 0 detected');" >> $MFILE
	echo "end" >> $MFILE
	echo "fprintf(subj_file, '\n');" >> $MFILE
	echo "fprintf(res_file, '\n');" >> $MFILE
	echo "${NL}%------------------------------------${NL}" >> $MFILE
    done
done
