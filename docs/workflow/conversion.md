# Conversion

Once the incoming metadata and the structure of the dataset has been validated then each EEG recording can be loaded into an MNE RawData object. From here some inital consistency checks are performed (e.g. ensrung that the sampling frequency specified in the metadata matches the value in the recordings), then some initial metadata is added to the data object. Finally, MNE-BIDS is used to save the recording and associated metadata in a BIDS compliant structure.

However, MNE-BIDS is not able to add all the metadata available into the BIDS-compliant dataset, and so the next step is enriching the existing files.

``` mermaid
graph TD

    MetaMem@{ shape: win-pane, label: "Dataset Metadata" }

    RawData@{ shape: docs, label: "Raw Resting-State EEG dataset" }
    BIDSmini@{ shape: docs, label: "BIDS-compliant dataset: Minimally compliant" }
    RecMem@{ shape: win-pane, label: "Available EEG recordings" }

    PartMem@{ shape: win-pane, label: "Participant data" }

    subgraph perRec ["Per EEG recording"]
        LoadRec["Load Raw Data"]
        MNERec@{ shape: win-pane, label: "MNE Data object" }
        ConCheck["Consistency Checks"]
        InitialEnrich["Initial metadata enrichment"]
        SaveData["Save initial dataset"]
    end

    RawData --> LoadRec --> MNERec --> ConCheck
    MetaMem --> ConCheck
    MetaMem --> InitialEnrich
    PartMem --> InitialEnrich
    ConCheck --> InitialEnrich --> SaveData --> BIDSmini
    RecMem --> perRec


    classDef docNode stroke:black
    classDef processNode fill:lightgreen,stroke:black
    classDef memNode fill:lightyellow,stroke:black

    %%class RawData,BIDSmini docNode
    %%class LoadRec,ConCheck,InitialEnrich,SaveData processNode
    %%class MetaMem,MNERec,RecMem,PartMem memNode
```