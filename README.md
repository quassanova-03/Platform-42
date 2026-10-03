# Platform 42

### Indian Railway Delay Analytics & Automation

Platform 42 is a Linux-based railway delay analysis and automation system
that processes Indian railway route data, validates the input datasets,
stores the data in SQLite, performs multi-level delay analysis, and
automatically generates analytical reports using Bash and Cron.

The system was built to turn raw railway route data into structured,
queryable information while demonstrating a complete data-processing and
automation pipeline.

---

## Overview

Platform 42 works with a dataset containing **42 trains**, their route
information, and historical delay statistics.

The system takes the raw CSV files through a validation and processing
pipeline:

```text
Train CSV Data
       │
       ▼
   Validator 
       │
   Valid data?
     │     │
    YES    NO
     │      └──────────► Stop
     ▼
  SQLite Import
       |
       ▼
   Analytics
       |
       ▼
  Daily Report
       |
       ▼
  Cron Automation
```
The complete pipeline has been tested with:

- 42 train records
- 42 train route files
- 1,479 route records
- 0 validation errors
- 0 validation warnings

## Features

### 1. Data Validation

Before any data is imported into the database, Platform 42 validates the
source files.

The validator checks for:

- Missing route files
- Missing required columns
- Duplicate train numbers
- Invalid train numbers
- Missing fields
- Invalid or negative delay values
- Invalid percentage values
- Incorrect delay-category percentages
- Malformed route records
- Missing train-route relationships

Invalid data stops the pipeline before it reaches the database.

### 2. SQLite Database

Validated train and route data is imported into a local SQLite database.

The database stores information including:

- Train numbers
- Station codes
- Station names
- Average delays
- Right-time percentages
- Slight delays
- Significant delays
- Cancelled/unknown records

SQLite keeps the project lightweight while allowing the data to be queried
using standard SQL.

### 3. Multi-Level Delay Analytics

Platform 42 provides several ways to analyze the dataset.

#### Train-level analysis

Identify trains with the highest average delays.
```
python3 scripts/analytics.py top
```
Limit the number of results:
```
python3 scripts/analytics.py top --limit 5
```
#### Station-level analysis

Analyze delay patterns at a specific station:
```
python3 scripts/analytics.py station KNE
```
Rank stations by average delay:
```
python3 scripts/analytics.py stations
```
Or limit the results:
```
python3 scripts/analytics.py stations --limit 5
```
#### Train comparison

Compare the delay performance of two trains:
```
python3 scripts/analytics.py compare 02501 20503
```
#### Network-level analysis

View overall statistics across the dataset:
```
python3 scripts/analytics.py network
```
Severe-delay analysis

Identify trains with a high proportion of delays exceeding one hour:
```
python3 scripts/analytics.py severe
```
Limit the results:
```
python3 scripts/analytics.py severe --limit 5
```
#### Route-level analysis

Examine how delays change from station to station along a train's route:
```
python3 scripts/analytics.py route 02501
```
This includes:

- Starting delay
- Ending delay
- Overall delay change
- Largest delay increases between consecutive stations

### 4. Automated Reports

Platform 42 generates a daily analytical report containing:

- Network summary
- Number of trains
- Number of route records
- Average station delay
- Right-time percentage
- Slight-delay percentage
- Significant-delay percentage
- Cancelled/unknown percentage
- Top trains by average delay
- Top stations by average delay
- Trains with the highest proportion of severe delays
- Largest delay increases along routes

Reports are generated automatically and stored in the reports/ directory.

### 5. Bash + Cron Automation

The complete process can be executed through a single Bash script:
```
bash scripts/daily_update.sh
```
The script performs the following steps:
```
1. Navigate to the project directory
              ↓
2. Validate the source datasets
              ↓
3. Stop if validation fails
              ↓
4. Import validated data into SQLite
              ↓
5. Generate analytical reports
              ↓
6. Record timestamps and execution output
              ↓
7. Complete the update
```
The pipeline uses Cron to schedule the process automatically.

This allows the entire validation → database → analytics → reporting
workflow to run without manually executing every step.

## Complete Pipeline
```
                 ┌──────────────────┐
                 │   Railway CSVs   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    Validator     │
                 │                  │
                 │ Data quality     │
                 │ checks           │
                 └────────┬─────────┘
                          │
                    Valid data
                          │
                          ▼
                 ┌──────────────────┐
                 │  SQLite Database │
                 │                  │
                 │ 42 trains        │
                 │ 1479 routes      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    Analytics     │
                 │                  │
                 │ Train            │
                 │ Station          │
                 │ Network          │
                 │ Route            │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Analytical Report│
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │  Bash + Cron     │
                 │   Automation     │
                 └──────────────────┘
```

