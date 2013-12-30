#!/bin/bash
TMP=`mktemp -t godo_coverage`
coverage erase
coverage run --branch ./manage.py test
coverage report > $TMP
cat $TMP
if ! tail -n1 $TMP | grep -q "100%"; then
    coverage html
    open htmlcov/index.html
fi
rm $TMP
flake8 .
