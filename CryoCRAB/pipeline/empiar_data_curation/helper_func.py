import os 
import time 
import json
import logging 
from ftplib import FTP
from pathlib import Path
from CryoCRAB.utils import EMPIAR
import requests

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

from .empiar_patch import possible_ext_patch, image_paths_ban_words_patch

def process_item_list(item: str):
    """
    Process the item list from the FTP server
    
    Args:
        item: (str) The item list from the FTP server
        
    Returns:
        name: (str) The name of the item
        type_flag: (str) The type of the item, either "directory" or "file"
    """
    parts = item.split()
    name = parts[-1]
    type_flag = parts[0][0]
    if type_flag == 'd':
        return name, "directory"
    else:
        return name, "file"
    
def list_directory(ftp: FTP, path: str):
    """
    List the directory contents of the FTP server
    """
    try:
        ftp.cwd(path)
    except Exception as e:
        print(f"Error changing directory to {path}: {e}")
        return []

    items = []
    ftp.retrlines('LIST', items.append)
    items = sorted(items)
    return items

def mirror_directory(ftp: FTP, path: str=EMPIAR().DIRECTORY):
    """
    Mirror the directory structure of the FTP server
    
    Args:
        ftp: (FTP) The FTP connection
        path: (str) The path to mirror
    """
    # print(path)
    items = list_directory(ftp, path)
    directory_structure = []
    items = [process_item_list(item) for item in items]
    items = sorted(items)
    
    for item, dtype in items:
        if dtype == "file": directory_structure.append(item)
    for item, dtype in items:
        if dtype == "directory":
            files = mirror_directory(ftp, os.path.join(path, item))
            directory_structure.append({item: files})
    return directory_structure

def new_ftp() -> FTP:
    ftp = FTP(timeout=200)
    ftp.connect(EMPIAR().EMPIAR_IP, EMPIAR().PORT)
    ftp.login()
    ftp.cwd(EMPIAR().DIRECTORY)
    ftp.set_debuglevel(0)
    return ftp

def get_all_empiar_ids():
    """
    Get all EMPIAR IDs from the FTP server
    """
    ftp = new_ftp()
    empiar_ids = []
    items = list_directory(ftp, EMPIAR().DIRECTORY)
    items = [process_item_list(item) for item in items]
    items = sorted(items)
    for item, dtype in items:
        if dtype == "directory": empiar_ids.append(item)
    ftp.close()
    return empiar_ids

def get_absolute_ftp_path(empiar_id: str, relateive_path: str):
    """
    Get the absolute path of the file on the FTP server
    
    Args:
        empiar_id: (str) The EMPIAR ID
        relateive_path: (str) The relative path of the file
    """
    base_url=Path("ftp.ebi.ac.uk/empiar/world_availability/")
    return base_url / empiar_id / relateive_path

def generate_relative_paths(data, current_path=Path()):
    """
    Generate relative paths from the directory structure
    
    Args:
        data: (dict) The directory structure
        current_path: (Path) The current path    
    """
    relative_paths = []
    if isinstance(data, dict): # IS Non-final directory
        for key, value in data.items():
            new_path = current_path / key
            relative_paths.extend(generate_relative_paths(value, new_path))
    elif isinstance(data, list): # IS Final directory
        for item in data:
            relative_paths.extend(generate_relative_paths(item, current_path))
    elif isinstance(data, str): # IS File
        complete_path = current_path / data
        relative_paths.append(str(complete_path))
    return relative_paths

def get_empiar_structure(empiar_id: str):
    """
    Get the empiar structure.
    """
    ftp = new_ftp()
    ftp_directory = Path(EMPIAR().DIRECTORY) / empiar_id
    ftp_directory = str(ftp_directory)
    empiar_structure = mirror_directory(ftp, ftp_directory)
    ftp.close()
    return empiar_structure
    
def get_response(
    url: str,
    headers: dict,
    params: dict,
    save_path: Path,
) -> dict:
    """
    Get the response from the URL
    """
    result = None
    for i in range(5):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            time.sleep(1)
            continue
        if save_path is not None:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path_str = str(save_path)
            if save_path_str.endswith("json"):
                result = response.json()
                with open(save_path, 'w') as file:
                    json.dump(result, file, indent=4)
            elif save_path_str.endswith("csv") or save_path_str.endswith("txt"):
                result = response.text
                with open(save_path, 'w') as file:
                    file.write(result)
        else:
            result = response.text
    return result
    
