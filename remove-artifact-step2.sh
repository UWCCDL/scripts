#!/bin/bash

# For each subject:
#    For each block:
#        create 4D file with 3dTcat from warped images
#        if the corresponding warped mask exists,
#        smooth with corresponding masks using 3dBlurInMask
#    Run new model using blurred 4D datasets
#

dir=`pwd`
exp=`basename $dir`

for s in $@; do
    echo "Processing subject $s"
    if [ -e ${s}/${s}_sessions.txt ]; then
	cd $s/raw
	b=1  # block counter
	while read line; do
	    echo "  Creating 4D files"

	    if [ -e wa${s}_${exp}${b}_mask_noiseless.nii ]; then

		3dBlurInMask -input wa${s}_${exp}${b}.nii \
		             -mask wa${s}_${exp}${b}_mask_noiseless.nii \
		             -prefix swa${s}_${exp}${b}_noart.nii \
		             -FWHM 6

		# 3. Replace the artifact hole with the artifact 
		3dcalc -prefix swa${s}_${exp}${b}_artreplaced.nii \
		       -a swa${s}_${exp}${b}_noart.nii \
		       -b wa${s}_${exp}${b}_mask_noiseless.nii \
		       -c wa${s}_${exp}${b}.nii \
		       -d wa${s}_${exp}${b}_mask.nii \
		       -expr "(a+(iszero(b)*c))*d"
		

		# 4. Calculate % signal change

		3dTstat -mean -prefix swa${s}_${exp}${b}_artreplaced_mean.nii \
		        swa${s}_${exp}${b}_artreplaced.nii

		3dcalc -a swa${s}_${exp}${b}_artreplaced.nii \
		       -b swa${s}_${exp}${b}_artreplaced_mean.nii \
		       -expr '(a/b)*100' \
		       -prefix swa${s}_${exp}${b}_artreplaced_psc.nii 

		# 5. Do another smoothing to even out the sharp
		# parts where the artifact has been replaced.
		3dBlurInMask -input swa${s}_${exp}${b}_artreplaced_psc.nii \
		             -mask wa${s}_${exp}${b}_mask.nii \
		             -prefix swa${s}_${exp}${b}_artreplaced_final.nii \
		             -FWHM 2

	    fi


	    b=$((${b}+1))  # Incr block counter
	done < ../${s}_sessions.txt
	cd ../..
    else
	echo "  Session file not found for subject $s"
    fi
done