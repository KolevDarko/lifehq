#!/bin/bash
NAME="LifeHQ"
DJANGODIR=/home/darko/django-commonplace/
SOCKFILE=/home/darko/django-commonplace/run/gunicorn.sock   # we will communicate using this unix socket
USER=darko                                      # The user to run as
GROUP=darko                                   # The group to run as
NUM_WORKERS=2                                   # How many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=mastermind.settings.production          # Which settings file should Django use
DJANGO_WSGI_MODULE=mastermind.wsgi                  # WSGI module name

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source /home/darko/.local/share/virtualenvs/django-commonplace-QuWyJPQA/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user $USER \
  --bind=unix:$SOCKFILE
