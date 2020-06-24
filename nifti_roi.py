#!/usr/bin/env python

# Import modules
import os
import re
import sys
import numpy as np
import pandas as pd
import nibabel as nib
import subprocess
import platform

# Import modules for argument parsing
import argparse

# Define global variable(s)
scripts_dir = os.path.dirname(os.path.realpath(__file__))

# Define class(es)

class Command():
    '''
    Creates a command and an empty command list for UNIX command line programs/applications. Primary use and
    use-cases are intended for the subprocess module and its associated classes (i.e. call/run).
    Attributes:
        command: Command to be performed on the command line
    '''

    def __init__(self):
        '''
        Init doc-string for Command class.
        '''
        pass

    def init_cmd(self, command):
        '''
        Init command function for initializing commands to be used on UNIX command line.
        
        Arguments:
            command (string): Command to be used. Note: command used must be in system path
        Returns:
            cmd_list (list): Mutable list that can be appended to.
        '''
        self.command = command
        self.cmd_list = [f"{self.command}"]
        return self.cmd_list

# Define functions

def run(cmd_list,stdout="",stderr=""):
    '''
    Uses python's built-in subprocess class to run a command from an input command list.
    The standard output and error can optionally be written to file.
    
    Arguments:
        cmd_list(list): Input command list to be run from the UNIX command line.
        stdout(file): Output file to write standard output to.
        stderr(file): Output file to write standard error to.
    Returns:
        stdout(file): Output file that contains the standard output.
        stderr(file): Output file that contains the standard error.
    '''
    if stdout and stderr:
        with open(stdout,"w") as file:
            with open(stderr,"w") as file_err:
                subprocess.call(cmd_list,stdout=file,stderr=file_err)
                file.close(); file_err.close()
    elif stdout:
        with open(stdout,"w") as file:
            subprocess.call(cmd_list,stdout=file)
            file.close()
        stderr = None
    else:
        subprocess.call(cmd_list)
        stdout = None
        stderr = None

    return stdout,stderr

def roi_loc(coords,vol_atlas_num=3):
    '''
    Uses input list of X,Y,Z MNI space mm coordinates to identify ROIs.
    
    NOTE: External bash script is used.
    
    Arguments:
        coords(list): Coordinate list with a lenth of 3 that corresponds to the XYZ coordinates of some ROI in MNI space.
        vol_atlas_num(int): Atlas to be used in FSL's `atlasquery`. Number corresponds to an atlas. See FSL's `atlasquery` help menu for details.
    Returns:
        roi_list(list): List of ROIs generated from input coordinates.
    '''
    
    # Define volume atlas number dictionary
    vol_atlas_dict = {
    1: "Cerebellar Atlas in MNI152 space after normalization with FLIRT",
    2: "Cerebellar Atlas in MNI152 space after normalization with FNIRT",
    3: "Harvard-Oxford Cortical Structural Atlas",
    4: "Harvard-Oxford Subcortical Structural Atlas",
    5: "Human Sensorimotor Tracts Labels",
    6: "JHU ICBM-DTI-81 White-Matter Labels",
    7: "JHU White-Matter Tractography Atlas",
    8: "Juelich Histological Atlas",
    9: "MNI Structural Atlas",
    10: "Mars Parietal connectivity-based parcellation",
    11: "Mars TPJ connectivity-based parcellation",
    12: "Neubert Ventral Frontal connectivity-based parcellation",
    13: "Oxford Thalamic Connectivity Probability Atlas",
    14: "Oxford-Imanova Striatal Connectivity Atlas 3 sub-regions",
    15: "Oxford-Imanova Striatal Connectivity Atlas 7 sub-regions",
    16: "Oxford-Imanova Striatal Structural Atlas",
    17: "Sallet Dorsal Frontal connectivity-based parcellation",
    18: "Subthalamic Nucleus Atlas",
    19: "Talairach Daemon Labels"}
    
    # Define list and output file
    roi_list = list()
    out_file = "subcort.rois.txt"
    
    if len(coords) == 3:
        atlasq_cmd = os.path.join(scripts_dir,"atlasq.sh")
        atlasq = Command().init_cmd(atlasq_cmd)
        atlasq.append(f"--coord")
        atlasq.append(f"\"{coords[0]},{coords[1]},{coords[2]}\"")
        atlasq.append("--atlas-num")
        atlasq.append(f"{vol_atlas_num}")
    
        run(atlasq,out_file)

        with open(out_file,"r") as file:
            text = file.readlines()
            for i in range(0,len(text)):
                text[i] = re.sub(f"<b>{vol_atlas_dict[vol_atlas_num]}</b><br>","",text[i].rstrip())

        os.remove(out_file)
        
        if len(text) == 0:
            pass
        else:
            roi_list.extend(text) 
        
    return roi_list

