DEMOGRAPHIC_MAPPINGS = {
    "sex": {
        "u": 0, "unknown": 0, 
        "m": 1, "male": 1,
        "f": 2, "female": 2
    },
    "hand": {
        "r": 1, "right": 1,
        "l": 2, "left": 2,
        "a": 3, "ambidextrous": 3
    }
}

PARTICIPANT_INFO = {
    "dataset": {
        "sheet_name": 6,
        "index_col": "participant_id"
    },
    "codebook": {
        "sheet_name": 7,
        "index_col": "Variable"
    },
}

PHENOTYPE_INFO = {
    "dataset": {
        "sheet_name": 8,
        "index_col": "participant_id"
    },
    "codebook": {
        "sheet_name": 9,
        "index_col": "Variable"
    },
}