## Project Structure
```
Platform_42/
│
├── Train_List.csv
│
├── Train_Routes/
│   ├── route_02501.csv
│   ├── route_02502.csv
│   └── ...
│
├── scripts/
│   ├── analytics.py
│   ├── daily_update.sh
│   ├── database.py
│   ├── report.py
│   ├── report_v2.py
│   ├── tracker.py
│   └── validator.py
│
├── database/
│   └── transport.db
│
├── reports/
│   └── generated reports
│
└── logs/
    └── cron.log
```

## Technologies

| Technology | Purpose |
|---|---|
| **Python** | Data processing, validation and analytics |
| **SQLite** | Local relational database |
| **Bash** | Pipeline automation |
| **Cron** | Scheduled execution |
| **Linux / WSL** | Execution environment |
| **CSV** | Source dataset format |
| **SQL** | Database querying |


## Setup
Platform 42 is designed to run in a Linux environment. It can also be
run through WSL (Windows Subsystem for Linux) on Windows.

#### 1. Clone the repository
```
git clone <repository-url>
cd Platform_42
```
#### 2. Verify Python
```
python3 --version
```
Python 3 is required.

#### 3. Validate the dataset
```
python3 scripts/validator.py
```
A successful validation should report:
```
42 train records
42 unique train numbers
42 route files
42 valid route files
1479 valid route records
0 missing route files
0 errors
0 warnings

STATUS: VALID
```
#### 4. Build the database
```
python3 scripts/database.py
```
#### 5. Run analytics

For example:
```
python3 scripts/analytics.py network
```
or:
```
python3 scripts/analytics.py top --limit 5
```
#### 6. Generate a report
```
python3 scripts/report_v2.py
```
#### 7. Run the complete pipeline
```
bash scripts/daily_update.sh
```

### Cron Setup

To schedule automatic execution, open the user's Cron configuration:
```
crontab -e
```
Add a schedule that runs daily_update.sh at the desired interval.

To verify the configured jobs:
```
crontab -l
```
Cron execution output can be recorded in:
```
logs/cron.log
```
Note: Uploading Platform 42 to GitHub does not run Cron on GitHub.
Cron runs in the Linux/WSL environment where the project is installed.
The repository contains the scripts and configuration needed to reproduce
the automation locally.

## What This Project Demonstrates
Platform 42 brings together several parts of a typical data-processing and
systems workflow:
- Structured data validation
- Relational database design
- SQL-based querying
- Python scripting
- Command-line analytics
- Linux environment usage
- Bash scripting
- Scheduled automation with Cron
- Pipeline failure handling
- Automated report generation
- Working with multiple related CSV datasets
The focus is not just on analyzing railway delays, but on building a
repeatable pipeline that can validate, process, analyze, and report on
data automatically.


## Example Output
#### VALIDATION
<img width="1226" height="608" alt="image" src="https://github.com/user-attachments/assets/a233dd8e-8710-4566-9e84-be7f1db79b06" />

#### ANALYTICS
<img width="1330" height="322" alt="image" src="https://github.com/user-attachments/assets/1a27b5de-2cca-4a54-bccb-3828cc02e558" />

#### FULL AUTOMATION
<img width="1228" height="842" alt="image" src="https://github.com/user-attachments/assets/a1ab275c-8bce-4115-a0ec-249407df5888" />
<img width="1080" height="707" alt="image" src="https://github.com/user-attachments/assets/0ea791b9-a67b-4b10-8bfe-1c36aff9e41e" />
<img width="828" height="942" alt="image" src="https://github.com/user-attachments/assets/889f02fe-0e62-44fa-ba82-c7bb5f730b47" />
<img width="937" height="468" alt="image" src="https://github.com/user-attachments/assets/1c8a8c04-c786-49b6-a629-c3d2978e46e2" />

## Dataset
Platform 42 uses the DA323 Indian Railway Train Delay Dataset.

Dataset source:
https://github.com/ankitaanand28/DA323_IndianRailwayTrainDelayDatasets

The repository contains the train list and individual route CSV files used
by the system.

## Notes

Platform 42 is a dataset-based delay analysis system.

The included dataset represents the source data available to the project
and should not be interpreted as a live railway tracking service.

The automated Cron pipeline periodically reprocesses the local dataset.
If the underlying CSV files are updated, the next scheduled execution can
validate, import, analyze, and report on the updated data.
