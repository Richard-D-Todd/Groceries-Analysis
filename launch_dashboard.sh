#! /bin/bash
echo 'activating virtual environment'
activate () {
	. groceries_venv/bin/activate
}
activate
echo 'launching dashboard'
cd Dashboard
python index.py
