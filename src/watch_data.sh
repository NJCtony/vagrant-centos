#!/bin/bash

inotifywait -m -e moved_to --format '%f' /srv/website/data/ | while read file
do
  if [ $file = "Need1_K03.csv" ]; then
    echo "Running demand change algorithm..."
    python /srv/website/analytics/demand_change.py
    echo "Running supply change algorithm..."
    python /srv/website/analytics/supply_change.py
  elif [ $file = "Need3_K03.csv" ]; then
    echo "Running order discrepancy algorithm..."
    python /srv/website/analytics/order_discrepancy.py
  fi
done