def vol_clust(nii_file,thresh=0.95,dist=0,vol_atlas_num=3):
    '''
    Identifies clusters in a volumetric (NIFTI) file.
    
    Arguments:
        nii_file(file): Input NIFTI file
        thresh(float): Cluster minimum threshold
        dist(float): Minimum distance between clusters
        vol_atlas_num(int): Atlas to be used in FSL's `atlasquery`. Number corresponds to an atlas. See FSL's `atlasquery` help menu for details.
    Returns:
        roi_list(list): List of ROIs that overlap with some given cluster
    '''
    
    out_file = "vol.cluster.tsv"
    
    roi_list = list()
    tmp_list = list()
    
    vol_clust = Command().init_cmd("cluster")
    
    vol_clust.append(f"--in={nii_file}")
    vol_clust.append(f"--thresh={thresh}")
    vol_clust.append(f"--peakdist={dist}")
    vol_clust.append("--mm")
    
    run(vol_clust,out_file)
    
    df_tmp = pd.read_csv(out_file,sep="\t")
    
    os.remove(out_file)
    
    df = df_tmp[['MAX X (mm)','MAX Y (mm)','MAX Z (mm)']].copy()
    
    for i in range(0,len(df)):
        coord_list=[df['MAX X (mm)'][i],df['MAX Y (mm)'][i],df['MAX Z (mm)'][i]]
        tmp_list = roi_loc(coord_list,vol_atlas_num)
        if len(tmp_list) == 0:
            pass
        else:
            roi_list.extend(tmp_list)
    
    return roi_list

def read_atlas_file(atlas_info):
    '''
    Reads CSV of key, value pairs of enumerated ROIs for some corresponding atlas.
    
    Arguments:
        atlas_info(file): Input CSV file of enumerated ROI key, value pairs
    Returns:
        atlas_dict(dict): Dictionary of atlas key, value pairs
    '''
    
    atlas_info = os.path.abspath(atlas_info)
    df = pd.read_csv(atlas_info,header=None); df.columns = ['key', 'id']
    # df = pd.read_csv(atlas_info,header=None,error_bad_lines=False); df.columns = ['key', 'id']
    atlas_dict = df.set_index('key').to_dict(orient='dict')['id']
    
    return atlas_dict

def remove_ext(file):
    '''
    Removes extension of some input file string. Primarily intended for NIFTI files.
    
    Arguments:
        file(str): Input file name string
    Returns:
        name(str): File name string with extension removed
    '''
    
    if '.nii.gz' in file:
        name = file[:-7]
    elif '.nii' in file:
        name = file[:-4]
    elif '.txt' in file or '.tsv' in file or '.csv' in file:
        name = file
    else:
        name = file
    
    return name

def convert_img_dtype(img,data_type="int"):
    '''
    Converts image data type to some other arbitrary data type. See fslmaths help menu for further details.
    
    Arguments:
        img(NIFTI file): Input NIFTI file
        data_type(str): Output data type (e.g. 'int','float','char','float','double')
    Returns:
        out_file(NIFTI file): NIFTI file with desired data type
    '''
    
    img = os.path.abspath(img)
    out_dir = os.path.dirname(img)
    
    img = remove_ext(img)
    name = os.path.basename(img)
    
    out_file = os.path.join(out_dir,name + ".int" + ".nii.gz")
    
    img_dtype = Command().init_cmd("fslmaths")
    img_dtype.append("-dt")
    img_dtype.append(data_type)
    img_dtype.append(img)
    img_dtype.append(out_file)
    img_dtype.append("-odt")
    img_dtype.append(data_type)
    
    run(img_dtype)
    
    return out_file

