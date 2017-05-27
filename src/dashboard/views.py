from django.http import HttpResponse
from django.shortcuts import render
import operator

# Security
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect

# Models
from .models import NeedOneRecord

def index(request):
    context={}
    # if not request.user.is_authenticated:
    #     return redirect('dashboard:login')
    return render(request, 'dashboard/index.html', context)

def login(request):
    context = {}
    auth_logout(request)
    try:
        del request.session['userid']
    except KeyError:
        pass

    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            auth_login(request, user)
            request.session['userid'] = username
            return redirect('dashboard:index')
    return render(request, 'dashboard/login.html', context)


def need_one(request):
    num_decline_alerts = 2
    num_increase_alerts = 3
    decline_alert_count = 0
    increase_alert_count = 0

    records = NeedOneRecord.objects.all()
    alerts = []

    alerts_query = NeedOneRecord.objects.filter(alert_type="Need 1").order_by('diff_umwteuro')

    for alert in alerts_query:
        if alert.diff_umwteuro < 0 and decline_alert_count < num_decline_alerts:
            alerts.append(alert)
            decline_alert_count += 1

    alerts_query_sorted = sorted(alerts_query, key=operator.attrgetter('sc_diff_umwteuro_percent'), reverse=True)

    for alert in alerts_query_sorted:
        if alert.sc_diff_umwteuro_percent != 100 and increase_alert_count < num_increase_alerts:
            alerts.append(alert)
            increase_alert_count += 1

    for alert in alerts:
        alerts_query_sorted.remove(alert)

    for alert in alerts_query_sorted:
        alerts.append(alert)

    return render(request, 'dashboard/need-one.html', {
        'records': records,
        'alerts': alerts
    })
