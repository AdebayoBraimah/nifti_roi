#!/usr/bin/env python 

# Import modules
import os
import re
import numpy as np
import nibabel as nib
import pandas as pd
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

def load_hemi_labels(file,wb_struct,map_number=1):
    '''
    Loads left or right hemisphere of CIFTI dlabel (dense label) file.
    
    Arguments:
        file(file): Input CIFTI dlabel file
        wb_struct(str): Structure - valid inputs are either: CORTEX_LEFT or CORTEX_RIGHT
        map_number(int): Map number of the input CIFTI dlabel map
    Returns:
        atlas_data(numpy array): Numpy array of labeled surface vertices for some specific hemisphere
        atlas_dict(dict): Dictionary of label IDs to ROI names
    '''
    
    gii_label = 'data.label.gii'
    
    load_label = Command().init_cmd("wb_command"); load_label.append("-cifti-separate")
    
    load_label.append(file)
    load_label.append("COLUMN")
    load_label.append("-label"); load_label.append(wb_struct)
    load_label.append(gii_label)
    
    run(load_label)
    
    gifti_img = nib.load(gii_label)
    
    atlas_data = gifti_img.get_arrays_from_intent('NIFTI_INTENT_LABEL')[map_number-1].data
    atlas_dict = gifti_img.get_labeltable().get_labels_as_dict()
    
    os.remove(gii_label)
    
    return atlas_data,atlas_dict

def load_gii_data(file,intent='NIFTI_INTENT_NORMAL'):
    '''
    Loads GIFTI surface/metric data (.func or .shape) and stores the 
    data as NxMxP numpy array - in which N = X dimensions, M = Y 
    dimensions, and P = the number of TRs or timepoints of the input 
    GIFTI data.
    
    Arguments:
        file(file): Input GIFTI surface/metric file
        intent(str): File read intention for nibabel i/o module
    Returns:
        data(numpy array): Numpy array of data for GIFTI file
    '''
    
    # Load surface data
    surf_dist_nib = nib.load(file)
    
    # Number of TRs in data
    num_da = surf_dist_nib.numDA
    
    # Read all arrays and concatenate temporally
    array1 = surf_dist_nib.get_arrays_from_intent(intent)[0]
    
    data = array1.data
    
    if num_da >= 1:
        for da in range(1,num_da):
            data = np.vstack((data,surf_dist_nib.get_arrays_from_intent(intent)[da].data))
            
    # Transpose data such that vertices are organized by TR
    data = np.transpose(data)
    
    # If output is 1D, make it 2D
    if len(data.shape) == 1:
        data = data.reshape(data.shape[0],1)
        
    return data

def load_hemi_data(file,wb_struct):
    '''
    Wrapper function for `load_gii_data`:
    Loads GIFTI surface/metric data (.func or .shape) and stores the 
    data as NxMxP numpy array - in which N = X dimensions, M = Y 
    dimensions, and P = the number of TRs or timepoints of the input 
    GIFTI data.
    
    Arguments:
        file(file): Input GIFTI surface/metric file
        wb_struct(str): Structure - valid inputs are either: CORTEX_LEFT or CORTEX_RIGHT
    Returns:
        data(numpy array): Numpy array of data for GIFTI file
    '''
    
    gii_data = 'data.func.gii'
    
    load_gii = Command().init_cmd("wb_command"); load_gii.append("-cifti-separate")
    
    load_gii.append(file)
    load_gii.append("COLUMN")
    load_gii.append("-metric"); load_gii.append(wb_struct)
    load_gii.append(gii_data)
    
    run(load_gii)
    
    data = load_gii_data(gii_data)
    
    os.remove(gii_data)
    
    return data

def get_roi_name(cluster_data,atlas_data,atlas_dict):
    '''
    Finds ROI names from overlapping clusters on the cortical surface via
    vertex matching.
    
    Arguments:
        cluster_data(numpy array): Input CIFTI dlabel file
        atlas_data(numpy array): Numpy array of labeled surface vertices for some specific hemisphere
        atlas_dict(dict): Dictionary of label IDs to ROI names
    Returns:
        roi_list(list): List of ROIs overlapped by cluster(s)
    '''
    
    # for idx,val in enumerate(cluster_data.astype(int)):
    for idx,val in enumerate(cluster_data):
        if cluster_data[idx] == 0:
            atlas_data[idx] = 0
    
    tmp_list = list()
    roi_list = list()
    
    for i in np.unique(atlas_data)[1:]:
        # print(atlas_dict[i])
        tmp_list = atlas_dict[i]
        roi_list.append(tmp_list)
    
    return roi_list

