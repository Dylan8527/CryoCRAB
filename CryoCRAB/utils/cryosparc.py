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
            base_port = int(base_port),
            email = email,
            password = password,
            timeout = timeout,
        )
    except Exception as e:
        cryosparc_client = None
        logger.error("Failed to create CryoSPARC client: %s", e)
    return cryosparc_client

def get_cryosparc_project(project_id: str=None):
    """
    Get the CryoSPARC project
    """
    if project_id is None:
        project_id = os.getenv("CRYOSPARC_PROJECT_ID", None)
        if project_id is None:
            raise ValueError("Please set project_id in the environment variable CRYOSPARC_PROJECT_ID.")
    return get_cryosparc_client().find_project(project_id)

def get_cryosparc_workspace(workspace_id: str, project_id: str=None):
    """
    Get the CryoSPARC job
    """
    project = get_cryosparc_project(project_id)
    return project.find_workspace(workspace_id)

def get_cryosparc_job(job_id: str, project_id: str=None):
    """
    Get the CryoSPARC job
    """
    project = get_cryosparc_project(project_id)
    return project.find_job(job_id)

def get_cryosparc_job_link(pid: str, wid: str, jid: str):
    host = os.getenv("CRYOSPARC_MASTER_HOSTNAME", "localhost")
    base_port = int(os.getenv("CRYOSPARC_BASE_PORT", 39000))
    link = f"http://{host}:{base_port}/browse/{pid}-{wid}-J*#job({pid}-{jid})"
    markdown_link = f"[Click here to view the job]({link})"
    return markdown_link
    
    
    