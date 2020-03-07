#!/bin/sh

pip install -r test_requirements.txt

auth_api db upgrade

pylint auth_api --rcfile=pylintrc

pytest tests