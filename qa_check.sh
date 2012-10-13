#!/bin/bash
./manage.py test --with-coverage
if [[ $? -ne 0 ]]; then exit 1; fi
flake8 .
