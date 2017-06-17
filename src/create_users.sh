#!/bin/bash

echo "from django.contrib.auth.models import User;
from dashboard.models import Profile;
User.objects.all().delete();
User.objects.create_superuser('admin', 'admin@example.com', 'password');
User.objects.create_superuser('K03', 'K03@example.com', 'password');
User.objects.create_superuser('Z02', 'Z02@example.com', 'password');
User.objects.create_superuser('Z04', 'Z04@example.com', 'password');
id = User.objects.get(username='admin').id
profile = Profile.objects.get(user_id=id);
profile.clm_code = 'Z02';
profile.save();
id = User.objects.get(username='K03').id
profile = Profile.objects.get(user_id=id);
profile.clm_code = 'K03';
profile.save();
id = User.objects.get(username='Z02').id
profile = Profile.objects.get(user_id=id);
profile.clm_code = 'Z02';
profile.save();
id = User.objects.get(username='Z04').id
profile = Profile.objects.get(user_id=id);
profile.clm_code = 'Z04';
profile.save();" | python /srv/website/manage.py shell
