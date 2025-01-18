import os
import enum 
import logging 
import numpy as np
from pydantic import BaseModel
from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from motor.motor_asyncio import AsyncIOMotorClient

from .datatype import *

logger = logging.getLogger()

def get_mongo_client_info():
    """
    Get the MongoDB client info
    """
    CRYOCRAB_MONGODB_HOST = os.getenv("CRYOCRAB_MONGODB_HOST", None)
    CRYOCRAB_MONGODB_PORT = os.getenv("CRYOCRAB_MONGODB_PORT", None) 
    CRYOCRAB_MONGODB_DBNAME = os.getenv("CRYOCRAB_MONGODB_DBNAME", None)
    if CRYOCRAB_MONGODB_HOST is None or CRYOCRAB_MONGODB_PORT is None or CRYOCRAB_MONGODB_DBNAME is None:
        logger.error(f"Please set CRYOCRAB_MONGODB_HOST and CRYOCRAB_MONGODB_PORT and CRYOCRAB_MONGODB_DBNAME in the environment variables")
        exit()
    return CRYOCRAB_MONGODB_HOST, int(CRYOCRAB_MONGODB_PORT), CRYOCRAB_MONGODB_DBNAME

def get_dataset(collection_name: str, async_motor=False):
    """
    Get the dataset
    """
    host, port, dbname = get_mongo_client_info()
    if not async_motor:
        return MongoClient(host, port)[dbname][collection_name]
    else:
        client = AsyncIOMotorClient(f"mongodb://{host}:{port}")
        return client[dbname][collection_name]

def get_empiar_dataset(async_motor=False):
    """
    Get the EMPIAR dataset
    """
    return get_dataset("empiar_dataset", async_motor=async_motor)
    
def get_spa_micrograph_dataset(async_motor=False):
    """
    Get the micrograph dataset
    """
    return get_dataset("micrograph_dataset", async_motor=async_motor)


def get_spa_movie_dataset(async_motor=False):
    """
    Get the movie dataset
    """
    return get_dataset("movie_dataset", async_motor=async_motor)

def get_total_image_num_given_dataset(collection: Collection, image_max_num=np.inf):
    """
    Get the total image number
    """
    # sum the image_num 
    total_image_num = 0
    for doc in collection.find({}, {"image_num": 1}):
        total_image_num += min(doc["image_num"], image_max_num)
    return total_image_num

def update_dataset_col_with_docs(col: Collection, docs: list[DatasetDocument]):
    """
    Update the dataset collection with the documents
    """
    update_ops = []
    for doc in docs:
        doc_json = doc.model_dump()
        doc_json.pop("id")
        update_ops.append(UpdateOne({"imageset_name": doc.imageset_name}, {"$set": doc_json}, upsert=True))
    col.bulk_write(update_ops)

def micrograph_dataset_filter(
    determination_method: DeterminationMethod, 
    image_category: ImageCategory,    
):
    """
    Filter the micrograph dataset
    """
    if determination_method != DeterminationMethod.spa:
        return False # only single particle analysis
    if image_category not in [ImageCategory.singleframe_micrographs, ImageCategory.singleframe_micrographs_nondw, ImageCategory.singleframe_micrographs_nondw2]:
        return False # only single frame micrographs
    return True
 
def movie_dataset_filter(
    determination_method: DeterminationMethod, 
    image_category: ImageCategory,    
):
    """
    Filter the movie dataset
    """
    if determination_method != DeterminationMethod.spa:
        return False # only single particle analysis
    if image_category not in [ImageCategory.multiframe_micrographs]:
        return False # only single frame movies
    return True
