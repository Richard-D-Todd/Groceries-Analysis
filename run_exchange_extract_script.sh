#! /bin/bash

echo 'activating virtual environment'
activate () {
        . groceries_venv/bin/activate
}
activate
echo 'launching script'
cd 'Extract From Exchange'
python extract_from_exchange_script.py
