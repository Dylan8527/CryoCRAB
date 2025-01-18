
def data_format_patch(dataset_name, data_format):
    """
    Patch the data format for some EMPIAR datasets
    """
    patch_dict = {
        "empiar-10026-imageset-00": "MRCS",
        "empiar-11813-imageset-00": "MRC",
        "empiar-11836-imageset-00": "MRC",
        "empiar-10023-imageset-00": "MRCS",
        "empiar-11980-imageset-00": "TIFF",
        "empiar-11890-imageset-00": "TIFF",
        "empiar-10408-imageset-00": "TIFF",
        "empiar-10247-imageset-00": "MRC",
        "empiar-10603-imageset-00": "MRC",
        "empiar-11925-imageset-00": "MRC",
        "empiar-11925-imageset-01": "MRC",
        "empiar-10259-imageset-00": "MRC",
        "empiar-10496-imageset-00": "MRC",

        "empiar-10026-00": "MRCS",
        "empiar-11813-00": "MRC",
        "empiar-11836-00": "MRC",
        "empiar-10023-00": "MRCS",
        "empiar-11980-00": "TIFF",
        "empiar-11890-00": "TIFF",
        "empiar-10408-00": "TIFF",
        "empiar-10247-00": "MRC",
        "empiar-10603-00": "MRC",
        "empiar-11925-00": "MRC",
        "empiar-11925-01": "MRC",
        "empiar-10259-00": "MRC",
        "empiar-10496-00": "MRC",
        
        
        "empiar-10026": "MRCS",
        "empiar-11813": "MRC",
        "empiar-11836": "MRC",
        "empiar-10023": "MRCS",
        "empiar-11980": "TIFF",
        "empiar-11890": "TIFF",
        "empiar-10408": "TIFF",
        "empiar-10247": "MRC",
        "empiar-10603": "MRC",
        "empiar-11925": "MRC",
        "empiar-11925": "MRC",
        "empiar-10259": "MRC",
        "empiar-10496": "MRC",
        
    }
    return patch_dict.get(dataset_name, data_format)

def possible_ext_patch(dataset_name, possible_ext):
    """
    Patch the possible extensions for some EMPIAR datasets
    """
    patch_dict = {
        "empiar-11190-imageset-00": [".tar"],
        "empiar-11190-00": [".tar"],
        "empiar-11190": [".tar"],
    }
    return patch_dict.get(dataset_name, possible_ext)

def empiar_id_patch(empiar_ids):
    """
    Patch the EMPIAR IDs
    """
    ban_ids = ["EMPIAR-10036", 
               "EMPIAR-10276", 
               "EMPIAR-11174", 
               "EMPIAR-11581", 
               "EMPIAR-11997",
               "EMPIAR-12099",
               "EMPIAR-11366",
               "EMPIAR-11607",
               "EMPIAR-11723",
               "EMPIAR-11802",
               "EMPIAR-11942",
               "EMPIAR-12090",
               "EMPIAR-12096",
               "EMPIAR-12232",
            ]
    return [empiar_id for empiar_id in empiar_ids if empiar_id not in ban_ids]

def image_paths_ban_words_patch(dataset_name, ban_words):
    """
    Patch the ban words for some EMPIAR datasets
    """
    if dataset_name == "empiar-11376-imageset-00": 
        ban_words = ["dark", "norm"]
    elif dataset_name == "empiar-11376-00": 
        ban_words = ["dark", "norm"]
    elif dataset_name == "empiar-11376": 
        ban_words = ["dark", "norm"]
    return ban_words
