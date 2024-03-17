# east_palestine_data

## About
This project is intended to assist with compiling and visualizing data published in connection with the train derailment in East Palestine, OH on February 3, 2023

The first part of this project, contained in the file **data_reader.py**, uses the Tabula-Py library and python to pull data about sampling data off Eurofins lab reports compiled for Norfolk Southern and its contractor, Arcadis.

## Data Source
Eventually, I plan to include multiple sources and additional visualizations. Currently the input sources include:

* [Volume 2](https://www.epa.gov/system/files/documents/2023-06/NS_East%20Palestine%20IRR_WMP_4.10.2023_Vol%202-508.pdf) of the incident's Waste Management Plan
* [Volume 3](https://www.epa.gov/system/files/documents/2023-06/NS_East%20Palestine%20IRR_WMP_4.10.2023_Vol%203-508.pdf) of the incident's Waste Management Plan

## Data Output
21,586 lines of data successfully compiled using **data_reader.py** can be found in the repo at **norfolk_southern_data.csv**
