install:
	source ../venv/bin/activate; \
  pip install -r requirements.txt; \
	python manage.py migrate; \
	echo "Running analytics scripts..."; \
	python ./analytics/demand_change.py; \
	python ./analytics/supply_change.py; \
	python ./analytics/order_discrepancy.py; \
	echo "Creating superuser vagrant..."; \
	bash create_super_user.sh; \
