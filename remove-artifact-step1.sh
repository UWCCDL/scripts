#!/bin/bash

# For each subject:
#    For each block:
#        create 4D file with 3dTcat from time sliced images
#        create Mask file with Automask
#        * create noiseless mask with Matlab
#        ** warp noiseless masks with SPM and sn_mat files
#        smooth with corresponding masks using 3dBlurInMask
#    Run new model using blurred 4D datasets
#
dir=`pwd`
exp=`basename $dir`

for s in $@; do #`ls -d 11[0-9][0-9][0-9]`; do
    echo "Processing subject $s"
    if [ -e ${s}/${s}_sessions.txt ]; then
	cd $s/raw
	b=1  # block counter
	while read line; do
	    echo "  Creating 4D files and mask"
	    # we need to know if we have Nifti or Analyze file formats
	    nifti=`ls 2> /dev/null ${line}.nii | wc | awk '{print $1}'`
	    if [ $nifti -eq 0 ]; then
		ext="hdr"
	    else
		ext="nii"
	    fi
	    3dTcat -prefix a${s}_${exp}${b}.nii a${line}.${ext}
	    3dAutomask -prefix a${s}_${exp}${b}_mask.nii a${s}_${exp}${b}.nii
	    matlab -nosplash -nodesktop -r "findFuncNoise(2, 'a${s}_${exp}${b}.nii', 'a${s}_${exp}${b}_mask.nii');quit;"
	    # Rename noiseless mask and noisePic
	    mv mask_noiseless.nii a${s}_${exp}${b}_mask_noiseless.nii
	    mv noisePic.png a${s}_${exp}${b}_noise.png
	    
	    b=$((${b}+1))  # Incr block counter

	done < ../${s}_sessions.txt
	cd ../..
    else
	echo "  Session file not found for subject $s"
    fi
done
