# Inputs

There are three key inputs required for RS-BIDSify to work:  

1. The metadata JSON file: This is a file specifying the key metadata about the recording environment.  
2. The participant spreadsheet: This is a spreadsheet specifying key information about each particpant.  
3. The dataset: This is the file structure containing the raw RS-EEG files.  

## Metadata JSON file

This file contains the metadata describing the environment that the RS-EEG data was collected in.  

It consists of 5 key sections:  
1. `metadata`: This section describes the overarching features of the dataset, including the authors, institution, funding, etc.   
2. `conditions`: This is a list of all the conditons present in the dataset (each condition should be a seperate recording)  
3. `acquisition_spec`: This section specifies the acquisition settings for the dataset  
4. `resting_state`: This section describes the resting state coditions, events, etc.  
5. `variable_fields`: This optional section provides a mapping between keys that varies between participants and the location of the information in the Participant spreadsheet (i.e. column name).  


## Participant Spreadsheet

The participant spreadsheet contains key information about each participant in tabular form, and may also include tabular phenotype information for each participant. It should also contain a codebook describing each column present in each of tabular datasets.

It should contain four worksheets:  
1. Participant tabular data  
2. Participant data codebook  
3. Phenotype tabular data  
4. Phenotype data codebook


## The Dataset

The dataset should be structured in the following way:  
1. Each participant should have their own directory, with the same name as listed in the participant_id column in the participant spreadsheet.  
2. Each condition should have its own directory nested in the participant directory, and with the same name as given in the metadata. If there is only a single condition, then this directory does not need to be present.  
3. Each participant (or condition, when present) directory should have a single EEG recording file within it.

Below are two example dataset structures:

Data Structure without conditions
```
dataset/
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

Data structure with conditions `rest` and `video`
```
dataset/
├── sub-001/
│   ├── rest/
│   │   └── sub-001-rest.edf
│   └── video/
│       └── sub-001-video.edf
├── sub-002/
│   ├── rest/
│   │   └── sub-002-rest.edf
│   └── video/
│       └── sub-002-video.edf
├── sub-003/
│   ├── rest/
│   │   └── sub-003-rest.edf
│   └── video/
│       └── sub-003-video.edf
├── ...
└── sub-xxx/
    ├── rest/
    │   └── sub-xxx-rest.edf
    └── video/
        └── sub-xxx-video.edf
```
