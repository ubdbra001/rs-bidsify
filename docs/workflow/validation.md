# Validation

This step reads the metadata JSON to ensure that the values present are valid. It also ensures that the directory structure for the dataset is as expected. Any discrepancies in validation will raise an error and stop processing.

Once these have been verified the metadata, participant spreadsheet, and a list of EEG recordings in the dataset are available in memory for the latter steps to use.

``` mermaid
graph TD

    JSON@{ shape: doc, label: "Dataset metadata (JSON)"}
    MetaValid["Metadata validation"]
    MetaMem@{ shape: win-pane, label: "Dataset Metadata" }

    RawData@{ shape: docs, label: "Raw Resting-State EEG dataset" }
    RecValid["Directory structure validation"]
    RecMem@{ shape: win-pane, label: "Available EEG recordings" }

    PartSpread@{ shape: doc, label: "Particpant spreadsheet"}
    PartValid["Participant information validation"]
    PartMem@{ shape: win-pane, label: "Participant data" }
    PhenoMem@{ shape: win-pane, label: "Phenotype data" }

    JSON --> MetaValid --> MetaMem
    PartSpread --> PartValid --> PartMem
    PartValid --> PhenoMem

    RawData --> RecValid --> RecMem

    PartMem -.-> RecValid
    MetaMem -.-> RecValid

    classDef docNode stroke:black
    classDef processNode fill:lightgreen,stroke:black
    classDef memNode fill:lightyellow,stroke:black

    %%class PartSpread,RawData,JSON docNode
    %%class MetaValid,PartValid,RecValid processNode
    %%class MetaMem,PartMem,PhenoMem,RecMem memNode
```