def load_atlas_data(nii_atlas,atlas_info,data_type="int"):
    '''
    Loads atlas data from input NIFTI neuroimage atlas and it's corresponding
    enumerated key, value paired atlas CSV file.
    
    Arguments:
        nii_atlas(NIFTI file): Input NIFTI atlas
        atlas_info(file): Corresponding atlas CSV file
        data_type(str): Output data type (e.g. 'int','float','char','float','double')
    Returns:
        atlas_data(numpy array): Atlas data represented as an N x M x P array
        atlas_dict(dict): Atlas dictionary of key, value pairs
    '''
    
    # Load atlas key/ID information
    atlas_dict = read_atlas_file(atlas_info)
    
    # Convert input image from float to int
    int_data = convert_img_dtype(nii_atlas,data_type)
    
    # Load/export data as numpy array
    img = nib.load(int_data)
    atlas_data = img.get_fdata()
    
    # Clean-up
    os.remove(int_data)
    
    return atlas_data,atlas_dict

def make_cluster_vol(nii_file,thresh=0.95,dist=0):
    '''
    Creates enumerated clusters from input NIFTI file and writes the enumerated clusters to a separate NIFTI volume.
    
    Arguments:
        nii_file(NIFTI file): Input NIFTI file
        thresh(float): Minimum threshold 
        dist(float): Minimum distance between clusters
    Returns:
        out_file(NIFTI file): Output NIFTI file of enumerated clusters
        out_stat(file): Corresponding table of enumerated clusters with MNI space mm and vox coordinates
    '''
    
    # Construct file paths
    nii_file = os.path.abspath(nii_file)
    out_dir = os.path.dirname(nii_file)
    
    nii_file = remove_ext(nii_file)
    name = os.path.basename(nii_file)
    out_prefix = os.path.join(out_dir,name + ".cluster")
    
    out_file = out_prefix + ".nii.gz"
    out_stat = out_prefix + ".txt"
    
    # Make cluster(s) from input data
    clust_cmd = Command().init_cmd("cluster")
    clust_cmd.append(f"--in={nii_file}")
    clust_cmd.append(f"--thresh={thresh}")
    clust_cmd.append(f"--peakdist={dist}")
    clust_cmd.append(f"--oindex={out_file}")
    # clust_cmd.append(f"--othresh={out_file}")
    
    run(clust_cmd,out_stat)
    
    return out_file,out_stat

def load_nii_vol(nii_file,thresh=0.95,dist=0):
    '''
    Reads in NIFTI volume information, creates a volume of enumerated clusters, and then stores 
    those clusters in an N x M x P array.
    
    Arguments:
        nii_file(NIFTI file): Input NIFTI file
        thresh(float): Minimum threshold
        dist(float): Minimum distance between clusters
    Returns:
        img_data(numpy array): N x M x P numpy array of the clusters
    '''
    
    # Create volume clusters
    [clust_file,clust_stat] = make_cluster_vol(nii_file,thresh,dist)
    
    # Load/export data as numpy array
    img = nib.load(clust_file)
    img_data = img.get_fdata()
    
    # Clean-up
    os.remove(clust_file)
    os.remove(clust_stat)
    
    return img_data

def get_roi_name(cluster_data,atlas_data,atlas_dict):
    '''
    Finds ROI names from overlapping clusters in a NIFTI volume by voxel matching.
    
    Arguments:
        cluster_data(numpy array): Input numpy of data
        atlas_data(numpy array): Numpy array of labeled surface vertices for some specific hemisphere
        atlas_dict(dict): Dictionary of label IDs to ROI names
    Returns:
        roi_list(list): List of ROIs overlapped by cluster(s)
    '''
    
    # Flatten matrices
    cluster_data = cluster_data.flatten(order='C')
    atlas_data = atlas_data.flatten(order='C')
    
    tmp_list = list()
    roi_list = list()
    
    for idx,val in enumerate(cluster_data):
        if cluster_data[idx] == 0:
            atlas_data[idx] = 0
            
    for i in np.unique(atlas_data)[1:]:
        tmp_list = atlas_dict[i]
        roi_list.append(tmp_list)
        
    return roi_list

