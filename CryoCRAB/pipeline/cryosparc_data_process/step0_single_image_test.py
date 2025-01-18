import datetime
import logging
import json
import os
from tqdm import tqdm
import pandas as pd
import logging
import matplotlib.pyplot as plt
from pathlib import Path
logger = logging.getLogger()

from ...utils import get_project_name, get_project_save_dir
PROJECT_NAME = get_project_name()
PROJECT_SAVE_DIR = get_project_save_dir()

from ...utils.datatype import DeterminationMethod
from ...utils.mongodb import get_spa_micrograph_dataset, get_empiar_dataset
from ...utils.datatype import SingleImageTestStatus, CryoCRAB_DataManager, CryoCRAB_Download_DataType

from .helper_func import get_ftp_download_path, update_dataset_SingleImageTestStatus, unset_dataset_SingleImageTestStatus, update_dataset_col_with_docID_key_value

def preview_all_suffixes_in_spa_empiar_dataset(apply_image_max_num_filter=False):
    """
    Preview all suffixes in the SPA EMPIAR dataset
    """
    empiar_dataset = get_empiar_dataset()
    document = empiar_dataset.find({"determination_method": DeterminationMethod.spa})
    image_suffix_list = []
    gain_suffix_list = []
    for doc in tqdm(document, "Preview image/gain suffix"):
        if apply_image_max_num_filter:
            image_suffix_list+=[os.path.splitext(image_path)[1] for image_path in doc["empiar_image_relative_paths"]]
            gain_suffix_list+=[os.path.splitext(gain_path)[1] for gain_path in doc["empiar_gain_relative_paths"]]
        else:
            if doc["image_num"] > 0:
                image_suffix_list += [os.path.splitext(doc["empiar_image_relative_paths"][0])[1]] * doc["image_num"]
            if doc["gain_num"] > 0:
                gain_suffix_list += [os.path.splitext(doc["empiar_gain_relative_paths"][0])[1]] * doc["gain_num"]
    image_suffix_count_dict = dict()
    for suffix in set(image_suffix_list):
        image_suffix_count_dict[suffix] = image_suffix_list.count(suffix)
    gain_suffix_count_dict = dict()
    for suffix in set(gain_suffix_list):
        gain_suffix_count_dict[suffix] = gain_suffix_list.count(suffix)
    # plot histograms
    fig, ax = plt.subplots(2, 1, figsize=(10, 10))
    ax[0].bar(image_suffix_count_dict.keys(), image_suffix_count_dict.values())
    ax[0].set_title("Image suffix count")
    ax[1].bar(gain_suffix_count_dict.keys(), gain_suffix_count_dict.values())
    ax[1].set_title("Gain suffix count")
    plt.tight_layout()
    plt.show()
    return image_suffix_count_dict, gain_suffix_count_dict

def update_empiar_dataset_image_and_gain_suffix():
    
    empiar_dataset = get_empiar_dataset()
    document = empiar_dataset.find()
    for doc in tqdm(document, "Update image/gain suffix"):
        if doc["image_num"] > 0:
            image_suffix = os.path.splitext(doc["empiar_image_relative_paths"][0])[1]
            update_dataset_col_with_docID_key_value(empiar_dataset, doc["_id"], "image_suffix", image_suffix)
        if doc["gain_num"] > 0:
            gain_suffix = os.path.splitext(doc["empiar_gain_relative_paths"][0])[1]
            update_dataset_col_with_docID_key_value(empiar_dataset, doc["_id"], "gain_suffix", gain_suffix)
            
def micrograph_dataset_processing_single_image_test():
    
    micrograph_dataset = get_spa_micrograph_dataset()
    document = micrograph_dataset.find_one({
        "status.single_image_test": {"$exists": False}, 
        "image_num": {"$gte": 0}
    }) # find one document without tested
    update_dataset_SingleImageTestStatus(micrograph_dataset, document, SingleImageTestStatus.testing)
    
    # download
    update_dataset_SingleImageTestStatus(micrograph_dataset, document, SingleImageTestStatus.downloading)
    cryocrab_datamanager = CryoCRAB_DataManager()
    empiar_ftp_directory = document["empiar_ftp_directory"]
    empiar_relative_directory = document["empiar_relative_directory"]
    empiar_image_relative_path = document["empiar_image_relative_paths"][0]
    ftp_path = get_ftp_download_path(empiar_ftp_directory, empiar_relative_directory, empiar_image_relative_path)
    ftp_file_size, local_file_size = cryocrab_datamanager.download_via_ftp(document["imageset_name"], ftp_path, CryoCRAB_Download_DataType.micrograph)
    
    if ftp_file_size == local_file_size:
        pass         

    # debug 
    unset_dataset_SingleImageTestStatus(micrograph_dataset, document)