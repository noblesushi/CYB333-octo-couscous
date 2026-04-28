---

# Modular Automated Log Analysis for MITRE ATT&CK Mapping

This project is a Python-based Jupyter Notebook to ingest security logs reformatted as CSV files, apply rule-based detections, and map results to the MITRE ATT&CK framework.

The intent is to create a way to filter and visualize historical attacks to identify trends and adjust security posture accordingly.

---

## Overview

The notebook demonstrates how security automation can replace manual log review by:

* Loading and normalizing log data from one or more CSV files
* Detecting suspicious behavior using modular rules
* Mapping detections to MITRE ATT&CK techniques
* Aggregating results into a single alert dataset
* Producing basic visualizations for analysis

MITRE reference: [https://attack.mitre.org/](https://attack.mitre.org/)

---

## Features

### Detection Rules

Includes both core and extended detections:

* Scanner user agent detection
* Blocked probe bursts
* Login endpoint probing
* Suspicious web payload indicators
* High-volume sensitive path access
* Rare source/destination pairs
* Rare protocol usage
* Multi-destination access (fan-out)
* Byte transfer outliers
* Time-clustered activity

Each detection is implemented as a standalone function and appends results to a shared `all_alerts` dataset.

---

## Data Input

The notebook expects CSV files with the following schema:

```
timestamp,source_ip,dest_ip,protocol,action,threat_label,log_type,bytes_transferred,user_agent,request_path
```
* Dataset was source from https://www.kaggle.com/datasets/aryan208/cybersecurity-threat-detection-logs under a CC0 license
* `threat_label` is not used in detection logic
* It may be used later for validation only

Multiple files are supported:

```python
CSV_PATHS = ["cybersecurity_threat_detection_logs.csv"]
```

---

## Setup

Install dependencies:

```
pip install pandas matplotlib
```

or:

```
conda install pandas matplotlib
```

Run the notebook:

```
jupyter notebook
```

Then execute all cells.

---

## Output

Detections are stored in `all_alerts`, which includes:

* detection name
* severity
* timestamp
* source and destination
* protocol
* supporting evidence
* MITRE ATT&CK mapping

The notebook also generates basic visualizations, including time-based heatmaps and protocol distributions.

---

## Notes

* Detection logic is rule-based and intentionally simple
* The design is modular and easy to extend
* Visualizations are included for basic analysis, not full SIEM functionality or pipeline integration
* When not using the "Run All" functionality, run steps 1-6, then any desired tests.

---

## Potential Future Improvements

* Code to attempt to map non-standardized CSV labels to existent labels
* Code to take raw logs and convert to CSV
* Parameterization for tests to make them more flexible and allow alignment with organization posture/policy
* Date range/last N entries filtering for large files
* "Run Setup" button to assist users who only want to run some tests but shouldn't have to press all 6 setup steps manually

__

## License

CC0 1.0 Universal (Public Domain Dedication)
