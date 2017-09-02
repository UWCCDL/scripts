#!/bin/bash
## ================================================================ ##
## EXTRACT_BETAS
## ================================================================ ##
## This file creates a matlab script that uses MarsBaR functions
## to extract betas from a design for a specific set of ROIs.
## ================================================================ ##
## Usage:
##
## $ extract_betas.sh <results_dir> <rois_dir>
##
## Where <results_dir> is the results folder where the SPM file can
## be found for every subject (e.g., "results2") and rois_dir is
## the path to a folder containing the rois (e.g., "/predef/rois02/").
##
## The script produces a Matlab .m file that can be run into
## matlab (after loading SPM and MarsBaR).
##
## ================================================================ ##
## 
## History
##
## 2013-11-20 : Generalized so that it runs on every experiment
##            : whose subjects are named "NNNNN".
## 
## 2013-01-05 : Added Help message.
##
## 2011-11-21 : Got rid of the 'extractfield' function (which was 
##              specific to some Matlab toolbox)
##
## 2011-01-16 : First run.
##
## 2011-01-15 : File created
##
## ================================================================ ##

## This is the matlab code

HLP_MSG="Usage:\n
\n
   $ extract_betas.sh <results_dir> <rois_dir> <subj1> <subj2> ... <subjN>\n
\n
Where:\n
\n
   <results_dir> is the results folder where the SPM file can\n
 be found for every subject (e.g., 'results2'); \n\n
   <rois_dir> is the path to a folder containing the rois (e.g.,\n
 '/predef/rois02/').\n
\n
 The script produces a Matlab .m file that can be run into\n
 matlab (after loading SPM and MarsBaR). The file is going to\n
 be named <results_dir>_<rois_dir>.m\n
\n
"

if [ $# -le 2 ]; then
    echo -e $HLP_MSG
    exit
fi

## Read the arguments
results=$1
rois_dir=$2

## Now let's get only the ROIs folder name
rois_base=`basename ${rois_dir}`
file=${results}_${rois_base}.m

sep="%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

## Let's load the rois into an array.
current=`pwd`
cd ${rois_dir}
rois_dir=`pwd`
rois=`ls *.mat`

## Go back to base dir
cd ${current}

if [ -e ${current}/${results}_${rois_base}.txt ]
then
    rm  ${current}/${results}_${rois_base}.txt
fi
      

#echo "c_file=fopen('cz_strings.txt', 'w');" > ${file}
echo "d_file=fopen('${current}/${results}_${rois_base}.txt', 'w');" > ${file}
echo `pwd`
for subj in "$@"; #`ls -d [0-9][0-9][0-9][0-9][0-9]` #`ls -d 11*`;
do
  if [ -e ${subj}/${results}/SPM.mat ]; then
      if [ -e ${current}/${subj}/${subj}_${results}_${rois_base}.txt ]; then
	  rm  ${current}/${subj}/${subj}_${results}_${rois_base}.txt
      fi
      echo "display('Starting subject ${subj}')" >> ${file}
      echo ${sep} >> ${file}
      echo -e "% Subject ${subj}\n${sep}" >> ${file}
      echo "subj_file=fopen('${current}/${subj}/${subj}_${results}_${rois_base}.txt', 'w');" >> ${file}
      echo "spm_name = '${current}/${subj}/${results}/SPM.mat';" >> ${file}
      for roi in ${rois}
      do
	echo ${sep} >> ${file}
	echo "roi_file = '${rois_dir}/${roi}';" >> ${file}
	echo "% Would it work if we specify a vector of ROIs?" >> ${file}

	echo "% Make marsbar design object" >> ${file}
	echo "D  = mardo(spm_name);" >> ${file}
	echo "% Make marsbar ROI object" >> ${file}
	echo "R  = maroi(roi_file);" >> ${file} 
	echo "% Fetch data into marsbar data object" >> ${file}
	echo "Y  = get_marsy(R, D, 'mean');" >> ${file}
	echo "% Get contrasts from original design" >> ${file}
	echo "xCon = get_contrasts(D);" >> ${file}
	echo "% Estimate design on ROI data" >> ${file}
	echo "E = estimate(D, Y);" >> ${file}
	echo "% Put contrasts from original design back into design object" >> ${file}
	echo "E = set_contrasts(E, xCon);" >> ${file}
	echo "% get design betas" >> ${file}
	echo "b = betas(E);" >> ${file}
	echo "% get stats and stuff for all contrasts into statistics structure" >> ${file}
	echo "marsS = compute_contrasts(E, 1:length(xCon));" >> ${file}

	echo "% need a file to save the ROI name" >> ${file}
	echo "roi_col=repmat(marsS.columns, length(xCon), 1);" >> ${file}
	echo "sub_col=cellstr(repmat('${subj}', length(xCon), 1));" >> ${file}
	
	# this function was removed because is specific to a toolbox.
	#echo "con_col=extractfield(xCon, 'name');" >> ${file}
	
	echo "con_col={xCon.name};" >> ${file}
	echo "strings=horzcat(sub_col, con_col', roi_col);" >> ${file}
	
	#echo "fprintf(c_file, '%s\t%s\t%s', strings{:});" >> ${file}

	echo "% Now let's concatenate the results" >> ${file}
	echo "data=horzcat(marsS.con, marsS.stat, marsS.P, marsS.Pc);" >> ${file}
	echo "table=horzcat(strings, num2cell(data));" >> ${file}
	echo "table=table';" >> ${file}
	echo "fprintf(subj_file, '%s\t\"%s\"\t%s\t%f\t%f\t%f\t%f\n', table{:});" >> ${file}
	echo "fprintf(d_file, '%s\t\"%s\"\t%s\t%f\t%f\t%f\t%f\n', table{:});" >> ${file}
	#echo "fprintf(d_file, '%f\t%f\t%f', k');" >> ${file}
      done
  fi
done