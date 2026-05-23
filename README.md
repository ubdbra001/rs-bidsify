# RS-BIDSify

RS-BIDSify is a package that leverages MNE and MNE-BIDS to easily and flexibly convert legacy resting-state EEG datasets to BIDS-compliant datasets.

It has been designed and built to be used as part of the #EEGManyLabs Resting-State project (ElectroPool/RosettaState).

## Table of Contents
* [Installation](#installation)
* [Data Preparation](#data-preparation)
    * [Input directory structure](#input-directory-structure)
    * [JSON Metadata](#json-metadata)
    * [Participant Information](#participant-information)
* [Usage](#usage)
* [Advanced Usage](#advanced-usage)
    * [Configuration File](#configuration-file)
* [Appendix](#appendix)
    * [Complete Metadata](#complete-metadata)

## Installation

RS-BIDSify works with Python>=3.12 and can be installed directly from GitHub:

``` shell
pip install rs-bidsify@git+https://github.com/ubdbra001/rs-bidsify.git
```

It is recommended that you install the package into a virtual environment.

## Data preparation

### Input directory structure

The input directory requires a specific structure to work. Each participant should have a single directory for their data, and there should only be a single recording in each directory.

``` shell
dataset/
├── data_metadata.json
├── participant_data.ods
├── sub-001/
│   └── sub-001.edf
├── sub-002/
│   └── sub-002.edf
├── sub-003/
│   └── sub-003.edf
├── ...
└── sub-xxx/
    └── sub-xxx.edf
```

Each subject directory can, optionally, contain task subdirectories, but again there should be a single recording per directory. e.g.:

```shell
dataset/
├── sub-001/
│   ├── rest/
│   │   └── sub-001-rest.edf
│   └── video/
│       └── sub-001-video.edf
...
```

The JSON file containg the dataset metadata and the spreadsheet (ods) containing the participant information should be in the root of the raw data directory. These do not have to be named as in the example above, but should have the correct file extensions, and there should only be a single file for each.

### JSON metadata

This file specifies the metadata describing the dataset. It is split into 4 different sections.

See the [appendix below](#complete-metadata) for an example of a complete metatdata file

#### 1. Conditions

This is a array/list outlining the different conditions present in the data set.
It can be omitted or left empty if these is a single condition, but need to be present when task directories are present in the dataset file structure, and the values should correspond exactly.

```json
"conditions": ["rest", "video"]
```
#### 2. Metadata
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
#### 3. Acquisition Specification

This structure contains information about the specifics of each recording.
It can be broken down into several sections:

##### Basic information

This is the basic information about the recording, e.g. sampling frequency, power line frequency, input file format, etc.

``` json
"software": "Brain Vision Recorder",
"acquisition_freq": 1000,
"file_format": ".set",
"amplifier_model": "Brain Products",
"power_line_freq": 50,
```

##### EEG channel information

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

##### Auxillary channel information

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
##### Filter Information

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


##### Extra information
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

#### 4. Resting state information
This section conatins information about the resting state tasks undertaken during the recording.  
In includes information about the instructions issued to the participants, the duration of the eyes-open and eyes-closed conditions, the stimuli used during these conditions, any other conditions recorded, and the detials of the event markers captured during the recording. 

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
    "other_conditions": [
        {
            "condition_name": "video watching",
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

### Participant information

This file contians information about the participants. This information should be stored in tabular form in a single worksheet with the columns: `participant_id`, `age`, `sex`, and `handedness`.
It should also contain a codebook: a seperate sheet with a table describing what each of these columns represent.  

This file can also optionally contain a sheet with phenotype data collected from the participants. This data should also be stored in tabular form with the required column `participant_id`, whose values should match the values in the participant information worksheet. As many other columns may be added to the sheet.  
If a phenotype sheet is included then a phenotype codebook sheet is required. As with the participant dataset codebook, this should describe each of the columns present in the phenotype datasheet.

By default a `.ods` spreadsheet is expected, but this can be customised using a config file ([see below](#spreadsheet-extension)) 

[↑ Back to Top](#table-of-contents)

## Usage
Once installed you can use a command line interface to run RS-BIDSify:

``` shellsee below
rs-bidsify path/to/raw/data path/for/bids/data
```

The first argument (`path/to/raw/data`) is the path to the input directory containing the raw data and metadata files  
The second argument (`path/for/bids/data`) is the path to the output directory where you would like the BIDS-compliant data to be saved.

## Advanced usage

### Configuration file

It is possible to specify a custom configuration for running RS-BIDSify:

``` shell
rs-bidsify path/to/raw/data path/for/bids/data --config path/to/config.yml
```

This configuration file should be a yaml file, and can be used to set the following options:

#### Demographic mappings
This describes mappings between text and numeric values for how sex and handedness may be described in the participants spreadsheet.

``` yaml
demographic_mappings:
  sex:
    u: 0
    unknown: 0
    m: 1
    male: 1
    f: 2
    female: 2
  hand:
    r: 1
    right: 1
    l: 2
    left: 2
    a: 3
    ambidextrous: 3
```

#### Sheet info
This describes the location and index column for each sheet in the participant information spreadsheet:

``` yaml
sheet_info:
  participant:
    dataset:
      sheet_name: 6
      index_col: "participant_id"
    codebook:
      sheet_name: 7
      index_col: "Variable"
  phenotype:
    dataset:
      sheet_name: 8
      index_col: "participant_id"
    codebook:
      sheet_name: 9
      index_col: "Variable"
```

#### Spreadsheet extension
The file extension to search for when looking up the participant spreadsheet:

``` yaml
spreadsheet_ext: "ods"
```

#### Metadata extension
The file extension to search for when looking up the metadta file:
``` yaml
metadata_ext: "json"
```

#### Output EEG format
The file format to save the EEG data to in the BIDS-compliant output:
```yaml
output_EEG_format: "edf"
```

#### Include extra information
A flag indicating whether the extra information section of the metadata should be written to the EEG recording sidecar files.
```yaml
include_extras: true
```
[↑ Back to Top](#table-of-contents)

## Appendix

### Complete Metadata

Below is an example of a complete JSON metadata file:

```json
{
    "conditions": ["rest", "video"],
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
    },
    "acquisition_spec": {
        "software": "Brain Vision Recorder",
        "amplifier_model": "Brain Products",
        "power_line_freq": 50,
        "acquisition_freq": 1000,
        "file_format": ".set",
        "eeg_channels": {
            "number" : 63,
            "montage": {
                "mne_name": "standard_1005" 
            },
            "ground": "FPz",
            "reference": "VARIES"
        },
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
        },
        "filters": [
            {
                "name": "Low-pass filter",
                "type": "Software",
                "info": {
                    "cut-off frequency (Hz)": 260
                }
            }
        ],
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
    },
    "resting_state": {
        "instructions": "A prerecorded voice gave commands to open and close the eyes every minute. The stimuli were presented in PsychoPy.",
        "eyes_closed": {
            "duration_secs": 240
        },
        "eyes_open": {
            "duration_secs": 240,
            "stimulus_description": "white fixation cross on a grey background"
        },
        "other_conditions": [
            {
                "condition_name": "video watching",
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
    },
}
```

[↑ Back to Top](#table-of-contents)
