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
from .step1_empiar_structure import load_empiar_structure
from .helper_func import generate_relative_paths, get_absolute_ftp_path

EMPIAR_PATH_CSV_DIR = Path(PROJECT_SAVE_DIR) / "Data" / "empiar-paths" / "empiar_path_csv" 
EMPIAR_PATH_CSV_FILE = lambda empiar_id: EMPIAR_PATH_CSV_DIR / "{}.csv".format(empiar_id.replace("EMPIAR-", ""))

def save_empiar_path_csv(empiar_id: str):
    """
    Save the EMPIAR path csv for an EMPIAR ID
    """
    empiar_structure = load_empiar_structure(empiar_id)
    relative_paths = generate_relative_paths(empiar_structure)
    ftp_absolute_paths = [get_absolute_ftp_path(empiar_id, path) for path in relative_paths]
    table = pd.DataFrame({"ftp_absolute_path": ftp_absolute_paths, "relative_path": relative_paths})
    table.to_csv(EMPIAR_PATH_CSV_FILE(empiar_id), index=False)
    
def load_empiar_path_csv(empiar_id: str):
    """
    Load the EMPIAR path csv for an EMPIAR ID
    """
    if not EMPIAR_PATH_CSV_FILE(empiar_id).exists():
        logger.warning(f"{PROJECT_NAME} {EMPIAR_PATH_CSV_FILE(empiar_id)} does not exist, save EMPIAR path csv first")
        save_empiar_path_csv(empiar_id)
    table = pd.read_csv(EMPIAR_PATH_CSV_FILE(empiar_id))
    logger.debug(f"{PROJECT_NAME} load EMPIAR path csv for {empiar_id} from {EMPIAR_PATH_CSV_FILE(empiar_id)}")
    return table

def save_empiar_path_csvs():
    """
    Save the EMPIAR path csv for each EMPIAR ID
    """
    empiar_ids = load_empiar_ids()
    logger.info(f"{PROJECT_NAME} FTP {len(empiar_ids)} EMPIAR IDs")
    EMPIAR_PATH_CSV_DIR.mkdir(parents=True, exist_ok=True)
    for empiar_id in tqdm(empiar_ids, "Saving EMPIAR path csvs"):
        if not EMPIAR_PATH_CSV_FILE(empiar_id).exists():
            save_empiar_path_csv(empiar_id)
    logger.info(f"{PROJECT_NAME} save {len(empiar_ids)} EMPIAR path csvs to {EMPIAR_PATH_CSV_DIR}")
    