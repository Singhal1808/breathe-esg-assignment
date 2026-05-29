#!/usr/bin/env bash
set -e

python manage.py migrate
python manage.py seed_demo
gunicorn breathe.wsgi:application