def write_spread(file,out_file,roi_list):
    '''
    Writes the contents or roi_list to a spreadsheet.
    
    Arguments:
        file (file): Input CIFTI file
        out_file (file): Output csv file name and path. This file need not exist at runtime.
        roi_list(list): List of ROIs to write to file
    Returns: 
        out_file (csv file): Output csv file name and path.
    '''
    
    # Strip csv file extension from output file name
    if '.csv' in out_file:
        out_file = os.path.splitext(out_file)[0]
        out_file = out_file + '.csv'
    elif '.tsv' in out_file:
        out_file = os.path.splitext(out_file)[0]
        out_file = out_file + '.csv'
    elif '.txt' in out_file:
        out_file = os.path.splitext(out_file)[0]
        out_file = out_file + '.csv'
    else:
        out_file = out_file + '.csv'
    
    # Construct image dictionary
    file = os.path.abspath(file)
    img_dict = {"File":file,
         "ROIs":[roi_list]}
    
    # Create dataframe from image dictionary
    df = pd.DataFrame.from_dict(img_dict,orient='columns')
    
    # Write output CSV file
    if os.path.exists(out_file):
        df.to_csv(out_file, sep=",", header=False, index=False, mode='a')
    else:
        df.to_csv(out_file, sep=",", header=True, index=False, mode='w')
    
    return out_file

def proc_vol(nii_file,out_file,thresh = 0.95, dist = 0, vol_atlas_num = 3, nii_atlas = "", atlas_info = ""):
    '''
    Identifies ROIs that have overlap with some cluster(s) from the input NIFTI file.
    
    Arguments:
        nii_file(NIFTI file): Input NIFTI volume file
        out_file(file): Name for output CSV
        thresh(float): Threshold values below this value
        dist(float): Minimum distance between two or more clusters
        vol_atlas_num(int): Atlas to be used in FSL's `atlasquery`. Number corresponds to an atlas. See FSL's `atlasquery` help menu for details.
        nii_atlas(NIFTI file): NIFTI atlas file
        atlas_info(file): Corresponding CSV key, value pairs of ROIs for atlas file
    Returns:
      out_filefile(file): Output CSV file
    '''
    
    if nii_atlas and atlas_info:
        # Read atlas data and info
        [atlas_data,atlas_dict] = load_atlas_data(nii_atlas,atlas_info)

        # Read NIFTI data and find clusters
        img_data = load_nii_vol(nii_file,thresh,dist)

        # Identify cluster and ROI overlaps
        roi_list = get_roi_name(img_data,atlas_data,atlas_dict)
    else:
        roi_list = vol_clust(nii_file,thresh,dist,vol_atlas_num)
    
    # Write spreadsheet to file
    if len(roi_list) != 0:
        out_file = write_spread(nii_file,out_file,roi_list)
    
    return out_file

def print_atlases():
    '''
    Prints all available atlases in FSL's atlasquery to the command line, in addition to their
    corresponding number to use in nifti_rois.
    '''
    
    atlas_txt = "\n\
    Atlas Numbers (for atlasquery wrapper) \n\
    \n\
    1.  Cerebellar Atlas in MNI152 space after normalization with FLIRT \n\
    2.  Cerebellar Atlas in MNI152 space after normalization with FNIRT \n\
    3.  Harvard-Oxford Cortical Structural Atlas \n\
    4.  Harvard-Oxford Subcortical Structural Atlas \n\
    5.  Human Sensorimotor Tracts Labels \n\
    6.  JHU ICBM-DTI-81 White-Matter Labels \n\
    7.  JHU White-Matter Tractography Atlas \n\
    8.  Juelich Histological Atlas \n\
    9.  MNI Structural Atlas \n\
    10. Mars Parietal connectivity-based parcellation \n\
    11. Mars TPJ connectivity-based parcellation \n\
    12. Neubert Ventral Frontal connectivity-based parcellation \n\
    13. Oxford Thalamic Connectivity Probability Atlas \n\
    14. Oxford-Imanova Striatal Connectivity Atlas 3 sub-regions \n\
    15. Oxford-Imanova Striatal Connectivity Atlas 7 sub-regions \n\
    16. Oxford-Imanova Striatal Structural Atlas \n\
    17. Sallet Dorsal Frontal connectivity-based parcellation \n\
    18. Subthalamic Nucleus Atlas \n\
    19. Talairach Daemon Labels \n"
    
    print(atlas_txt)
    
    return None

