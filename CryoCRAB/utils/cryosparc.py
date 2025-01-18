import os
import logging
 
from cryosparc.tools import CryoSPARC

logger = logging.getLogger()

def get_cryosparc_client(
    license = os.getenv("CRYOSPARC_LICENSE_ID", ""),
    host = os.getenv("CRYOSPARC_MASTER_HOSTNAME", "localhost"),
    base_port = int(os.getenv("CRYOSPARC_BASE_PORT", 39000)),
    email = os.getenv("CRYOSPARC_EMAIL", ""),
    password = os.getenv("CRYOSPARC_PASSWORD", ""),
    timeout = 300,
):
    """
    Get the CryoSPARC client
    """
    try:
        cryosparc_client = CryoSPARC(
            license = license,
            host = host,
            base_port = base_port,
            email = email,
            password = password,
            timeout = timeout,
        )
    except Exception as e:
        cryosparc_client = None
        logger.error("Failed to create CryoSPARC client: %s", e)
    return cryosparc_client

def get_cryosparc_project