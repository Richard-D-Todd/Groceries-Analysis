#! /bin/bash

echo 'activating virtual environment'
source groceries_venv/bin/activate

echo 'launching dashboard'
cd Dashboard
python index.py