if __name__ == "__main__":

    # Check system
    if platform.system().lower() == 'windows':
        print("")
        print("\tThe required software (FSL) is not installable on Windows platforms. Exiting.")
        print("")
        sys.exit(1)

    # Argument parser
    parser = argparse.ArgumentParser(description="Finds NIFTI volume clusters and writes the overlapping ROIs to a CSV file.\n\
\n\
This process can be performed using either one to two methods:\n\
\n\
1. A NIFTI volume file is provided, along with an atlas number to determine which ROI the cluster overlaps (this requires the input NIFTI volume to be in MNI space).\n\
2. A NIFTI volume file is provided, along with a separate atlas NIFTI volume and an enumrated CSV file, that contains the ROI intensity values as a number-ROI pair (this requires the input NIFTI volume to be in this atlas' space.) \n\
\n\
For a list of available atlases, see the '--dump-atlases' option for details.\n\
\n\
Note: enumrated CSV files must not contain Window's carriage returns.",
# usage="use '%(prog)s --help' for more information",
formatter_class=argparse.RawTextHelpFormatter)

    # Parse Arguments
    # Required Arguments
    reqoptions = parser.add_argument_group('Required arguments')
    reqoptions.add_argument('-i', '-in', '--input',
                            type=str,
                            dest="nii",
                            metavar="STATS.nii.gz",
                            required=False,
                            help="NIFTI image file.")
    reqoptions.add_argument('-o', '-out', '--output',
                            type=str,
                            dest="out_file",
                            metavar="OUTPUT.csv",
                            required=False,
                            help="Output spreadsheet name.")

    # Atlasquery options
    atlqoptions = parser.add_argument_group('Atlasquery options')
    atlqoptions.add_argument('--atlas-num',
                            type=int,
                            dest="atlas_num",
                            metavar="INT",
                            required=False,
                            help="Atlas number. See '--dump-atlases' for details.")

    # Stand-alone atlas options
    atlsoptions = parser.add_argument_group('Stand-alone atlas options')
    atlsoptions.add_argument('-a', '-atlas', '--atlas',
                            type=str,
                            dest="atlas",
                            metavar="ATLAS.nii.gz",
                            required=False,
                            help="NIFTI atlas file.")
    atlsoptions.add_argument('-info', '--atlas-info',
                            type=str,
                            dest="info",
                            metavar="ATLAS.info.csv",
                            required=False,
                            help="Atlas information file.")

    # Optional Arguments
    optoptions = parser.add_argument_group('Optional arguments')
    optoptions.add_argument('-t', '-thresh', '--thresh',
                            type=float,
                            dest="thresh",
                            metavar="FLOAT",
                            default=0.95,
                            required=False,
                            help="Cluster threshold. [default: 0.95]")
    optoptions.add_argument('-d', '-dist', '--distance',
                            type=float,
                            dest="dist",
                            metavar="FLOAT",
                            default=0,
                            required=False,
                            help="Minimum distance between clusters. [default: 0]")
    optoptions.add_argument('--dump-atlases',
                            dest="dump_atlases",
                            required=False,
                            action="store_true",
                            help="Prints available atlases and its corresponding atlas number.")

    args = parser.parse_args() 

    # Print help message in the case
    # of no arguments
    try:
        args = parser.parse_args()
    except SystemExit as err:
        if err.code == 2:
            parser.print_help()

    # Run
    if args.dump_atlases:
        print_atlases()
    elif args.nii and args.out_file and args.atlas and args.info:
        args.out_file = proc_vol(nii_file=args.nii,out_file=args.out_file,thresh=args.thresh,dist=args.dist,nii_atlas=args.atlas,atlas_info=args.info)
    elif args.nii and args.out_file and args.atlas_num:
        args.out_file = proc_vol(nii_file=args.nii,out_file=args.out_file,thresh=args.thresh,dist=args.dist,vol_atlas_num=args.atlas_num)
    else:
        print("")
        print("No valid options specified. Please see help menu for details.")
        print("")
        sys.exit(1)