def find_clusters(file,left_surf,right_surf,thresh = 1.77,distance = 20):
    '''
    Loads left or right hemisphere of CIFTI dscalar (dense scalar) file and identifies clusters
    and returns a numpy array of the clusters' vertices.
    
    Arguments:
        file(file): Input CIFTI dscalar file
        left_surf(file): Left surface file (preferably midthickness file)
        right_surf(file): Rigth surface file (preferably midthickness file)
        thresh(float): Threshold values below this value
        distance(float): Minimum distance between two or more clusters
    Returns:
        cii_data(numpy array): Numpy array of surface vertices
    '''
    
    cii_data = 'clusters.dscalar.nii'
    
    thresh = str(thresh)
    distance = str(distance)
    
    find_cluster = Command().init_cmd("wb_command"); find_cluster.append("-cifti-find-clusters")
    find_cluster.append(file)
    find_cluster.append(thresh); find_cluster.append(distance)
    find_cluster.append(thresh); find_cluster.append(distance)
    find_cluster.append("COLUMN")
    find_cluster.append(cii_data)
    find_cluster.append("-left-surface")
    find_cluster.append(left_surf)
    find_cluster.append("-right-surface")
    find_cluster.append(right_surf)
    
    run(find_cluster)
    
    return cii_data

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
        pass
    
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

def proc_hemi(gii_data, gii_atlas, wb_struct):
    '''
    Wrapper function for `load_hemi_labels`, `load_hemi_data`, and `get_roi_name`:
    
    Loads GIFTI data to find the names or ROIs that overlap with clusters for some hemisphere
    
    Arguments:
        gii_data(file): Input GIFTI file
        gii_atlas(file): Input GIFTI atlas label file
        wb_struct(str): Structure - valid inputs are either: CORTEX_LEFT or CORTEX_RIGHT
    Returns:
        roi_list(list): List of ROIs that overlap with CIFTI cluster
    '''
       
    
    # Get atlas information
    [atlas_data,atlas_dict] = load_hemi_labels(gii_atlas,wb_struct)
    
    # Get cluster data
    cluster_data = load_hemi_data(gii_data, wb_struct)
    
    # Get ROI names from overlapping cluster(s)
    roi_list = get_roi_name(cluster_data,atlas_data,atlas_dict)
    
    return roi_list

def roi_loc(coords,vol_atlas="Harvard-Oxford Subcortical Structural Atlas"):
    '''
    Uses input list of X,Y,Z MNI space mm coordinates to identify ROIs.
    
    NOTE: External bash script is used. Atlas option is hard-coded.
    
    Arguments:
        coords(list): Coordinate list with a lenth of 3 that corresponds to the XYZ coordinates of some ROI in MNI space.
        vol_atlas(str): Atlas to be used in FSL's `atlasquery`. See FSL's `atlasquery` help menu for details.
        
    Returns:
        roi_list(list): List of ROIs generated from input coordinates.
    '''
    
    roi_list = list()
    out_file = "subcort.rois.txt"
    
    if len(coords) == 3:
        atlasq_cmd = os.path.join(scripts_dir,"atlasq.sh")
        atlasq = Command().init_cmd(atlasq_cmd)
        atlasq.append(f"--coord")
        atlasq.append(f"\"{coords[0]},{coords[1]},{coords[2]}\"")
        # atlasq.append(f"--atlas=\"{vol_atlas}\"")
    
        run(atlasq,out_file)

        with open(out_file,"r") as file:
            text = file.readlines()
            for i in range(0,len(text)):
                text[i] = re.sub(f"<b>{vol_atlas}</b><br>","",text[i].rstrip())

        os.remove(out_file)
        
        if len(text) == 0:
            pass
        else:
            roi_list.extend(text) 
        
    return roi_list

