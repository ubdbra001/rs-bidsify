---
title: Dataset structure
---

## Single task

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

The JSON file containing the dataset metadata and the spreadsheet containing the participant information should be in the root of the raw data directory. These do not have to be named as in the example above, but should have the correct file extensions, and there should only be a single file for each. The example above shows the default file extensions for both the dataset metadata file and the participant spreadsheet, however these can be altered in a [custom configuration file](configuration.md).

The names of the subject directories should match the values in the `participant-id` column of the participant spreadsheet.

## Multiple tasks

Each subject directory can, optionally, contain task sub-directories, but again there should be a single recording per directory. e.g.:

```shell
dataset/
├── sub-001/
│   ├── rest/
│   │   └── sub-001-rest.edf
│   └── video/
│       └── sub-001-video.edf
...
```

If the dataset contains multiple tasks, these should be included in the metadata file (in the [tasks section](metadata.md#tasks)) with identical names.
