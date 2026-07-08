---
title: "Dataset metadata"
toc_depth: 3
---

`RS-BIDSify` requires two metadata files as inputs:

1. **Recording metadata**: A file specifying key metadata about the EEG recording environment.
2. **Participant metadata**: A spreadsheet containing participant-level metadata, and, optionally, phenotype metadata.

These form the basis of the information that will be placed in the BIDS metadata files.

## Recording metadata

This file can be in either [TOML][toml_spec], [YAML][yaml_spec] or [JSON][json_spec] format, and can be broken down into four key sections, each describing a part of the recording environment.  
Not all sections are required, and not all items in a section are required.

1. [Tasks](#tasks)
2. [Acquisition metadata](#acquisition-metadata)
3. [Acquisition specification](#acquisition-specification)
4. [Resting-state information](#resting-state-information)

### Tasks

This is a array/list outlining the different tasks present in the data set.
It can be omitted if there is only a single task (in which case the task name will default to "rest"), but it is required when task directories are present in the dataset file structure, and the values should correspond exactly.

=== "TOML"
    ```toml
    tasks: ["rest", "video"]
    ```

=== "YAML"
    ```yaml
    tasks:
      - rest
      - video
    ```

=== "JSON"
    ```json
    "tasks": ["rest", "video"]
    ```

| Field Name | Type           | Required | Description                         |
| ---------- | -------------- | -------- | ----------------------------------- |
| tasks      | list( string ) | No       | A list of task names in the Dataset |

### Acquisition metadata

This structure contains information about dataset-level metadata (i.e. values that would not differ between participants).  
The section itself is required as some fields are required.

=== "TOML"
    ```toml
    [metadata]
    population: "Healthy Adults"
    dataset_name: "Test dataset"
    authors: ["Pavlov, Yuri"]
    funding: "n/a"
    ethics_approval: "Approved"
    references_links: "n/a"
    license: "n/a"
    institution_name: "n/a"
    institution_dept: "n/a"
    ```

=== "YAML"
    ```yaml
    metadata:
      population: "Healthy Adults"
      dataset_name: "Test dataset"
      authors:
        - "Pavlov, Yuri"
      funding: "n/a"
      ethics_approval: "Approved"
      references_links: "n/a"
      license: "n/a"
      institution_name: "n/a"
      institution_dept: "n/a"
    ```

=== "JSON"
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

| Field Name       | Type                             | Required | Default | Description                                                                                                      |
| ---------------- | -------------------------------- | -------- | ------- | ---------------------------------------------------------------------------------------------------------------- |
| population       | string                           | Yes      | -       | A short description of the population in the recording                                                           |
| dataset_name     | string                           | Yes      | -       | Name of the dataset.                                                                                             |
| authors          | list( string )                   | Yes      | -       | List of individuals who contributed to the creation/curation of the dataset.                                     |
| funding          | string or list( string )         | No       | `"n/a"` | A string, or list of strings, detailing the funding sources for the dataset.                                     |
| ethics_approval  | `"Approved"` or `"Not Required"` | Yes      | -       | A string describing ethical approval status for the dataset. <br>Must be either `"Approved"` or `"Not Required"` |
| references_links | string or list( string )         | No       | `"n/a"` | List of references to publications that contain information on the dataset.                                      |
| license          | string                           | Yes      | -       | The license for the dataset.                                                                                     |
| institution_name | string                           | Yes      | -       | The name of the institution in charge of the equipment that produced the measurements.                           |
| institution_dept | string                           | Yes      | -       | The department in the institution in charge of the equipment that produced the measurements.                     |

### Acquisition Specification

This structure contains information about the specifics of each recording.

??? info "Complete example"

    === "TOML"
        ```toml
        [acquisition_spec]
        software: "Brain Vision Recorder"
        amplifier_model: "Brain Products"
        power_line_freq: 50
        acquisition_freq: 1000
        file_format: ".set"
        
        [acquisition_spec.eeg_channels]
        number: 63
        montage.mne_name: "standard_1005"
        ground: "FPz"
        reference: "VARIES"

        [acquisition_spec.aux_channels.ECG]
        bids_type: "ECG"
        location: {
            "active": "right wrist"
            "reference": "left wrist"
            "ground": "left inner forearm 3 cm distal from the elbow"
        }

        [acquisition_spec.aux_channels.PPG]
        bids_type: "PPG"
        description: "photoplethysmography"
        location: "placed on the left index finger",
        units: "µV"

        [acquisition_spec.aux_channels.audio]
        bids_type: "AUDIO",
        description: "Audio channel",
        location: "n/a"
        
        [[acquisition_spec.filters]]
        name: "Low-pass filter",
        type: "Software",
        info: {
            "cut-off frequency (Hz)": 260
        }
        
        [[acquisition_spec.filters]]
        name: "Anti-aliasing filter"
        type: "Software"
        info: {
            "half-amplitude cutoff (Hz)": 500
            "Roll-off": "6dB/Octave"
        }

        [[acquisition_spec.filters]]
        name: "ADC's decimation filter (hardware bandwidth limit)"
        type: "Hardware",
        info: {
            "-3dB cutoff point (Hz)": 480
            "Filter order sinc response": 5
        }

        [acquisition_spec.extras]
        acceptable_impedance: {"value": 25, "units": "kOhm"},
        electrode_type: "active",
        conductive_medium: "gel",
        faraday_cage: false,
        sound_proof: false,
        lighting_conditions: {
            description: "380 lux ambient lighting",
            measurement: "measured with a luxmeter around the head of the participant"
        }
        ```

    === "YAML"
        ```yaml
        acquisition_spec:
          software: "Brain Vision Recorder"
          amplifier_model: "Brain Products"
          power_line_freq: 50
          acquisition_freq: 1000
          file_format: ".set"
          eeg_channels:
            number: 63
            montage:
              mne_name: "standard_1005"
            ground: "FPz"
            reference: "VARIES"
          aux_channels:
            ECG:
              bids_type: "ECG"
              location:
                active: "right wrist"
                reference: "left wrist",
                ground: "left inner forearm 3 cm distal from the elbow"
            PPG:
              bids_type: "PPG"
              description": "photoplethysmography"
              location: "placed on the left index finger"
              units: "µV"
            audio:
              bids_type: "AUDIO"
              description: "Audio channel"
              location: "n/a"
          filters:
            - name: "Low-pass filter"
              type: "Software"
              info:
                "cut-off frequency (Hz)": 260
            - name: "Anti-aliasing filter"
              type: "Software"
              info:
                "half-amplitude cutoff (Hz)": 500
                "Roll-off": "6dB/Octave"
            - name: "ADC's decimation filter (hardware bandwidth limit)"
              type: "Hardware"
              info:
                "-3dB cutoff point (Hz)": 480
                "Filter order sinc response": 5
          extras:
            acceptable_impedance:
              value: 25
              units: "kOhm"
            electrode_type: "active"
            conductive_medium: "gel"
            faraday_cage: false
            sound_proof: false
            lighting_conditions:
              description: "380 lux ambient lighting"
              measurement: "measured with a luxmeter around the head of the participant"
        ```

    === "JSON"
        ```json
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
                    "bids_type": "ECG",
                    "location": {
                        "active": "right wrist",
                        "reference": "left wrist",
                        "ground": "left inner forearm 3 cm distal from the elbow"
                    }
                },
                "PPG": {
                    "bids_type": "PPG",
                    "description": "photoplethysmography",
                    "location": "placed on the left index finger",
                    "units": "µV"
                },
                "audio": {
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
                },
                {
                  "name": "Anti-aliasing filter"
                    "type": "Software"
                    "info": {
                    "half-amplitude cutoff (Hz)": 500,
                        "Roll-off": "6dB/Octave"
                    }
                },
                {
                   "name": "ADC's decimation filter (hardware bandwidth limit)"
                    "type": "Hardware"
                    "info": {
                        "-3dB cutoff point (Hz)": 480
                        "Filter order sinc response": 5
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
        }
        ```

It can be broken down into several sections:

#### Basic information

This is the basic information about the recording, e.g. sampling frequency, power line frequency, input file format, etc.

=== "TOML"
    ```toml
    software: "Brain Vision Recorder"
    acquisition_freq: 1000
    file_format: ".set"
    amplifier_model: "Brain Products"
    power_line_freq: 50
    ```

=== "YAML"
    ```yaml
    software: "Brain Vision Recorder"
    acquisition_freq: 1000
    file_format: ".set"
    amplifier_model: "Brain Products"
    power_line_freq: 50
    ```

=== "JSON"
    ```json
    "software": "Brain Vision Recorder",
    "acquisition_freq": 1000,
    "file_format": ".set",
    "amplifier_model": "Brain Products",
    "power_line_freq": 50,
    ```

| Field Name       | Type             | Required | Default | Description                                                                                            |
| ---------------- | ---------------- | -------- | ------- | ------------------------------------------------------------------------------------------------------ |
| software         | string           | Yes      | -       | The software used to record the data                                                                   |
| acquisition_freq | positive integer | Yes      | -       | The sampling frequency the data was recorded at                                                        |
| file_format      | string           | Yes      | -       | The extension for the EEG data files. <br>[see MNE's `read_raw`][mne_read_raw] for readable extensions |
| amplifier_model  | string           | Yes      | -       | The amplifier model used to record the data                                                            |
| power_line_freq  | `50` or `60`     | Yes      | -       | Frequency (in Hz) of the power grid at the geographical location of the instrument                     |

#### EEG channel information

This structure contains information about the EEG channels present in the recording.  

=== "TOML"
    ```toml
    [acquisition_spec.eeg_channels]
    number: 63
    montage.mne_name: "standard_1005"
    ground: "FPz"
    reference: "VARIES"
    ```

=== "YAML"
    ```yaml
    eeg_channels:
      number: 63
      montage:
        mne_name: "standard_1005"
      ground: "FPz"
      reference: "VARIES"
    ```

=== "JSON"
    ```json
    "eeg_channels": {
        "number" : 63,
        "montage": {
            "mne_name": "standard_1005"
        },
        "ground": "FPz",
        "reference": "Cz"
    }
    ```

| Field Name | Type             | Required | Default | Description                                                                                                              |
| ---------- | ---------------- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------ |
| number     | positive integer | Yes      | -       | The number of EEG channels in the recording data                                                                         |
| montage    | dictionary       | Yes      | -       | A dictionary with either a named montage or a file path to a custom montage. <br>[See below](#montage) for more details. |
| ground     | string           | Yes      | -       | The name of the ground electrode                                                                                         |
| reference  | string           | Yes      | -       | The name of the reference electrode                                                                                      |

##### Montage

The montage provided can either be a named montage (`mne_name`) or a path to a file specifying a custom montage (`path`). Providing both or neither will raise an error.  
The named montage must be one of the named montages available from the list of [standard MNE montages][built_in_montages].  
The custom montage file can be any that [MNE can read][read_custom_montage].  

=== "Named montage"

    === "TOML"
        ``` toml
        montage.mne_name: "standard_1005"
        ```
    === "YAML"
        ```yaml
        montage:
          mne_name: "standard_1005"
        ```
    === "JSON"
        ``` json
        "montage": {
            "mne_name": "standard_1005"
        }
        ```

=== "Custom Montage"
    === "TOML"
        ``` toml
        montage.path: "path/to/custom/montage.loc"
        ```
    === "YAML"
        ```yaml
        montage:
          path: "path/to/custom/montage.loc"
        ```
    === "JSON"
        ``` json
        "montage": {
            "path": "path/to/custom/montage.loc"
        }
        ```

#### Auxiliary channel information

This structure outlines the details of all the non-EEG channels present in the recordings.  
It consists of a dictionary with an entry for each auxiliary channel in the recording. The key for a channel should be the name of the channel as it appears in the recording, and the value should be a dictionary containing further information about that channel, [see below](#auxiliary-channel-description) for more details.  

=== "TOML"
    ``` toml
    [acquisition_spec.aux_channels.ECG]
    bids_type: "ECG"
    location: {
        "active": "right wrist"
        "reference": "left wrist"
        "ground": "left inner forearm 3 cm distal from the elbow"
    }

    [acquisition_spec.aux_channels.PPG]
    bids_type: "PPG"
    description: "photoplethysmography"
    location: "placed on the left index finger"
    units: "µV"

    [acquisition_spec.aux_channels.audio]
    bids_type: "AUDIO"
    description: "Audio channel"
    location: "n/a"
    ```
=== "YAML"
    ``` yaml
    aux_channels:
      ECG:
        bids_type: "ECG"
        location:
          active: "right wrist"
          reference: "left wrist",
          ground: "left inner forearm 3 cm distal from the elbow"
      PPG:
        bids_type: "PPG"
        description": "photoplethysmography"
        location: "placed on the left index finger"
        units: "µV"
      audio:
        bids_type: "AUDIO"
        description: "Audio channel"
        location: "n/a"
    ```
=== "JSON"
    ``` json
    "aux_channels": {
        "ECG": {
            "bids_type": "ECG",
            "location": {
                "active": "right wrist",
                "reference": "left wrist",
                "ground": "left inner forearm 3 cm distal from the elbow"
            }
        },
        "PPG": {
            "bids_type": "PPG",
            "description": "photoplethysmography",
            "location": "placed on the left index finger",
            "units": "µV"
        },
        "audio": {
            "bids_type": "AUDIO",
            "description": "Audio channel",
            "location": "n/a"
        }
    }
    ```

##### Auxiliary channel description

This object should be included as the value for each auxiliary channel.

| Field Name  | Type                 | Required | Default | Description                                                                                                                                       |
| ----------- | -------------------- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| bids_type   | string               | Yes      | -       | The BIDS channel type. See the [list of possible values][bids_chans]                                                                              |
| description | string               | No       | -       | A short description of the channel                                                                                                                |
| location    | string or dictionary | No       | -       | A description of where the channel is located. <br>If the channel is multi-electrode then this can be a dictionary with a location per electrode. |
| units       | string               | No       | -       | The units the channel is recorded in                                                                                                              |

#### Filter Information

This section consists of a list of all the hardware and software filters specified for the recording.  
Each filter should consist of an dictionary with a name, a type (Hardware or Software), and information about the filter properties. As shown below there can be multiple filters of the same type, but they much have unique names.  
Filter information should be represented in an object with key-value pairs. Each key is a property of the filter and each value is the value of that property. This information is translated directly to the BIDS recording sidecar file.

=== "TOML"
    ``` toml
    [[acquisition_spec.filters]]
    name: "Low-pass filter"
    type: "Software"
    info: {
        "cut-off frequency (Hz)": 260
    }

    [[acquisition_spec.filters]]
    name: "Anti-aliasing filter"
    type: "Software"
    info: {
        "half-amplitude cutoff (Hz)": 500
        "Roll-off": "6dB/Octave"
    }

    [[acquisition_spec.filters]]
    name: "ADC's decimation filter (hardware bandwidth limit)"
    type: "Hardware",
    info: {
        "-3dB cutoff point (Hz)": 480
        "Filter order sinc response": 5
    }
    ```
=== "YAML"
    ``` yaml
    filters:
      - name: "Low-pass filter"
        type: "Software"
        info:
          "cut-off frequency (Hz)": 260
      - name: "Anti-aliasing filter"
        type: "Software"
        info:
          "half-amplitude cutoff (Hz)": 500
          "Roll-off": "6dB/Octave"
      - name: "ADC's decimation filter (hardware bandwidth limit)"
        type: "Hardware"
        info:
          "-3dB cutoff point (Hz)": 480
          "Filter order sinc response": 5
    ```
=== "JSON"
    ``` json
    "filters": [
        {
            "name": "Low-pass filter",
            "type": "Software",
            "info": {
                "cut-off frequency (Hz)": 260
            }
        },
        {
            "name": "Anti-aliasing filter"
            "type": "Software"
            "info": {
              "half-amplitude cutoff (Hz)": 500,
                "Roll-off": "6dB/Octave"
            }
        },
        {
            "name": "ADC's decimation filter (hardware bandwidth limit)"
            "type": "Hardware"
            "info": {
                "-3dB cutoff point (Hz)": 480
                "Filter order sinc response": 5
            }
        }
    ],
    ```

#### Extra information

This structure specifies extra metadata that may be recorded but does not have a formal place in BIDS, and so may optionally be included in the final BIDS-compliant dataset.
This section is entirely optional, as are each of the fields contained within.

=== "TOML"
    ``` toml
    [acquisition_spec.extras]
    acceptable_impedance: {"value": 25, "units": "kOhm"}
    electrode_type: "active"
    conductive_medium: "gel"
    faraday_cage: false
    sound_proof: false
    lighting_conditions: {
        description: "380 lux ambient lighting",
        measurement: "measured with a luxmeter around the head of the participant"
    }
    ```
=== "YAML"
    ``` yaml
    extras:
      acceptable_impedance:
        value: 25
        units: "kOhm"
      electrode_type: "active"
      conductive_medium: "gel"
      faraday_cage: false
      sound_proof: false
      lighting_conditions:
        description: "380 lux ambient lighting"
        measurement: "measured with a luxmeter around the head of the participant"
    ```
=== "JSON"
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

| Field Name           | Type       | Description                                                                                                                                            |
| -------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| acceptable_impedance | dictionary | A dictionary specifying the acceptable impedance value and units for the recording                                                                     |
| electrode_type       | string     | The type of electrode used in the recording                                                                                                            |
| conductive_medium    | string     | The type of conductive medium used for the recording                                                                                                   |
| faraday_cage         | boolean    | Was the data recorded in a faraday cage?                                                                                                               |
| sound_proof          | boolean    | Was the data recorded in a room with sound proofing?                                                                                                   |
| lighting_conditions  | dictionary | A dictionary specifying the lighting conditions during the recording. <br>If present, must include a description, but measurement details are optional |

### Resting-state information

This section contains details for the resting state tasks undertaken during the recording.  
In includes information about the instructions issued to the participants, the duration of the eyes-open and eyes-closed tasks, the stimuli used during these tasks, any other tasks recorded, and the details of the event markers captured during the recording.  

??? info "Complete example"

    === "TOML"
        ``` toml
        [resting_state]
        instructions: "A prerecorded voice gave commands to open and close the eyes every minute. The stimuli were presented in PsychoPy."
        
        [resting_state.eyes_closed]
        duration_secs: 240

        [resting_state.eyes_open]
        duration_secs: 240
        stimulus_description: "white fixation cross on a grey background"

        [[resting_state.other_task]]
        task_name: "video watching"
        duration_secs: 231
        stimulus_description: "a short animated movie 'The man who was afraid of falling' (https://osf.io/x9jpz)"

        [resting_state.events]
        "S 20": "Eyes open"
        "S 21": "Eyes closed"
        "S 22": "Movie start"
        "S 23": "Movie end"
        "S254": "Start of Resting State Recording"
        "S252": "End of Resting State Recording"
        ```
    === "YAML"
        ``` yaml
        resting_state:
          instructions: "A prerecorded voice gave commands to open and close the eyes every minute. The stimuli were presented in PsychoPy."
          eyes_closed:
            duration_secs: 240
          eyes_open:
            duration_secs: 240
            stimulus_description: "white fixation cross on a grey background"
          other_task:
            - task_name: "video watching"
              duration_secs: 231
              stimulus_description: "a short animated movie 'The man who was afraid of falling' (https://osf.io/x9jpz)"
          events:
            "S 20": "Eyes open"
            "S 21": "Eyes closed"
            "S 22": "Movie start"
            "S 23": "Movie end"
            "S254": "Start of Resting State Recording"
            "S252": "End of Resting State Recording"
        ```
    === "JSON"
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

| Field Name   | Type                  | Required | Description                                                                                                                                           |
| ------------ | --------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| instructions | string                | Yes      | A description of the instructions provided to participants, specifically what and how                                                                 |
| eyes_closed  | dictionary or `false` | Yes      | Details of the eyes closed resting-state condition. [See below](#resting-task) for more details. <br>Must be explicitly set to `False` if not present |
| eyes_open    | dictionary or `false` | Yes      | Details of the eyes open resting-state condition. [See below](#resting-task) for more details. <br>Must be explicitly set to `False` if not present   |
| other_task   | list( dictionary )    | No       | Details of other resting-state tasks recorded. [See below](#other-task) for more details.                                                             |
| events       | dictionary            | Yes      | Details of the event markers used within the recording.                                                                                               |

#### Resting task

Eyes-open and Eyes-closed are considered to be the default resting-state tasks, and are both incorporated under the single "rest" task.  
Either or both may not be present, but they have to be explicitly set to `False` in the metadata to indicate this.  

When present, both conditions should have the 'condition duration in seconds' (`duration_secs`) field. The value for this field should be a positive integer.  
Optionally, either of these conditions can have a description of the stimulus presented in the condition (`stimulus_description`).  
e.g.:

=== "TOML"
    ```toml
    [resting_state.eyes_closed]
    duration_secs: 240

    [resting_state.eyes_open]
    duration_secs: 240
    stimulus_description: "white fixation cross on a grey background"
    ```
=== "YAML"
    ```yaml
    eyes_closed:
      duration_secs: 240
    eyes_open:
      duration_secs: 240
      stimulus_description: "white fixation cross on a grey background"
    ```
=== "JSON"
    ```json
    "eyes_closed": {
        "duration_secs": 240
    },
    "eyes_open": {
        "duration_secs": 240,
        "stimulus_description": "white fixation cross on a grey background"
    }
    ```

#### Other task

All other resting-state tasks recorded should be included under the `other_task` field. This is a list of dictionaries, with each dictionary describing a specific condition.  
When a task is included all of the fields in the dictionary describing it are required.

=== "TOML"
    ```toml
    [[resting_state.other_task]]
    task_name: "video watching"
    duration_secs: 231
    stimulus_description: "a short animated movie 'The man who was afraid of falling' (https://osf.io/x9jpz)"
    ```
=== "YAML"
    ```yaml
    other_task:
    - task_name: "video watching"
      duration_secs: 231
      stimulus_description: "a short animated movie 'The man who was afraid of falling' (https://osf.io/x9jpz)"
    ```
=== "JSON"
    ```json
    "other_task": [
        {
            "task_name": "video watching",
            "duration_secs": 231,
            "stimulus_description": "a short animated movie 'The man who was afraid of falling' (https://osf.io/x9jpz)"
        }
    ]
    ```

| Field Name           | Type             | Description                                              |
| -------------------- | ---------------- | -------------------------------------------------------- |
| task_name            | string           | The name of the task.                                    |
| duration_secs        | positive integer | The duration of the task in seconds.                     |
| stimulus_description | string           | A description of the stimuli presented during this task. |

#### Events

THis field contains a dictionary mapping the event markers in the recording with a human-readable tag describing what the event represents.  
The dictionary should use strings for both the keys (the event markers) and the values (the human-readable tags). e.g.:

=== "TOML"
    ```toml
    [resting_state.events]
    "S 20": "Eyes open"
    "S 21": "Eyes closed"
    "S 22": "Movie start"
    "S 23": "Movie end"
    "S254": "Start of Resting State Recording"
    "S252": "End of Resting State Recording"
    ```
=== "YAML"
    ```yaml
    events:
      "S 20": "Eyes open"
      "S 21": "Eyes closed"
      "S 22": "Movie start"
      "S 23": "Movie end"
      "S254": "Start of Resting State Recording"
      "S252": "End of Resting State Recording"
    ```
=== "JSON"
    ```json
    "events": {
        "S 20": "Eyes open",
        "S 21": "Eyes closed",
        "S 22": "Movie start",
        "S 23": "Movie end",
        "S254": "Start of Resting State Recording",
        "S252": "End of Resting State Recording"
    }
    ```

## Participant metadata

The participant metadata contains key information about each participant. It is provided in the form of a spreadsheet with a worksheet containing tabular data: one row par participant and one column per variable. It may also include a worksheet for phenotype information for each participant, again in tabular form.  
Each worksheet containing tabular data must be accompanied by a codebook worksheet that provides a description for each variable in the associated tabular data.  
As such the participant metadata spreadsheet should consist of either:

- Two worksheets (participant data and associated codebook), or
- Four worksheets (participant data and codebook, plus phenotype data and codebook).

By default a `.ods` spreadsheet is expected, but this can be customised in the [configuration file](configuration.md#spreadsheet-extension).

### Participant data and codebook

The participant data should contain the following column headings at a minimum:

| participant-id | age | sex | handedness |
| -------------- | --- | --- | ---------- |
| sub-001        | 34  | M   | R          |
| sub-002        | 27  | F   | A          |
| ...            | ... | ... | ...        |

The values in the `participant-id` column should match the subject directory names.  
A default mapping (to MNE-compliant values; e.g. M -> 1, etc.) for the values in the `sex` and `handedness` column is outlined in the [configuration section](configuration.md#demographic-mappings), but a custom mapping can also be defined.

The codebook sheet for the participant data should contain two columns:

| Variable       | Description                     |
| -------------- | ------------------------------- |
| participant-id | unique participant identifier   |
| age            | age of the participant in years |
| sex            | sex of the participant          |
| handedness     | dominant hand                   |

The values in the `Variable` column should match the column names in the participant data sheet. The `Description` column should include a brief description of the providing context for the values in the `Variable` column.

### Phenotype data and codebook

Phenotype data is additional information about each participant that was collected as part of a research project. This could be: education level, socio-economic status, the results of standardised tests, or some other quantitative variable.

The worksheet containing the tabular data for these measures must include a `participant-id` column, and the values of this column must match the values in the participant data worksheet. Additional columns can be added to accommodate the other information being provided, the only limitations are:

- Each column should have a unique name.
- Each column should have a row with description in the associated phenotype data codebook.

| participant-id | years_of_education | IQ  | ... |
| -------------- | ------------------ | --- | --- |
| sub-001        | 10                 | 110 | ... |
| sub-002        | 5                  | 107 | ... |
| ...            | ...                | ... | ... |

As with the participant data the phenotype codebook should contain `Variable` and `Description` columns:

| Variable           | Description                                 |
| ------------------ | ------------------------------------------- |
| participant-id     | unique participant identifier               |
| years_of_education | number of years in formal education         |
| IQ                 | participant IQ as measured by the WAIS-5-UK |
| ...                | ...                                         |

[toml_spec]: https://toml.io/en/v1.1.0
[yaml_spec]: https://yaml.org/spec/1.2.2/
[json_spec]: https://www.json.org/json-en.html
[mne_read_raw]: https://mne.tools/stable/generated/mne.io.read_raw.html
[built_in_montages]: https://mne.tools/stable/auto_tutorials/intro/40_sensor_locations.html#working-with-built-in-montages
[read_custom_montage]: https://mne.tools/stable/generated/mne.channels.read_custom_montage.html
[bids_chans]: https://bids-specification.readthedocs.io/en/stable/glossary.html#objects.columns.type__channels
