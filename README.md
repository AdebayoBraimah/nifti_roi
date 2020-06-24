# nifti_roi

Identifies the ROIs overlapped with clusters from some input NIFTI volume file.

Requirements:
* `python v3.5+`
	* `numpy`
	* `pandas`
	* `nibabel`
* `FSL v6.0+`

**Note**: 
* This script depends heavily on several of `FSL`'s binaries, and is therefore not executable on Windows platforms.
* `Python` environmental issues may arise. If so, try this: `export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${FSLDIR}/fslpython/envs/fslpython/lib`.

```
usage: nifti_roi.py [-h] [-i STATS.nii.gz] [-o OUTPUT.csv] [--atlas-num INT]
                    [-a ATLAS.nii.gz] [-info ATLAS.info.csv] [-t FLOAT]
                    [-d FLOAT] [--dump-atlases]

Finds NIFTI volume clusters and writes the overlapping ROIs to a CSV file.

This process can be performed using either one to two methods:

1. A NIFTI volume file is provided, along with an atlas number to determine which ROI the cluster overlaps (this requires the input NIFTI volume to be in MNI space).
2. A NIFTI volume file is provided, along with a separate atlas NIFTI volume and an enumrated CSV file, that contains the ROI intensity values as a number-ROI pair (this requires the input NIFTI volume to be in this atlas' space.) 

For a list of available atlases, see the '--dump-atlases' option for details.

Note: enumrated CSV files must not contain Window's carriage returns.

optional arguments:
  -h, --help            show this help message and exit

Required arguments:
  -i STATS.nii.gz, -in STATS.nii.gz, --input STATS.nii.gz
                        NIFTI image file.
  -o OUTPUT.csv, -out OUTPUT.csv, --output OUTPUT.csv
                        Output spreadsheet name.

Atlasquery options:
  --atlas-num INT       Atlas number. See '--dump-atlases' for details.

Stand-alone atlas options:
  -a ATLAS.nii.gz, -atlas ATLAS.nii.gz, --atlas ATLAS.nii.gz
                        NIFTI atlas file.
  -info ATLAS.info.csv, --atlas-info ATLAS.info.csv
                        Atlas information file.

Optional arguments:
  -t FLOAT, -thresh FLOAT, --thresh FLOAT
                        Cluster threshold. [default: 0.95]
  -d FLOAT, -dist FLOAT, --distance FLOAT
                        Minimum distance between clusters. [default: 0]
  --dump-atlases        Prints available atlases and its corresponding atlas number.
```

