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

from .helper_func import get_all_empiar_ids

EMPIAR_IDS_FILE = Path(PROJECT_SAVE_DIR) / "Data" / "empiar-paths" / "empiar_ids.csv"

def get_empiar_ids():
    """
    Get all EMPIAR IDs from the FTP server, also print the time taken
    """
    
    empiar_ids = get_all_empiar_ids()
    empiar_ids = sorted(empiar_ids)
    current_time = datetime.datetime.now()
    logger.info(f"{PROJECT_NAME} get {len(empiar_ids)} EMPIAR IDs at {current_time}")
    return empiar_ids
    
def save_empiar_ids():
    """
    Save the EMPIAR IDs to a file
    """
    empiar_ids = get_all_empiar_ids()
    empiar_ids_df = pd.DataFrame(empiar_ids, columns=["empiar_id"])
    empiar_ids_df["empiar_id"] = empiar_ids_df["empiar_id"].apply(lambda x: "EMPIAR-{}".format(x))
    EMPIAR_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    empiar_ids_df.to_csv(EMPIAR_IDS_FILE, index=False)
    logger.info(f"{PROJECT_NAME} save {len(empiar_ids)} EMPIAR IDs to {EMPIAR_IDS_FILE}")
    
def load_empiar_ids():
    """
    Load the EMPIAR IDs from a file
    """
    if not EMPIAR_IDS_FILE.exists():
        logger.warning(f"{PROJECT_NAME} {EMPIAR_IDS_FILE} does not exist, save EMPIAR IDs first")
        save_empiar_ids()
    empiar_ids_df = pd.read_csv(EMPIAR_IDS_FILE)
    empiar_ids = empiar_ids_df["empiar_id"].tolist()
    logger.debug(f"{PROJECT_NAME} load {len(empiar_ids)} EMPIAR IDs from {EMPIAR_IDS_FILE}")
    return empiar_ids
