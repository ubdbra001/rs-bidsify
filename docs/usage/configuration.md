---
title: "Configuration file"
---

The configuration file should be a `yaml` file, and can be used to set the options outlined below.  
The examples given below are the defaults, and custom files can set individual elements without recreating the whole file.

## Demographic mappings

This describes mappings between text and numeric values for how sex and handedness may be described in the participants spreadsheet. MNE uses numerical values for both sex and handedness ([see `subject_info` dictionary in the MNE `Info` object](https://mne.tools/stable/generated/mne.Info.html)), and so string representations of these values will have to be converted to numeric (and will be converted back during BIDSification).

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

## Sheet info

This describes the sheet name/number and index column for each sheet in the participant information spreadsheet.  
If using numeric values for `sheet_name` indexing starts at 0.

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

## Spreadsheet extension

The file extension to search for when looking up the participant metadata spreadsheet:

``` yaml
spreadsheet_ext: "ods"
```

## Metadata extension

!!! danger
    Reading metadata from other file types (e.g. YAML, TOML, etc.) is not currently implemented.  
    Do not change this option in custom configuration files.

The file extension to search for when looking up the metadata file:

``` yaml
metadata_ext: "json"
```

## Output EEG format

The file format to save the EEG data to in the BIDS-compliant output:

```yaml
output_EEG_format: "edf"
```

## Include extra information

A flag indicating whether the extra information section of the metadata should be written to the EEG recording sidecar files.

```yaml
include_extras: true
```
