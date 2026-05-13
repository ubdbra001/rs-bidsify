# Introduction

The `RS-BIDSify` package is designed to take resting-state EEG (RS-EEG) datasets and metadata that do not follow a standard structure, and to standardise them via conversion to the [Brain Imaging Data Structure (BIDS)](https://bids.neuroimaging.io/).

## Background

This package has been has been developed as part of the #EEGManyLabs project to faciliate the curation of existing but dormant RS-EEG datasets. We define a dormant dataset broadly as a dataset that has been collected by researchers, but has not been published or used in published work.  

Curation of these datasets involves the following three steps:  
1. Donation of the dataset and metadata by the researcher who collected them originally  
2. Standardisation of the data and metadata structure  
3. Depostion of the dataset into a publicly available database/repository of RS-EEG datasets  

The `RS-BIDSify` package addesses the second of these steps. See the workflow page for more details about how this standardisation is acheived. 