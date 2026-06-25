---
title: Using RS-BIDSIfy 
---

## Command line interface

`RS-BIDSify` has two main commands:

### `check`

This command is used to validate the input dataset metadata and structure without actually converting the data. This allows a rapid way to identify and resolve issues with the inputs.

**Usage**

```shell
rs-bidsify check path/to/raw/dataset
```

**Options**

The `check` command allows a [custom configuration file](configuration.md) to be passed using the `--config` option.

### `convert`

This command validates the input dataset metadata and structure, and then converts the input data to a BIDS-compliant dataset.  
In normal usage, the `convert` command will skip existing BIDS-compatible data (e.g. existing subject directories/tasks) and will skip over recordings where an error is encountered. A summary of the status for each subject (and task) will be printed at the end of processing.  
Each of these behaviours can be modified with the `--force` and `--strict` flags described below.

**Usage**

```shell
rs-bidsify convert path/to/raw/dataset path/to/output/dir
```

**Option**

The `convert` command includes a number of flags to adjust its operation:

- `--config`: Specify a [custom YAML configuration file](configuration.md)
- `--logs`: Specify a custom directory for log file output
- `--force`/`-f`: Force overwrite of an existing dataset in the output location
- `--strict`/`-s`: Stop immediately when an error is encountered
