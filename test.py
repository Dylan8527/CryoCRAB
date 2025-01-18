from CryoCRAB import *

import logging 

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pymongo").setLevel(logging.WARNING)

logger = logging.getLogger()
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(message)s')
console_handler.setFormatter(formatter)
logger.handlers=[]
logger.addHandler(console_handler)

from CryoCRAB.utils.mongodb import get_total_image_num_given_dataset, get_empiar_dataset, get_spa_micrograph_dataset, get_spa_movie_dataset

def pipeline_empiar_data_curation():
    print("================================================")
    # Step0: get empiar ids
    empiar_ids = get_empiar_ids()
    empiar_ids = load_empiar_ids()
    empiar_path_csv = load_empiar_path_csv(empiar_ids[0])

    # Step2: get empiar structures
    save_empiar_structures()
    empiar_structure = load_empiar_structure(empiar_ids[0])
    
    # Step3: get empiar path csv
    save_empiar_path_csvs()
    empiar_path_csv = load_empiar_path_csv(empiar_ids[0])
    
    # Step4: get empiar emdb json entries
    save_empiar_emdb_entries()
    empiar_emdb_pair = get_empiar_emdb_pair_list(empiar_ids[0])
    print("================================================\n\n")

def mongodb_dataset_generation():
    print("================================================")
    # Movie Dataset + Micrograph Dataset
    generate_empiar_dataset_documents(num_workers=8, image_max_num=1000)
    # Micrograph Dataset
    generate_micrograph_dataset_documents(num_workers=8, image_max_num=1000)
    # Movie Dataset
    generate_movie_dataset_documents(num_workers=8, image_max_num=1000)
    print("================================================\n\n")

def mongodb_dataset_have_a_look():
    print("================================================")
    # Movie Dataset + Micrograph Dataset
    empiar_dataset = get_empiar_dataset()
    total_image_num = get_total_image_num_given_dataset(empiar_dataset)
    filter_image_num = get_total_image_num_given_dataset(empiar_dataset, image_max_num=1000)
    logger.info("EMPIAR (NOT ONLY SPA) total image num: %d, after filtering: %d", total_image_num, filter_image_num)
    # Micrograph Dataset
    micrograph_dataset = get_spa_micrograph_dataset()
    total_image_num = get_total_image_num_given_dataset(micrograph_dataset)
    filter_image_num = get_total_image_num_given_dataset(micrograph_dataset, image_max_num=1000)
    logger.info("Micrograph total image num: %d, after filtering: %d", total_image_num, filter_image_num)
    # Movie Dataset
    movie_dataset = get_spa_movie_dataset()
    total_image_num = get_total_image_num_given_dataset(movie_dataset)
    filter_image_num = get_total_image_num_given_dataset(movie_dataset, image_max_num=1000)
    logger.info("Movie total image num: %d, after filtering: %d", total_image_num, filter_image_num)
    # Preview suffix
    image_suffix_count_dict, gain_suffix_count_dict = preview_all_suffixes_in_spa_empiar_dataset()
    print(f"{image_suffix_count_dict = }")
    print(f"{gain_suffix_count_dict = }")
    update_empiar_dataset_image_and_gain_suffix()
    print("================================================\n\n")

def cryosparc_data_process():
    from CryoCRAB.utils.datatype import SingleImageTestStatus, CryoCRAB_DataManager, DownloadMode, CryoCRAB_Download_DataType
    from CryoCRAB.pipeline.cryosparc_data_process.helper_func \
        import update_dataset_SingleImageTestStatus, get_ftp_download_path, unset_dataset_SingleImageTestStatus
    from CryoCRAB.utils.cryosparc import get_cryosparc_client
    print("================================================")
    # Step0: single image test for each dataset
    micrograph_dataset = get_spa_micrograph_dataset()
    document = micrograph_dataset.find_one({
        "status.single_image_test": {"$exists": False}, 
        "image_num": {"$gte": 0}
    }) # find one document without tested
    update_dataset_SingleImageTestStatus(micrograph_dataset, document, SingleImageTestStatus.testing)
    
    # download
    update_dataset_SingleImageTestStatus(micrograph_dataset, document, SingleImageTestStatus.downloading)
    cryocrab_datamanager = CryoCRAB_DataManager(DownloadMode.local)
    empiar_ftp_directory = document["empiar_ftp_directory"]
    empiar_relative_directory = document["empiar_relative_directory"]
    empiar_image_relative_path = document["empiar_image_relative_paths"][0]
    ftp_path = get_ftp_download_path(empiar_ftp_directory, empiar_relative_directory, empiar_image_relative_path)
    ftp_file_size, local_file_size = cryocrab_datamanager.download_via_ftp(document["imageset_name"], ftp_path, CryoCRAB_Download_DataType.micrograph)
    if ftp_file_size != local_file_size:
        print(f"Download failed: {ftp_path}")
        unset_dataset_SingleImageTestStatus(micrograph_dataset, document)
        
    cs = get_cryosparc_client()

    # debug 
    unset_dataset_SingleImageTestStatus(micrograph_dataset, document)
    print("================================================\n\n")
    
def main():
    # pipeline_empiar_data_curation()
    # mongodb_dataset_generation()
    # mongodb_dataset_have_a_look()
    cryosparc_data_process()
    pass
    
if __name__ == "__main__":
    from CryoCRAB.utils import get_project_name, get_project_root
    project_root = get_project_root()
    print(f"{project_root = }")
    main()