#!/bin/bash

SUBJ=$1

cd $SUBJ/results

for imgtype in con spmT; do
    for measure in mean max var; do
	echo "${imgtype}/${measure}" >> ${SUBJ}_${imgtype}_${measure}.txt
	for image in ${imgtype}_*.hdr; do    
	    3dBrickStat -${measure} -automask -slow $image >> ${SUBJ}_${imgtype}_${measure}.txt
	done
    done
done

paste ${SUBJ}_*_*.txt >> ${SUBJ}_stats.txt
rm ${SUBJ}_*_*.txt
