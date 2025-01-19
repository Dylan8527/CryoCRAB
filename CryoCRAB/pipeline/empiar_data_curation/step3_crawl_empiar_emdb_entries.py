import datetime
import logging
import json
from tqdm import tqdm
import pandas as pd
import logging
from pathlib import Path
logger = logging.getLogger()

from CryoCRAB.utils import get_project_name, get_project_save_dir
from CryoCRAB.utils.datatype import *
PROJECT_NAME = get_project_name()
PROJECT_SAVE_DIR = get_project_save_dir()

from .step0_empiar_ids import load_empiar_ids
from .step2_empiar_path_csv import load_empiar_path_csv
from .helper_func import  get_response, read_list_safely, read_dict_safely, read_element_safely, get_image_paths_of_empiar_imageset, get_gain_paths_of_empiar_imageset, is_none, str_default, int_default, float_default
from .empiar_patch import empiar_id_patch, data_format_patch

EMPIAR_ENTRY_DIR = Path(PROJECT_SAVE_DIR) / "Data" / "empiar-emdb-entries" / "empiar_entry"
EMPIAR_ENTRY_FILE = lambda empiar_id: EMPIAR_ENTRY_DIR / "{}.json".format(empiar_id)

def save_empiar_entry(empiar_id:str, save_path: str):
    """
    Save the EMPIAR entry
    """
    try:
        get_response(
            url=f'https://www.ebi.ac.uk/empiar/api/entry/{empiar_id}',
            headers={'accept': 'application/json','X-CSRFToken': '4qs1WOHLU4Epq1gxkJjhspJV3MWpMxuMlCSBCSrmuGvH6n06O4h21aoSAhC719II','Cache-Control': 'no-cache','Pragma': 'no-cache'},
            params={},
            save_path=save_path,
        )
    except Exception as e:
        logger.warning(f"Error saving EMPIAR entry {empiar_id}: {e}")
        
def load_empiar_entry(empiar_id: str):
    """
    Load the EMPIAR entry
    """
    if not EMPIAR_ENTRY_FILE(empiar_id).exists():
        logger.warning(f"{PROJECT_NAME} {EMPIAR_ENTRY_FILE(empiar_id)} does not exist, save EMPIAR entry first")
        save_empiar_entry(empiar_id, EMPIAR_ENTRY_FILE(empiar_id))
    with open(EMPIAR_ENTRY_FILE(empiar_id), "r") as f:
        empiar_entry = json.load(f)
    logger.debug(f"{PROJECT_NAME} load EMPIAR entry for {empiar_id} from {EMPIAR_ENTRY_FILE(empiar_id)}")
    return empiar_entry[empiar_id]    

EMDB_ENTRY_DIR = Path(PROJECT_SAVE_DIR) / "Data" / "empiar-emdb-entries" / "emdb_entry"
EMDB_ENTRY_FILE = lambda empiar_id, emdb_id: EMDB_ENTRY_DIR / empiar_id / "{}.json".format(emdb_id)

def save_emdb_entry(emdb_id: str, save_path: str):
    """
    Save the EMDB entry
    """
    try:
        get_response(
            url=f"https://www.ebi.ac.uk/emdb/api/entry/{emdb_id}",
            headers={'accept': 'application/json','X-CSRFToken': 'erok9V3otfDBilWcRiAZgcCXjhYI91iVvDOUPZNZ3RuTYHGLlDyKPXhUQMEqoDwR','Cache-Control': 'no-cache','Pragma': 'no-cache'},
            params={},
            save_path=save_path,
        )
    except Exception as e:
        logger.warning(f"Error saving EMDB entry {emdb_id}: {e}")
        
