# Workflow

The overall workflow for using RS-BIDSify is depicted below

``` mermaid
%%{init: {'themeVariables': { 'fontSize': '18px'}}}%%
graph LR

    JSON@{ shape: doc, label: "Dataset metadata (JSON)"}
    PartSpread@{ shape: doc, label: "Particpant spreadsheet"}
    RawData@{ shape: docs, label: "Raw Resting-State EEG dataset" }
    BIDSfull@{shape: docs, label: "BIDS-compliant dataset: enriched metadata"}

    subgraph Layer ["RS-BIDSify" ]
        direction LR
        Validate["Validation" ]
        Convert["Conversion" ]
        BIDSmini@{shape: docs, label: "BIDS-compliant dataset: minimal metadata"}
        Enrich["Enrichment" ]
    end

    Validate --> Convert --> BIDSmini --> Enrich --> BIDSfull
    RawData --> Validate
    JSON --> Validate
    JSON --> Enrich
    PartSpread --> Validate
    PartSpread --> Enrich


```

It consists of 3 stages:  
1. Validate the dataset inputs    
2. Checking and conversion  
3. Enrich the metadata  


Each of these steps is described in more detail in their own sections
