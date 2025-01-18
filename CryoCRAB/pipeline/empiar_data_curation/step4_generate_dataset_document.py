import os
import datetime
import logging
import json
from tqdm import tqdm
import pandas as pd
import logging
from pymongo.collection import Collection
from pathlib import Path
logger = logging.getLogger()

from CryoCRAB.utils import get_project_name, get_project_save_dir
from CryoCRAB.utils.datatype import *
from CryoCRAB.utils.parallel import start_work_ppe

PROJECT_NAME = get_project_name()
PROJECT_SAVE_DIR = get_project_save_dir()

from .step3_crawl_empiar_emdb_entries import get_empiar_emdb_pair_list, parse_empiar_emdb_pair
from CryoCRAB.utils.mongodb import get_empiar_dataset, update_dataset_col_with_docs, get_spa_micrograph_dataset, get_spa_movie_dataset, micrograph_dataset_filter, movie_dataset_filter

def generate_empiar_dataset_documents_workfn(pair_dict: dict, image_max_num: int=1000):
    """
    Generate the EMPIAR dataset documents
    """
    col = get_empiar_dataset()
    imagesets_doc_list:list[DatasetDocument] = parse_empiar_emdb_pair(pair_dict,image_max_num=image_max_num)
    update_dataset_col_with_docs(col, imagesets_doc_list)
    logger.debug(f"Generated {len(imagesets_doc_list)} dataset documents for {pair_dict['empiar']['name']}")
    return len(imagesets_doc_list)
    
def generate_empiar_dataset_documents(num_workers: int=10, image_max_num: int=1000):
    """
    Generate the EMPIAR dataset documents
    """
    get_empiar_dataset() # try create to avoid error
    empiar_emdb_pair_list = get_empiar_emdb_pair_list()
    start_work_ppe(generate_empiar_dataset_documents_workfn, empiar_emdb_pair_list, show_tqdm=True, num_workers=num_workers, image_max_num=image_max_num)
    
def generate_micrograph_dataset_documents_workfn(pair_dict: dict, image_max_num: int=1000):
    """
    Generate the micrograph dataset documents
    """
    col = get_spa_micrograph_dataset()
    imagesets_doc_list:list[DatasetDocument] = parse_empiar_emdb_pair(pair_dict,image_max_num=image_max_num)
    imagesets_doc_list = [doc for doc in imagesets_doc_list if micrograph_dataset_filter(doc.determination_method, doc.image_category)]
    if len(imagesets_doc_list) > 0:
        update_dataset_col_with_docs(col, imagesets_doc_list)
    logger.debug(f"Generated {len(imagesets_doc_list)} dataset documents for {pair_dict['empiar']['name']}")
    return len(imagesets_doc_list)
    
def generate_micrograph_dataset_documents(num_workers: int=10, image_max_num: int=1000):
    """
    Generate the micrograph dataset documents
    """
    get_spa_micrograph_dataset() # try create to avoid error
    empiar_emdb_pair_list = get_empiar_emdb_pair_list()
    start_work_ppe(generate_micrograph_dataset_documents_workfn, empiar_emdb_pair_list, show_tqdm=True, num_workers=num_workers, image_max_num=image_max_num)
    
def generate_movie_dataset_documents_workfn(pair_dict: dict, image_max_num: int=1000):
    """
    Generate the movie dataset documents
    """
    col = get_spa_movie_dataset()
    imagesets_doc_list:list[DatasetDocument] = parse_empiar_emdb_pair(pair_dict,image_max_num=image_max_num)
    imagesets_doc_list = [doc for doc in imagesets_doc_list if movie_dataset_filter(doc.determination_method, doc.image_category)]
    if len(imagesets_doc_list) > 0:
        update_dataset_col_with_docs(col, imagesets_doc_list)
    logger.debug(f"Generated {len(imagesets_doc_list)} dataset documents for {pair_dict['empiar']['name']}")
    return len(imagesets_doc_list)

def generate_movie_dataset_documents(num_workers: int=10, image_max_num: int=1000):
    """
    Generate the movie dataset documents
    """
    get_spa_movie_dataset() # try create to avoid error
    empiar_emdb_pair_list = get_empiar_emdb_pair_list()
    start_work_ppe(generate_movie_dataset_documents_workfn, empiar_emdb_pair_list, show_tqdm=True, num_workers=num_workers, image_max_num=image_max_num)
