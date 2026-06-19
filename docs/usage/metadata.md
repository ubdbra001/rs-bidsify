# Dataset metadata

`RS-BIDSify` requires two metadata files as inputs:

1. **Recording metadata**: A JSON file specifying key metadata about the EEG recording environment.
2. **Participant metadata**: A spreadsheet containing participant-level metadata, and, optionally, phenotype metadata.

These form the basis of the information that will be placed in the BIDS metadata files.

## Recording metadata

This file can be broken down into four key sections, each describing a part of the recording environment.  
Not all sesctions are required, and not all items in a section are required.

### 1. Tasks

This is a array/list outlining the different tasks present in the data set.
It can be omitted if there is only a single task (in which case the task name will default to "rest"), but it is required when task directories are present in the dataset file structure, and the values should correspond exactly.

```json
"tasks": ["rest", "video"]
```

### 2. Metadata

This structure contains infomation about dataset-level metadata (i.e. values that would not differ between participants)

``` json
"metadata": {
    "population": "Healthy Adults",
    "dataset_name": "Test dataset",
    "authors": [
        "Pavlov, Yuri"
    ],
    "funding": "n/a",
    "ethics_approval": "Approved",
    "references_links": "n/a",
    "license": "n/a",
    "institution_name": "n/a",
    "institution_dept": "n/a"
}
```

### 3. Acquisition Specification

This structure contains information about the specifics of each recording.
It can be broken down into several sections:

#### Basic information

This is the basic information about the recording, e.g. sampling frequency, power line frequency, input file format, etc.

``` json
"software": "Brain Vision Recorder",
"acquisition_freq": 1000,
"file_format": ".set",
"amplifier_model": "Brain Products",
"power_line_freq": 50,
```

#### EEG channel information

This structure contains information about the EEG channels present in the recording.

``` json
"eeg_channels": {
    "number" : 63,
    "montage": {
        "mne_name": "standard_1005" 
    },
    "ground": "FPz",
    "reference": "Cz"
}
```

#### Auxillary channel information

This structure outlines the details of all the non-EEG channels present in the recordings.  
Each channel should be named as they are in the recording, and should include information about the type of channel in both MNE and BIDS, as well as the location of the channel, measurement units, and description.  

``` json
"aux_channels": {
    "ECG": {
        "mne_type": "ecg",
        "bids_type": "ECG",
        "location": {
            "active": "right wrist",
            "reference": "left wrist",
            "ground": "left inner forearm 3 cm distal from the elbow"
        }
    },
    "PPG": {
        "mne_type": "misc",
        "bids_type": "PPG",
        "description": "photoplethysmography",
        "location": "placed on the left index finger",
        "units": "µV"
    },
    "audio": {
        "mne_type": "misc",
        "bids_type": "AUDIO",
        "description": "Audio channel",
        "location": "n/a"
    }
}
```

#### Filter Information

This section consists of a list of all the hardware and software filters soecified for the recording.  
Each filter should consist of an object with a name, a type (Hardware or Software), and info about the filter.  
Info should be represented in an object with key value pairs, and these are translated directly to the BIDS recording sidecar file.

``` json
"filters": [
    {
        "name": "Low-pass filter",
        "type": "Software",
        "info": {
            "cut-off frequency (Hz)": 260
        }
    }
],

```

#### Extra information

This structure specifies extra metadata that may be recorded but does not have a formal place in BIDS, and so may optioanlly be included in the final BIDS-compliant dataset.
This section is entirely optional, as are each of the fields contained within.

``` json
"extras": {
    "acceptable_impedance": {"value": 25, "units": "kOhm"},
    "electrode_type": "active",
    "conductive_medium": "gel",
    "faraday_cage": false,
    "sound_proof": false,
    "lighting_conditions": {
        "description": "380 lux ambient lighting",
        "measurement": "measured with a luxmeter around the head of the participant"
    }
}
```

### 4. Resting state information

This section conatins information about the resting state tasks undertaken during the recording.  
In includes information about the instructions issued to the participants, the duration of the eyes-open and eyes-closed tasks, the stimuli used during these tasks, any other tasks recorded, and the detials of the event markers captured during the recording.  

``` json
"resting_state": {
    "instructions": "A prerecorded voice gave commands to open and close the eyes every minute. The stimuli were presented in PsychoPy.",
    "eyes_closed": {
        "duration_secs": 240
    },
    "eyes_open": {
        "duration_secs": 240,
        "stimulus_description": "white fixation cross on a grey background"
    },
    "other_task": [
        {
            "task_name": "video watching",
            "duration_secs": 231,
            "stimulus_description": "a short animated movie 'The man who was afraid of falling' (https://osf.io/x9jpz)"
        }
    ],
    "events": {
        "S 20": "Eyes open",
        "S 21": "Eyes closed",
        "S 22": "Movie start",
        "S 23": "Movie end",
        "S254": "Start of Resting State Recording",
        "S252": "End of Resting State Recording"
    }
}
```

## Participant metadata