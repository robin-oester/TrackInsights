# TrackInsights: Replication of the Swiss Athletics Database
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)


## Local Setup

Run the following commands (in the root folder) to set up the project locally:
```bash
conda env create -f ./environment.yml
conda activate track-insights
pip install -e .
```

For testing, also install the dev dependencies via:
```bash
pip install -r dev-requirements.txt
```

## Database Setup

In order to properly run the system, please install a database system (e.g., MySQL) on your local machine.
Create a new database and preferably also a new user for this system.
Edit the corresponding fields in ```track_insights/config/configuration.yaml``` to make it usable.

## First Steps
Go to the folder ```track_insights```, which holds the important code files.
In order to become familiar with the system, execute the main method in ```track_insights/main.py```.
This should setup the tables in the database and perform the scraping of 100 longjump results from 
the year 2023.

## Execute Tests
All tests can be run via the console:
```bash
pytest .
```
