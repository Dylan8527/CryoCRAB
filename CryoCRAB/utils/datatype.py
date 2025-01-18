import enum
from ftplib import FTP
from pydantic import BaseModel
from pathlib import Path 
import os
import logging 

logger = logging.getLogger()

from . import EMPIAR, get_project_root
from .helper_func import timer

class ImageCategory(str, enum.Enum):
    """
    Image category, for micrographs or picked particles
    """
    
    focal_pairs_unprocessed = "micrographs - focal pairs - unprocessed"
    focal_pairs_processed = "micrographs - focal pairs - processed"
    focal_pairs_contrast_inverted = "micrographs - focal pairs - contrast inverted"
    multiframe_micrographs = "micrographs - multiframe"
    singleframe_micrographs = "micrographs - single frame"
    singleframe_micrographs_nondw = "micrographs - single frame - non-dose-weighted"
    singleframe_micrographs_nondw2 = "micrographs - single frame - no-doseweighted"
    multiframe_particles_unprocessed = "picked particles - multiframe - unprocessed"
    multiframe_particles_processed = "picked particles - multiframe - processed"
    singleframe_particles_unprocessed = "picked particles - single frame - unprocessed"
    singleframe_particles_processed = "picked particles - single frame - processed"
    tilt_series = "tilt series"
    class_averages = "class averages"
    reconstructed_volumes = "reconstructed volumes"
    diffraction_images = "diffraction images"
    stitched_maps="stitched maps"
    subtomograms = "subtomograms"
    Other = "Other"
    unknown = "unknown"

class ImageType(str, enum.Enum):
    """
    Image type, for EER, MRC, MRCS, TIFF
    """
    EER = "EER"
    MRC = "MRC"
    MRCS = "MRCS"
    TIFF = "TIFF"
    SPIDER = "SPIDER"
    IMAGIC = "IMAGIC"
    DM4 = "DM4"
    HDF5 = "BIG DATA VIEWER HDF5"
    SMV = "SMV"
    JPEG = "JPEG"
    EM = "EM"
    PNG = "PNG"
    TPX3 = "TPX3"
    Other = "Other"
    DM3 = "DM3"
    unknown = "unknown"
    
class PixelType(str, enum.Enum):
    """
    Pixel type, for 32-bit float, 1-bit, 4-bit, 8-bit, 16-bit, 32-bit integer,
    unsigned 8-bit integer, unsigned 16-bit integer, unsigned 32-bit integer
    """
    BIT_1 = "BIT"
    INT_4 = "4 BIT INTEGER"
    INT_8 = "SIGNED BYTE"
    INT_16 = "SIGNED 16 BIT INTEGER"
    INT_32 = "SIGNED 32 BIT INTEGER"
    UINT_8 = "UNSIGNED BYTE"
    UINT_16 = "UNSIGNED 16 BIT INTEGER"
    UINT_32 = "UNSIGNED 32 BIT INTEGER"
    FLOAT_32 = "32 BIT FLOAT"
    FLOAT_16 = "16 BIT FLOAT"
    Other = "Other"
    
class DeterminationMethod(str, enum.Enum):
    """
    Determination method, for single particle
    """
    spa = "singleParticle"
    ec = "electronCrystallography"
    sa = "subtomogramAveraging"
    helical = "helical"
    tomography = "tomography"
    unknown = "unknown"

class CategoryStatus(int, enum.Enum):
    """
    Category status, for singleframe or multiframe
    """
    SINGLEFRAME = 0
    MULTIFRAME = 1
    
class GainFlip(int, enum.Enum):
    """
    Gain flip status, for gain flip check
    """
    NO_FLIP = 0
    FLIP_X = 1 # left-right flip
    FLIP_Y = 2 # up-down flip
    FLIP_XY = 3 # left-right and up-down flip
    
class DatasetDocument(BaseModel):
    id: str=""
    dataset_name: str=""
    imageset_name: str=""
    imageset_title: str=""
    imageset_details: str=""
    image_category: ImageCategory=ImageCategory.unknown
    dataset_title: str=""
    organization: list[str]=""
    town_or_city: list[str]=""
    country: list[str]=""
    paper_doi: str=""
    deposition_date: str=""

    image_type: ImageType=ImageType.unknown
    pixel_type: PixelType=PixelType.Other
    image_num: int=0
    image_suffix: str=""
    gain_num: int=0
    gain_suffix: str=""
    
    corresponding_emdb_num: int=0
    corresponding_pdb_num: int=0
    average_emdb_resolution: float=-1 
    determination_method: DeterminationMethod=DeterminationMethod.unknown
    
    image_width: int=0
    image_height:int=0
    gain_width: int=0
    gain_height: int=0
    pixel_spacing: float=0
    acceleration_voltage: float=0 
    spherical_aberration: float=0
    film_detector_model: str=""
    microscope: str=""
    average_electron_dose: float=0
    nominal_defocus_max: float=0
    nominal_defocus_min: float=0
    
    corresponding_emdb_entries: list[str]=[""]
    corresponding_pdb_entries: list[str]=[""]
    
    empiar_ftp_directory: str=""
    empiar_relative_directory: str=""
    empiar_image_relative_paths: list[str]=[""]
    empiar_gain_relative_paths: list[str]=[""]
    
    gain_rotate: int=0
    gain_flip: GainFlip=GainFlip.NO_FLIP