def read_element_safely(src, key, default=""):
    """
    Read the element safely from the source
    """
    value = None
    if type(src) is dict: value = src.get(key, default)
    if value is None: value = default
    return value 

def read_list_safely(src, key, default=[]):
    """
    Read the list safely from the source
    """
    value = read_element_safely(src, key)
    if type(value) is not list: value = [""]
    if len(value) == 0: value = default
    return value

def read_dict_safely(src, key)-> dict:
    """
    Read the dictionary safely from the source
    """
    value = read_element_safely(src, key)
    if type(value) is not dict: value = {}
    return value

def data_format_to_possible_ext(dataset_name, data_format):
    """
    Get the possible extensions from the data format
    """
    if data_format == "EER": possible_ext = [".eer"]
    elif data_format == "TIFF": possible_ext = [".tif", ".tiff", ".tif.bz2", ".tiff.bz2", ".tif.gz", ".tiff.gz"]
    elif data_format in ["MRC", "MRCS"]: possible_ext = [".mrc", ".mrc.bz2", ".mrc.gz", ".mrcs", ".mrcs.bz2", ".mrcs.gz"] # import bz2, gzip
    elif data_format == "SPIDER": possible_ext = [".dat"]
    elif data_format == "IMAGIC": possible_ext = [".img"]
    elif data_format == "DM4": possible_ext = [".dm4"]
    elif data_format == "Other": possible_ext = [".eer"] + [".tif", ".tiff", ".tif.bz2", ".tiff.bz2", ".tif.gz", ".tiff.gz"] + [".mrc", ".mrc.bz2", ".mrc.gz"] + [".mrcs", ".mrcs.bz2", ".mrcs.gz"] + [".dat"] + [".img"] + [".dm4"]
    elif data_format == "BIG DATA VIEWER HDF5": possible_ext = [".hdf"]
    elif data_format == "SMV": possible_ext = [".zip"]
    elif data_format == "JPEG": possible_ext = [".jpg"]
    elif data_format == "EM": possible_ext = [".em"]
    elif data_format == "PNG": possible_ext = [".png"]
    elif data_format == "TPX3": possible_ext = [".tpx3"]
    elif data_format == "DM3": possible_ext = [".dm3"]
    else: possible_ext = []
    possible_ext = possible_ext_patch(dataset_name, possible_ext)
    return possible_ext

def filter_paths(paths: list[str], ban_list: list):
    """
    Filter the paths based on the ban list
    """
    filtered_paths = [rel_path for rel_path in paths if all(ban.lower() not in rel_path.lower() for ban in ban_list)]
    return filtered_paths


def get_image_paths_of_empiar_imageset(data_format: str, dataset_name: str, data_directory: str, rel_paths: list[str]):
    possible_ext = data_format_to_possible_ext(dataset_name, data_format)
    def path_match(path:str, dir:str, exts:list[str]):
        """
        Check if the path matches the directory and extensions
        """
        path_str = str(path)
        dir_match = path_str.startswith(dir)
        ext_match = any([path_str.lower().endswith(ext) for ext in exts])
        return dir_match and ext_match
    rel_paths = [path for path in rel_paths if path_match(path, data_directory, possible_ext)]
    image_paths_ban_words = image_paths_ban_words_patch(dataset_name, ["particles"])
    rel_paths = sorted(filter_paths(rel_paths, image_paths_ban_words))
    if not data_directory.endswith("/"): 
        data_directory = data_directory + "/"
    rel_paths = [path[len(data_directory):] for path in rel_paths]
    return rel_paths

def get_gain_paths_of_empiar_imageset(rel_paths: list[str]):
    def path_match(path: str, parts: list[str], exts: list[str]):
        """
        Check if the path matches the parts and extensions
        """
        path_str = str(path).lower()
        part_match = any(part in path_str for part in parts)
        ext_match = any([path_str.endswith(ext) for ext in exts])
        return part_match and ext_match
    parts = ["superref", "gain", "norm", "reference", "countref"]
    possible_ext = [".dm4", ".gain", ".mrc"]
    rel_paths = [path for path in rel_paths if path_match(path, parts, possible_ext)]
    rel_paths = sorted(filter_paths(rel_paths, ["defects", "dark"]))
    return rel_paths

def is_none(v):
    return v is None or (type(v) == str and v == "")
def str_default(v):
    if is_none(v): v = ""
    return str(v)
def int_default(v):
    if is_none(v): v = 0
    return int(v)
def float_default(v):
    if is_none(v): v = 0.0
    return float(v)