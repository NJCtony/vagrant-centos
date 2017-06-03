#!/bin/bash

echo "from django.contrib.auth.models import User; User.objects.all().delete(); User.objects.create_superuser('vagrant', 'admin@example.com', 'password');
id = User.objects.get(username='vagrant').id
from dashboard.models import Profile;
profile = Profile.objects.get(user_id=id);
profile.clm_code = 'K03';
profile.save();" | python /srv/website/manage.py shell