class CryoCRAB_Download_DataType(str, enum.Enum):
    micrograph: str="micrograph"
    movie: str="movie"
    gain: str="gain"
    
class CryoCRAB_Image_SuffixType(str, enum.Enum):
    eer: str=".eer"
    tif: str=".tif"
    mrcs: str=".mrcs"
    mrc: str=".mrc"
    tiff: str=".tiff"
    MRC: str=".MRC"

class CryoCRAB_Gain_SuffixType(str, enum.Enum):
    mrc: str=".mrc"
    dm4: str=".dm4"
    MRC: str=".MRC"
    gain: str=".gain"

class DownloadMode(str, enum.Enum):
    local: str="local"
    cluster: str="cluster"

class CryoCRAB_DataManager(object):
    
    def __init__(self, 
        storage_mode: DownloadMode=DownloadMode.local
    ):
        
        if storage_mode == DownloadMode.local:
            project_dir = get_project_root()
            self.storage_cryocrab_datadir = project_dir
        else:
            raise NotImplementedError("Cluster mode is not implemented yet.")
            # storage cluster info
            self.storage_host: str="10.15.56.104"
            self.storage_port: int=28111
            self.storage_username: str="cellverse"
            self.storage_password: str="Cellverse123!"
            self.storage_cryocrab_datadir: str="/mnt/cryocrab_storage"
        
        # empiar ftp info
        self.empiar_ftp_host: str=EMPIAR().EMPIAR_IP
        self.empiar_ftp_port: int=EMPIAR().PORT
        self.empiar_ftp_directory: str=EMPIAR().DIRECTORY
        
    def ftppath_to_localpath(self, imageset_name: str, ftp_path: str, download_datatype: CryoCRAB_Download_DataType):
        
        filename = ftp_path.split('/')[-1]
        local_path = Path(self.storage_cryocrab_datadir) / "Data" / imageset_name / download_datatype.value / "raw" / filename
        return local_path 
    
    def new_ftp(self):
        """
        Initialize and return an FTP connection to the EMPIAR server.
        """
        ftp = FTP(timeout=200)
        ftp.connect(self.empiar_ftp_host, self.empiar_ftp_port)
        ftp.login()  
        ftp.cwd(EMPIAR().DIRECTORY)
        ftp.set_debuglevel(0)
        return ftp
    
    def get_ftp_file_size(self, ftp, ftp_path: str):
        """
        Get the file size of the file in the ftp server
        """
        if type(ftp_path) is not str: ftp_path = str(ftp_path)
        try:
            size = ftp.size(ftp_path)
        except Exception as e:
            size =  -1
        return size

    def get_local_file_size(self, local_path: str):
        """
        Get the file size of the local file
        """
        try:
            size = os.path.getsize(local_path)
        except Exception as e:
            size = -1
        return size
    
    def download_via_ftp(self, imageset_name: str, ftp_path: str, download_datatype: CryoCRAB_Download_DataType):
        
        ftp = self.new_ftp()
        ftp_file_size = self.get_ftp_file_size(ftp, ftp_path)
        
        local_path = self.ftppath_to_localpath(imageset_name, ftp_path, download_datatype)
        local_path.parent.mkdir(parents=True, exist_ok=True)        
        local_file_size = self.get_local_file_size(local_path)
        
        if local_file_size == -1:
            logger.info("Start FTP Download %s -> %s", ftp_path, local_path)
            @timer
            def main(ftp_path, local_path):
                with open(local_path, "wb") as f:
                    ftp.retrbinary("RETR " + ftp_path, f.write)
                local_file_size = self.get_local_file_size(local_path)
                return local_file_size 
            local_file_size, time_st, time_ed = main(ftp_path, local_path)
            logger.info("FTP download costs: {:.2f} s.".format(time_ed - time_st))
            
        ftp.close()
        
        if ftp_file_size == local_file_size:
            return ftp_file_size, local_file_size
        else:
            local_path.unlink()
        
        return ftp_file_size, local_file_size
        
    
class SingleImageTestStatus(str, enum.Enum):
    """
    Single image test status, for cryosparc single image test
    """
    testing: str="testing"
    downloading: str="downloading"
    # unpacking: str="unpacking"
    # compressing: str="compressing"
    passed: str="passed"
    failed: str="failed"
    
class SingleImageTestRecording(str, enum.Enum):
    pass 