def load_emdb_entry(empiar_id: str, emdb_id: str):
    """
    Load the EMDB entry
    """
    if not EMDB_ENTRY_FILE(empiar_id, emdb_id).exists():
        logger.warning(f"{PROJECT_NAME} {EMDB_ENTRY_FILE(empiar_id, emdb_id)} does not exist, save EMDB entry first")
        save_emdb_entry(emdb_id, EMDB_ENTRY_FILE(empiar_id, emdb_id))
    with open(EMDB_ENTRY_FILE(empiar_id, emdb_id), "r") as f:
        emdb_entry = json.load(f)
    logger.debug(f"{PROJECT_NAME} load EMDB entry for {emdb_id} from {EMDB_ENTRY_FILE(empiar_id, emdb_id)}")
    return emdb_entry

def load_emdb_entry_with_path(emdb_path: str):
    """
    Load the EMDB entry with path
    """
    with open(emdb_path, "r") as f:
        emdb_entry = json.load(f)
    logger.debug(f"{PROJECT_NAME} load EMDB entry from {emdb_path}")
    return emdb_entry
    
def get_empiar_emdb_pair_list(empiar_ids: list[str] = None) -> list[dict]:
    """
    Load the EMPIAR-EMDB pairs
    """
    if empiar_ids is None:
        empiar_ids = load_empiar_ids()
    elif type(empiar_ids) is not list:
        empiar_ids = [empiar_ids]
    empiar_emdb_pair_list = []
    for empiar_id in empiar_ids:
        if not EMPIAR_ENTRY_FILE(empiar_id).exists():
            continue 
        empiar_entry = load_empiar_entry(empiar_id)
        emdb_cross_references: list[str] = read_list_safely(empiar_entry, "cross_references")
        empiar_emdb_pair_dict = {
            "empiar": {"name": empiar_id, "json_path": EMPIAR_ENTRY_FILE(empiar_id)},
            "emdb": [{"name": emdb_id, "json_path": EMDB_ENTRY_FILE(empiar_id, emdb_id)} for emdb_id in emdb_cross_references]
        }
        empiar_emdb_pair_list.append(empiar_emdb_pair_dict)
    logger.info(f"{PROJECT_NAME} load {len(empiar_emdb_pair_list)} EMPIAR-EMDB pairs")
    return empiar_emdb_pair_list

