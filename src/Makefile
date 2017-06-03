install:
	source ../venv/bin/activate; \
  pip install -r requirements.txt; \
	python manage.py migrate; \
	python ./analytics/need_one.py; \
	python ./analytics/need_two.py; \
	python ./analytics/need_three.py; \
	echo "Creating superuser vagrant..."; \
	bash create_super_user.sh; \
