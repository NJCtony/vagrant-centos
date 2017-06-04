#!/bin/bash

inotifywait -m -e moved_to /srv/website/data/ | while read line
do
  python ../analytics/demand_change.py
  python ../analytics/supply_change.py
  python ../analytics/order_discrepancy.py
done
