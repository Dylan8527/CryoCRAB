import datetime
import logging
import json
from tqdm import tqdm
import pandas as pd
import logging
from pathlib import Path
from pymongo.collection import Collection
logger = logging.getLogger()

from CryoCRAB.utils import get_project_name, get_project_save_dir
PROJECT_NAME = get_project_name()
PROJECT_SAVE_DIR = get_project_save_dir()

from CryoCRAB.utils.datatype import SingleImageTestStatus

def get_ftp_download_path(ftp_directory: str, relative_directory: str, relative_path: str):
    """
    Get the FTP download path
    """
    relative_ftp_directory = ftp_directory.replace("ftp.ebi.ac.uk/empiar/world_availability/", "")
    ftp_download_path = Path(relative_ftp_directory) / relative_directory / relative_path
    return str(ftp_download_path)

def update_dataset_SingleImageTestStatus(micrograph_dataset: Collection, document: dict, status: SingleImageTestStatus):
    """
    Update the dataset with the SingleImageTestStatus
    """
    micrograph_dataset.update_one({"_id": document["_id"]}, {"$set": {"status.single_image_test": status}})

def unset_dataset_SingleImageTestStatus(micrograph_dataset: Collection, document: dict):
    """
    Unset the SingleImageTestStatus
    """
    micrograph_dataset.update_one({"_id": document["_id"]}, {"$unset": {"status.single_image_test": ""}})
    
def update_dataset_col_with_docID_key_value(dataset: Collection, docID: str, key: str, value: str):
    """
    Update the dataset collection with the docID key value
    """
    dataset.update_one({"_id": docID}, {"$set": {key: value}})