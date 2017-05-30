install:
	source ../venv/bin/activate; \
  pip install -r requirements.txt; \
	python manage.py migrate; \
	python ./analytics/need_one.py; \
	python ./analytics/need_three.py; \