def parse_empiar_emdb_pair(pair_dict: dict, image_max_num=1000) -> list[DatasetDocument]:
    imagesets_doc_list = []
    empiar_id = pair_dict["empiar"]["name"]
    empiar_number = empiar_id.replace("EMPIAR-", "")
    empiar_path_csv = load_empiar_path_csv(empiar_id)
    empiar_entry = load_empiar_entry(empiar_id)
    emdb_entries = [load_emdb_entry_with_path(emdb["json_path"]) for emdb in pair_dict["emdb"]]
    imagesets_list:list[dict] = read_list_safely(empiar_entry, "imagesets")
    corresponding_emdb_entries = read_list_safely(empiar_entry, "cross_references")
    pdb_entries  = read_list_safely(empiar_entry, "related_pdb_entries")
    corresponding_emdb_num = len(corresponding_emdb_entries)
    corresponding_pdb_num = len(pdb_entries)
    determination_method = DeterminationMethod.unknown.value
    acceleration_voltage = 0
    spherical_aberration = 0
    film_or_detector_model = ""
    microscope = ""
    average_electron_dose = ""
    nominal_defocus_max = 0
    nominal_defocus_min = 0
    average_emdb_resolution = 0
    if len(emdb_entries) > 0:
        emdb_entry = emdb_entries[0]
        sample = read_element_safely(emdb_entry, "sample")
        structure_determination = read_list_safely(read_element_safely(emdb_entry, "structure_determination_list"), "structure_determination")[0]
        microscopy = read_list_safely(read_element_safely(structure_determination, "microscopy_list"), "microscopy")[0]
        image_recording = read_list_safely(read_element_safely(microscopy, "image_recording_list"), "image_recording")[0]
        map = read_element_safely(emdb_entry, "map")
        # determination_method
        determination_method = structure_determination.get("method", DeterminationMethod.unknown.value)
        acceleration_voltage = read_element_safely(read_element_safely(microscopy, "acceleration_voltage"), "valueOf_", 0)
        spherical_aberration = read_element_safely(read_element_safely(microscopy, "nominal_cs"), "valueOf_", 0)
        film_or_detector_model = read_element_safely(read_element_safely(image_recording, "film_or_detector_model"), "valueOf_", "")
        microscope = read_element_safely(microscopy, "microscope", "")
        average_electron_dose = read_element_safely(read_element_safely(image_recording, "average_electron_dose_per_image"), "valueOf_", 0)
        nominal_defocus_max = read_element_safely(read_element_safely(microscopy, "nominal_defocus_max"), "valueOf_", 0)
        nominal_defocus_min = read_element_safely(read_element_safely(microscopy, "nominal_defocus_min"), "valueOf_", 0)
        # resolution
        average_emdb_resolution = 0
        for emdb_c in emdb_entries:
            try:
                structure_determination = read_list_safely(read_element_safely(emdb_c, "structure_determination_list"), "structure_determination")[0]
                resolution = structure_determination["image_processing"][0]["final_reconstruction"]["resolution"]["valueOf_"]
                resolution = round(float(resolution), 2)
            except:
                resolution = 0
            average_emdb_resolution += resolution
        average_emdb_resolution /= len(emdb_entries)
    dataset_name = pair_dict["empiar"]["name"].lower()
    dataset_title = empiar_entry.get("title", "")
    deposition_date = empiar_entry.get("deposition_date", "")
    
    citation_list = read_list_safely(empiar_entry, "principal_investigator", [""])
    organization=[]
    town_or_city=[]
    country=[]
    for citation in citation_list:
        organization.append(read_element_safely(citation, "organization"))
        town_or_city.append(read_element_safely(citation, "town_or_city"))
        country.append(read_element_safely(citation, "country"))
    
    paper_doi = read_element_safely(read_list_safely(empiar_entry, "citation", [""])[0], "doi")
    
    empiar_ftp_directory = "ftp.ebi.ac.uk/empiar/world_availability/{}".format(empiar_number)
    for imageset_idx, imageset_c in enumerate(imagesets_list):
        imageset_name = "{}-imageset-{:02d}".format(dataset_name, imageset_idx)
        imageset_title = imageset_c.get("name", "")
        imageset_details = imageset_c.get("details", "")
        image_width = imageset_c.get("image_width", 0)
        image_height = imageset_c.get("image_height", 0)
        gain_width = 0 # unknown...
        gain_height = 0
        pixel_spacing = read_element_safely(imageset_c, "pixel_width", 0.0)
        image_type = data_format_patch(dataset_name, imageset_c.get("data_format", ImageType.unknown.value))
        image_category = imageset_c.get("category", ImageCategory.unknown.value)
        pixel_type = imageset_c.get("voxel_type", PixelType.Other.value)
        empiar_relative_directory = imageset_c.get("directory", "") 
        # image / gain
        empiar_image_relative_paths = get_image_paths_of_empiar_imageset(image_type, dataset_name, empiar_relative_directory, empiar_path_csv["relative_path"].tolist())
        empiar_gain_relative_paths = get_gain_paths_of_empiar_imageset(empiar_path_csv["relative_path"].tolist())
        image_num = len(empiar_image_relative_paths)
        gain_num = len(empiar_gain_relative_paths)
        
        image_st = image_num//2-image_max_num//2
        image_ed = image_st+image_max_num
        empiar_image_relative_paths = empiar_image_relative_paths[image_st:image_ed]
        empiar_gain_relative_paths = empiar_gain_relative_paths[:image_max_num]
        image_suffix = ""
        gain_suffix = ""
        if image_num > 0:
            image_suffix = os.path.splitext(empiar_image_relative_paths[0])[1]
        if gain_num > 0:
            gain_suffix = os.path.splitext(empiar_gain_relative_paths[0])[1]
        
        dataset_doc = DatasetDocument(
            dataset_name=str_default(dataset_name),
            imageset_name=str_default(imageset_name),
            imageset_title=str_default(imageset_title),
            imageset_details=str_default(imageset_details),
            image_category=str_default(image_category),
            dataset_title=str_default(dataset_title),
            organization=organization,
            town_or_city=town_or_city,
            country=country,
            paper_doi=str_default(paper_doi),
            deposition_date=str_default(deposition_date),
            
            image_type=str_default(image_type),
            pixel_type=str_default(pixel_type),
            image_num=int_default(image_num),
            image_suffix=str_default(image_suffix),
            gain_num=int_default(gain_num),
            gain_suffix=str_default(gain_suffix),
            
            corresponding_emdb_num=int_default(corresponding_emdb_num),
            corresponding_pdb_num=int_default(corresponding_pdb_num),
            average_emdb_resolution=float_default(average_emdb_resolution),
            determination_method=str_default(determination_method),
            
            image_width=int_default(image_width),
            image_height=int_default(image_height),
            gain_width=int_default(gain_width),
            gain_height=int_default(gain_height),
            pixel_spacing=float_default(pixel_spacing),
            acceleration_voltage=float_default(acceleration_voltage),
            spherical_aberration=float_default(spherical_aberration),
            film_detector_model=str_default(film_or_detector_model),
            microscope=str_default(microscope),
            average_electron_dose=float_default(average_electron_dose),
            nominal_defocus_max=float_default(nominal_defocus_max),
            nominal_defocus_min=float_default(nominal_defocus_min),
            
            corresponding_emdb_entries=corresponding_emdb_entries,
            corresponding_pdb_entries=pdb_entries,
            
            empiar_ftp_directory=str_default(empiar_ftp_directory),           # ftp/.../10007/
            empiar_relative_directory=str_default(empiar_relative_directory), # data/
            empiar_image_relative_paths=empiar_image_relative_paths,
            empiar_gain_relative_paths=empiar_gain_relative_paths,
        )
        
        imagesets_doc_list.append(dataset_doc)
        
    return imagesets_doc_list
        
