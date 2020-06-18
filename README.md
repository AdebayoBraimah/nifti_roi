# vol_stats_ROI_overlap

Identifies the ROIs overlapped with clusters from some input NIFTI volume file.

Requirements:
* `python v3.5+`
	* `numpy`
	* `pandas`
	* `nibabel`
* `FSL v6.0+`

Note: this script depends heavily on several of `FSL`'s binaries, and is therefore not executable on Windows platforms.

```
usage: vol_stats_ROI_overlap.py [-h] -i STATS.nii.gz -o OUTPUT.csv -a
                                ATLAS.nii.gz -info ATLAS.info.csv [-t FLOAT]
                                [-d FLOAT]

Finds NIFTI volume clusters and writes the overlapping ROIs to a CSV file.

optional arguments:
  -h, --help            show this help message and exit

Required arguments:
  -i STATS.nii.gz, -in STATS.nii.gz, --input STATS.nii.gz
                        NIFTI image file.
  -o OUTPUT.csv, -out OUTPUT.csv, --output OUTPUT.csv
                        Output spreadsheet name.
  -a ATLAS.nii.gz, -atlas ATLAS.nii.gz, --atlas ATLAS.nii.gz
                        NIFTI atlas file.
  -info ATLAS.info.csv, --atlas-info ATLAS.info.csv
                        Atlas information file.

Optional arguments:
  -t FLOAT, -thresh FLOAT, --thresh FLOAT
                        Cluster threshold. [default: 0.95]
  -d FLOAT, -dist FLOAT, --distance FLOAT
                        Minimum distance between clusters. [default: 0]
```
