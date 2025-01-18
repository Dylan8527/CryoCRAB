import os
import datetime
import logging
import json
import mrcfile 
from typing import Union
from tqdm import tqdm
import pandas as pd
import numpy as np
import logging
from pymongo.collection import Collection
from pathlib import Path
logger = logging.getLogger()

from . import get_project_name, get_project_save_dir

PROJECT_NAME = get_project_name()
PROJECT_SAVE_DIR = get_project_save_dir()

from .datatype import CryoCRAB_Image_SuffixType, CryoCRAB_Gain_SuffixType

SUFFIXTYPE = Union[CryoCRAB_Image_SuffixType, CryoCRAB_Gain_SuffixType]
FILEPATH = Union[str, Path]

class IO:
    def __init__(self, suffixtype: SUFFIXTYPE):
        self.suffixtype = suffixtype
    
    def read(self, filepath: FILEPATH, dtype=np.float16):
        """
        Read data
        """
        pass 
    
    def write(self, filepath: FILEPATH, data: np.ndarray, dtype=np.float16):
        """
        Write data
        """
        pass
    
class MRC_IO(IO):
    def __init__(self):
        super().__init__(CryoCRAB_Image_SuffixType.mrc)
    
    def read(self, filepath: FILEPATH, dtype=np.float16):
        """
        Read MRC file
        """
        try:
            with mrcfile.open(filepath, mode='r+', permissive=True) as mrc:
                data = mrc.data.astype(dtype)
                header = mrc.header
        except Exception as e:
            data = None 
            header = None 
            logger.warning(f"Could not read MRC file {filepath}")
        return data, header

    def write(self, filepath: FILEPATH, data: np.ndarray, dtype=np.float16):
        """
        Write MRC file
        """
        try:
            with mrcfile.new(filepath, overwrite=True) as mrc:
                mrc.set_data(data.astype(dtype))
        except Exception as e:
            logger.warning(f"Could not write MRC file {filepath}")

