import os
#TODO: more elegant solution
os.environ["CRYOCRAB_PROJECT_SAVE_DIR"] = "/home/vrlab/code/Cryo/CryoCRAB/"
# MongoDB Information
os.environ["CRYOCRAB_MONGODB_HOST"] = "10.15.89.239"
os.environ["CRYOCRAB_MONGODB_PORT"] = "27017"
os.environ["CRYOCRAB_MONGODB_DBNAME"] = "cryocrab_0119"

# CryoSPARC Information
os.environ["CRYOSPARC_LICENSE_ID"] = "8d73981e-880a-11eb-8573-7b1bc5716ba6"
os.environ["CRYOSPARC_MASTER_HOSTNAME"] = "10.15.56.173"
os.environ["CRYOSPARC_BASE_PORT"] = "45000"
os.environ["CRYOSPARC_EMAIL"] = "shenyj2022@shanghaitech.edu.cn"
os.environ["CRYOSPARC_PASSWORD"] = "vrlab123"
os.environ["CRYOSPARC_PROJECT_ID"] = "P365"
from .pipeline import *