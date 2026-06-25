# Getting started with RS-BIDSify

## Installation

`RS-BIDSify` works with `python` 3.12 and later.  
It is currently not available on PyPI, and so needs be installed directly from GitHub:

``` shell
pip install rs-bidsify@git+https://github.com/ubdbra001/rs-bidsify.git
```

It is recommended that you install the package into a [virtual environment](https://docs.python.org/3/library/venv.html).

## Data preparation

There are three key elements required to convert an existing resting state EEG (RS-EEG) dataset to BIDS using `RS-BIDSify`:

1. **Recording metadata**: A JSON file specifying key metadata about the EEG recording environment.
2. **Participant metadata**: A spreadsheet containing participant-level metadata, and, optionally, phenotype metadata.
3. **The raw dataset**: The directory structure containing the raw RS-EEG dataset, and the above metadata files.

For more specific information about the metadata files and their structure refer to the [metadata section](usage/metadata.md). Likewise, refer to the [dataset section](usage/dataset.md) for specific information about the expected dataset structure.

## Conversion

Once the three elements listed above are correct then you can use the `convert` command to convert your raw dataset to a BIDS-compliant dataset:

``` shell
rs-bidsify convert path/to/input path/to/output
```

For more specific information about `convert` command, including its options see the [commands section](usage/commands.md).
