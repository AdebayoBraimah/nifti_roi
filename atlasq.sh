#!/usr/bin/env bash

#
# Command usage
#==============================================================================

Usage() {
  cat << USAGE

  Usage: $(basename ${0}) --coord "X,Y,Z" --atlas-num 3

Runs FSL's atlasquery for some atlas given some set of MNI space coordinates (in mm).

Required arguements:

  -c,-coord,--coord     MNI space X,Y,Z coordinates (provided as quoted comma separated list)

Optional arguements:

  -a,--atlas-num        Number used to determine which atlas is used, valid values range from 1-19 [default: 3]
  -h,-help,--help       Displays help menu

------------------------------

Atlas Numbers

1.  Cerebellar Atlas in MNI152 space after normalization with FLIRT
2.  Cerebellar Atlas in MNI152 space after normalization with FNIRT
3.  Harvard-Oxford Cortical Structural Atlas
4.  Harvard-Oxford Subcortical Structural Atlas
5.  Human Sensorimotor Tracts Labels
6.  JHU ICBM-DTI-81 White-Matter Labels
7.  JHU White-Matter Tractography Atlas
8.  Juelich Histological Atlas
9.  MNI Structural Atlas
10. Mars Parietal connectivity-based parcellation
11. Mars TPJ connectivity-based parcellation
12. Neubert Ventral Frontal connectivity-based parcellation
13. Oxford Thalamic Connectivity Probability Atlas
14. Oxford-Imanova Striatal Connectivity Atlas 3 sub-regions
15. Oxford-Imanova Striatal Connectivity Atlas 7 sub-regions
16. Oxford-Imanova Striatal Structural Atlas
17. Sallet Dorsal Frontal connectivity-based parcellation
18. Subthalamic Nucleus Atlas
19. Talairach Daemon Labels

  Usage: $(basename ${0}) --coord "X,Y,Z" --atlas-num 3

USAGE
  exit 1
}

#
# Parse command line
#==============================================================================

# Set defaults
atlas_num=3

# Parse options
while [[ ${#} -gt 0 ]]; do
  case "${1}" in
    -c|-coord|--coord) shift; coord=${1} ;;
    -a|--atlas-num) shift; atlas_num=${1} ;;
    -h|-help|--help) Usage; ;;
    -*) echo "$(basename ${0}): Unrecognized option ${1}" >&2; Usage; ;;
    *) break ;;
  esac
  shift
done

#
# Argument checks
#==============================================================================

if [[ -z ${coord} ]]; then
  echo "Required: 'coord' arguement required. Exiting..."
fi

if [[ -z ${atlas_num} ]]; then
  echo "Required: Atlas number required. See help menu. Exiting..."
elif [[ ${atlas_num} -gt 19 ]] || [[ ${atlas_num} -eq 0 ]]; then
  echo "Invalid atlas number. See help menu. Exiting..."
fi

#
# Determine desired atlas
#==============================================================================

# Define all available atlases in atlasquery
atlases=( "Cerebellar Atlas in MNI152 space after normalization with FLIRT"
"Cerebellar Atlas in MNI152 space after normalization with FNIRT"
"Harvard-Oxford Cortical Structural Atlas"
"Harvard-Oxford Subcortical Structural Atlas"
"Human Sensorimotor Tracts Labels"
"JHU ICBM-DTI-81 White-Matter Labels"
"JHU White-Matter Tractography Atlas"
"Juelich Histological Atlas"
"MNI Structural Atlas"
"Mars Parietal connectivity-based parcellation"
"Mars TPJ connectivity-based parcellation"
"Neubert Ventral Frontal connectivity-based parcellation"
"Oxford Thalamic Connectivity Probability Atlas"
"Oxford-Imanova Striatal Connectivity Atlas 3 sub-regions"
"Oxford-Imanova Striatal Connectivity Atlas 7 sub-regions"
"Oxford-Imanova Striatal Structural Atlas"
"Sallet Dorsal Frontal connectivity-based parcellation"
"Subthalamic Nucleus Atlas"
"Talairach Daemon Labels" )

# Define atlas indices
atlas_idx=$(( ${atlas_num} - 1 ))

# Determine atlas
atlas=${atlases[${atlas_idx}]}

#
# Perform atlas query
#==============================================================================

atlasquery --coord=${coord} --atlas="${atlas}"

# atlasquery --coord=${coord} --atlas="Harvard-Oxford Subcortical Structural Atlas" # old hard-coded command

# Test commands
# atlas="Harvard-Oxford Subcortical Structural Atlas"
# coord="24,-28,-10"
# atlasquery --coord=${coord} --atlas="${atlas}"