def save_empiar_emdb_entries(empiar_ids: str | list[str] =None):
    """
    Save the EMPIAR-EMDB entries
    """
    if empiar_ids is None:
        empiar_ids = load_empiar_ids()
    elif type(empiar_ids) is not list:
        empiar_ids = [empiar_ids]
    empiar_ids = empiar_id_patch(empiar_ids)
    
    EMDB_ENTRY_DIR.mkdir(parents=True, exist_ok=True)
    for empiar_id in tqdm(empiar_ids, "Crawling empiar entries"):
        if not EMPIAR_ENTRY_FILE(empiar_id).exists():
            save_empiar_entry(empiar_id, EMPIAR_ENTRY_FILE(empiar_id))
    logger.info(f"{PROJECT_NAME} save {len(empiar_ids)} EMPIAR entries to {EMPIAR_ENTRY_DIR}")
        
    total_emdb_num = 0
    for empiar_id in tqdm(empiar_ids, "Crawling emdb entries"):
        if not EMPIAR_ENTRY_FILE(empiar_id).exists():
            logger.warning(f"{PROJECT_NAME} {EMPIAR_ENTRY_FILE(empiar_id)} does not exist, skip saving EMDB entries")
            continue 
        emdb_cross_references: list[str] = read_list_safely(load_empiar_entry(empiar_id), "cross_references")
        for emdb_id in emdb_cross_references:
            if not EMDB_ENTRY_FILE(empiar_id, emdb_id).exists():
                save_emdb_entry(emdb_id, EMDB_ENTRY_FILE(empiar_id, emdb_id))
        total_emdb_num += len(emdb_cross_references)
    logger.info(f"{PROJECT_NAME} save {total_emdb_num} EMDB entries to {EMDB_ENTRY_DIR}")
    