def vol_clust(nii_file,thresh=1.77,dist=20,vol_atlas="Harvard-Oxford Subcortical Structural Atlas"):
    '''
    Identifies clusters in a volumetric (NIFTI) file (specifically for subcortical volumes).
    
    Arguments:
        nii_file(file): Input NIFTI file
        thresh(float): Cluster minimum threshold
        dist(float): Minimum distance between clusters
        vol_atlas(str): Atlas to be used in FSL's `atlasquery`. See FSL's `atlasquery` help menu for details.
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
        tmp_list = roi_loc(coord_list,vol_atlas)
        if len(tmp_list) == 0:
            pass
        else:
            roi_list.extend(tmp_list)
    
    return roi_list

def load_vol_data(file,thresh=1.77,dist=20,vol_atlas="Harvard-Oxford Subcortical Structural Atlas"):
    '''
    Creates (subcortical) NIFTI volumetric data from input CIFTI, followed by identifying the ROIs that
    are overlapped by clusters.
    
    Arguments:
        file(file): Input CIFTI file
        thresh(float): Cluster minimum threshold
        dist(float): Minimum distance between clusters
        vol_atlas(str): Atlas to be used in FSL's `atlasquery`. See FSL's `atlasquery` help menu for details.
    Returns:
        roi_list(list): List of ROIs that overlap with some given cluster
    '''
    
    vol_data = 'data.nii.gz'
    
    load_vol = Command().init_cmd("wb_command"); load_vol.append("-cifti-separate")
    
    load_vol.append(file)
    load_vol.append("COLUMN")
    load_vol.append("-volume-all")
    load_vol.append(vol_data)
    
    run(load_vol)
    
    roi_list = vol_clust(vol_data,thresh,dist,vol_atlas)
    
    os.remove(vol_data)
    
    return roi_list

def proc_stat_cluster(cii_file,cii_atlas,out_file,left_surf,right_surf,thresh=1.77,distance=20,vol_atlas="Harvard-Oxford Subcortical Structural Atlas"):
    '''
    Identifies ROIs that have overlap with some cluster(s) from the input CIFTI file.
    
    Arguments:
        cii_file(file): Input CIFTI dscalar file
        cii_atlas(file): Input CIFTI dlabel (atlas) file
        out_file(file): Name for output CSV file
        left_surf(file): Left surface file (preferably midthickness file)
        right_surf(file): Rigth surface file (preferably midthickness file)
        thresh(float): Threshold values below this value
        distance(float): Minimum distance between two or more clusters
        vol_atlas(str): Atlas to be used in FSL's `atlasquery`. See FSL's `atlasquery` help menu for details.
    Returns:
        out_file(file): Output CSV file
    '''
    
    # Isolate cluster data
    cii_data = find_clusters(cii_file,left_surf,right_surf,thresh,distance)
    
    # Significant cluster overlap ROI list
    roi_list = list()
    tmp_list = list()
    
    # Iterate through wb_structures
    wb_structs = ["CORTEX_LEFT","CORTEX_RIGHT"]
    
    for wb_struct in wb_structs:
        tmp_list = proc_hemi(cii_data,cii_atlas,wb_struct)
        # roi_list.append(tmp_list)
        # roi_list.extend(tmp_list)
        if len(tmp_list) == 0:
            pass
        else:
            roi_list.extend(tmp_list)
    
    os.remove(cii_data)
    
    if platform.system().lower() != 'windows':
        tmp_list = load_vol_data(cii_file,thresh,distance,vol_atlas)
    
    if len(tmp_list) == 0:
        pass
    else:
        roi_list.extend(tmp_list)
    
    # Write output spreadsheet of ROIs
    if len(roi_list) != 0:
        out_file = write_spread(cii_file,out_file,roi_list)
        
    return out_file                                                             

if __name__ == "__main__":

    # Argument parser
    parser = argparse.ArgumentParser(description='Finds cifti surface clusters and writes the overlapping ROIs to a CSV file.')

    # Parse Arguments
    # Required Arguments
    reqoptions = parser.add_argument_group('Required arguments')
    reqoptions.add_argument('-i', '-in', '--input',
                            type=str,
                            dest="cii_file",
                            metavar="STATS.dscalar.nii",
                            required=True,
                            help="Cifti image file.")
    reqoptions.add_argument('-o', '-out', '--output',
                            type=str,
                            dest="out_file",
                            metavar="OUTPUT.csv",
                            required=True,
                            help="Output spreadsheet name.")
    reqoptions.add_argument('-l', '-left', '--left-surface',
                            type=str,
                            dest="left_gii",
                            metavar="GII",
                            required=True,
                            help="Input left gifti surface.")
    reqoptions.add_argument('-r', '-right', '--right-surface',
                            type=str,
                            dest="right_gii",
                            metavar="GII",
                            required=True,
                            help="Input right gifti surface.")
    reqoptions.add_argument('-a', '-atlas', '--atlas',
                            type=str,
                            dest="atlas",
                            metavar="ATLAS.dlabel.nii",
                            required=True,
                            help="Cifti atlas file.")

    # Optional Arguments
    optoptions = parser.add_argument_group('Optional arguments')
    optoptions.add_argument('-t', '-thresh', '--thresh',
                            type=float,
                            dest="thresh",
                            metavar="FLOAT",
                            default=1.77,
                            required=False,
                            help="Cluster threshold.")
    optoptions.add_argument('-d', '-dist', '--distance',
                            type=float,
                            dest="dist",
                            metavar="FLOAT",
                            default=20,
                            required=False,
                            help="Minimum distance between clusters.")

    args = parser.parse_args()

    # Print help message in the case
    # of no arguments
    try:
        args = parser.parse_args()
    except SystemExit as err:
        if err.code == 2:
            parser.print_help()

    # Run
    args.out_file = proc_stat_cluster(cii_file=args.cii_file,cii_atlas=args.atlas,out_file=args.out_file,left_surf=args.left_gii,right_surf=args.right_gii,thresh=args.thresh,distance=args.dist)
