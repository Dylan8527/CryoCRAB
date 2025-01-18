import datetime
import logging
import json
from tqdm import tqdm
import pandas as pd
import logging
from pathlib import Path
logger = logging.getLogger()

from CryoCRAB.utils import get_project_name, get_project_save_dir
PROJECT_NAME = get_project_name()
PROJECT_SAVE_DIR = get_project_save_dir()

from .step0_empiar_ids import load_empiar_ids
from .helper_func import get_empiar_structure

EMPIAR_STRUCTURE_DIR = Path(PROJECT_SAVE_DIR) / "Data" / "empiar-paths" / "empiar_structure"
EMPIAR_STRUCTURE_FILE = lambda empiar_id: EMPIAR_STRUCTURE_DIR / "{}.json".format(empiar_id.replace("EMPIAR-", ""))

# get_empiar_structure() implemented in CryoCRAB/pipeline/empiar_data_curation/helper_func.py

def save_empiar_structure(empiar_id: str):
    """
    Save the EMPIAR structure for an EMPIAR ID to a json file
    """
    EMPIAR_STRUCTURE_DIR.mkdir(parents=True, exist_ok=True)
    empiar_structure = get_empiar_structure(empiar_id)
    with open(EMPIAR_STRUCTURE_FILE(empiar_id), "w") as f:
        json.dump(empiar_structure, f, indent=4)
        
def load_empiar_structure(empiar_id: str):
    """
    Load the EMPIAR structure for an EMPIAR ID from a json file
    """
    if not EMPIAR_STRUCTURE_FILE(empiar_id).exists():
        logger.warning(f"{PROJECT_NAME} {EMPIAR_STRUCTURE_FILE(empiar_id)} does not exist, save EMPIAR structure first")
        save_empiar_structure(empiar_id)
    with open(EMPIAR_STRUCTURE_FILE(empiar_id), "r") as f:
        empiar_structure = json.load(f)
    logger.debug(f"{PROJECT_NAME} load EMPIAR structure for {empiar_id} from {EMPIAR_STRUCTURE_FILE(empiar_id)}")
    return empiar_structure

def save_empiar_structures():
    """
    Save the EMPIAR structure for each EMPIAR ID to a json file
    """
    empiar_ids = load_empiar_ids()
    logger.debug(f"{PROJECT_NAME} FTP {len(empiar_ids)} EMPIAR IDs")
    for empiar_id in tqdm(empiar_ids, "Crawl EMPIAR structures"):
        if not EMPIAR_STRUCTURE_FILE(empiar_id).exists():
            save_empiar_structure(empiar_id)
    logger.info(f"{PROJECT_NAME} save {len(empiar_ids)} EMPIAR IDs to {EMPIAR_STRUCTURE_DIR}")
    
def load_empiar_structure(empiar_id: str):
    """
    Load the EMPIAR structure for an EMPIAR ID from a json file
    """
    if not EMPIAR_STRUCTURE_FILE(empiar_id).exists():
        logger.warning(f"{PROJECT_NAME} {EMPIAR_STRUCTURE_FILE(empiar_id)} does not exist, save EMPIAR structure first")
        save_empiar_structure(empiar_id)
    with open(EMPIAR_STRUCTURE_FILE(empiar_id), "r") as f:
        empiar_structure = json.load(f)
    logger.info(f"{PROJECT_NAME} load EMPIAR structure for {empiar_id} from {EMPIAR_STRUCTURE_FILE(empiar_id)}")
    return empiar_structure