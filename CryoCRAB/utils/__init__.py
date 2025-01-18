import os 
import sys
from pydantic import BaseModel
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
print(PROJECT_ROOT)
def get_project_root():
    return PROJECT_ROOT

PROJECT_NAME = "CryoCRAB"
def get_project_name():
    return PROJECT_NAME

class EMPIAR(BaseModel):
    EMPIAR_IP:str = "193.62.193.165"
    PORT:int = 21
    DIRECTORY:str = "/empiar/world_availability"
    
def get_project_save_dir():
    PROJECT_SAVE_DIR=os.getenv("CRYOCRAB_PROJECT_SAVE_DIR", None)
    if PROJECT_SAVE_DIR is None:
        raise ValueError(f"PROJECT_SAVE_DIR is not set. Please set it in the environment variable CRYOCRAB_PROJECT_SAVE_DIR.")
    PROJECT_SAVE_DIR = Path(PROJECT_SAVE_DIR)
    assert not PROJECT_SAVE_DIR.is_file(), f"PROJECT_SAVE_DIR is a file, not a directory."
    assert PROJECT_SAVE_DIR.parts[-1] != "Data", "Do you add extra 'Data' folder in the path?"
    return PROJECT_SAVE_DIR
