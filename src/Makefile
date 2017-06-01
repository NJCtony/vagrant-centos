install:
	source ../venv/bin/activate; \
  pip install -r requirements.txt; \
	python manage.py migrate; \
	python manage.py loaddata dashboard/fixtures/clm_soldto_pair.json; \
	python ./analytics/need_one.py; \
	python ./analytics/need_three.py; \
