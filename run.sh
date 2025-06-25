#!/usr/bin/env bash
cd ~/.ip-reporter
source ~/.venvs/ip-reporter/bin/activate
python3 main.py --mode report
deactivate
