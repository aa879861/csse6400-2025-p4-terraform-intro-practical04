#!/bin/bash
#
# Copy the tests directory and run the tests

pipenv install
pipenv run python3 -m unittest discover -s tests

