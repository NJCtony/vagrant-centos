#!/bin/bash

inotifywait -m -e moved_to /srv/website/data/ | while read line
do
  python ../analytics/need_three.py
  python ../analytics/need_one.py
done
