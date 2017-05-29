from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
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

# JSON API Endpoints
def api_need_one_records(request):
    monat_list = [temp_dict['monat'] for temp_dict in NeedOneRecord.objects.values('monat').distinct()]
    soldtoname_available = [temp_dict['soldtoname'] for temp_dict in NeedOneRecord.objects.values('soldtoname').distinct()]
    #TODO: Narrow down soldtoname_list based on CLM's access

    summary = []
    for soldtoname_item in soldtoname_list:
        soldtoname_summary = {}
        sc_mean = [0.0,0.0,0.0]
        sc_count = [0,0,0]

        soldtoname_summary['soldtoname'] = soldtoname_item
        soldtoname_summary['salesname_sc'] = []
        salesname_list = [temp_dict['salesname'] for temp_dict in NeedOneRecord.objects.filter(soldtoname = soldtoname_item).values('salesname').distinct()]
        for salesname_item in salesname_list:
            salesname_sc = [] # set of structural-change-% for each sales-name
            for monat_item in monat_list:
                if NeedOneRecord.objects.filter(salesname=salesname_item, monat=monat_item).exists():
                    salesname_sc.append(NeedOneRecord.objects.filter(salesname=salesname_item, monat=monat_item) \
                    .values('sc_diff_umwteuro_percent')[0]['sc_diff_umwteuro_percent'])
                else:
                    salesname_sc.append(0.0)

            for i in range(len(salesname_sc)):
                if salesname_sc[i] != 0:
                    sc_mean[i] += salesname_sc[i]
                    sc_count[i] += 1

            soldtoname_summary['salesname_sc'].append({'salesname': salesname_item, 'sc': salesname_sc})
        for i in range(len(salesname_sc)):
            if sc_mean[i] > 0:
                sc_mean[i] /= sc_count[i]
            sc_mean[i] = round(sc_mean[i], 1)

        soldtoname_summary['mean'] = sc_mean
        summary.append(soldtoname_summary)

    return JsonResponse({'data' : {'summary': summary, 'label': monat_list}})

def api_need_one_alerts(request):
    alert_labels = ('Sales name', 'MONAT', 'Description')
    alert_fields = ('salesname','monat','alert_description', 'diff_umwteuro', 'sc_diff_umwteuro_percent') # Define field to be be shown

    soldtoname_available = [temp_dict['soldtoname'] for temp_dict in NeedOneRecord.objects.values('soldtoname').distinct()]
    soldtoname_choices = soldtoname_available

    consolidatedAlerts = []

    for soldtonameChoice in soldtoname_choices:
        if soldtonameChoice in soldtoname_available:

            records_filtered = NeedOneRecord.objects.filter(soldtoname = soldtonameChoice)

            num_decline_alerts = 2
            num_increase_alerts = 3
            decline_alert_count = 0
            increase_alert_count = 0

            alerts = []

            # values() limits the number of fields that is to be converted to list
            # alerts_query = NeedOneRecord.objects.filter(alert_type="Need 1").order_by('diff_umwteuro')
            alerts_query = records_filtered.values(*alert_fields).filter(alert_type="Need 1").order_by('diff_umwteuro')

            for alert in alerts_query:
                if alert['diff_umwteuro'] < 0 and decline_alert_count < num_decline_alerts:
                    alerts.append(alert)
                    decline_alert_count += 1

            alerts_query_sorted = sorted(alerts_query, key=lambda k: k['sc_diff_umwteuro_percent'], reverse=True)

            for alert in alerts_query_sorted:
                if alert['sc_diff_umwteuro_percent'] != 100 and increase_alert_count < num_increase_alerts:
                    alerts.append(alert)
                    increase_alert_count += 1

            for alert in alerts:
                alerts_query_sorted.remove(alert)

            for alert in alerts_query_sorted:
                alerts.append(alert)

        consolidatedAlerts.append({'soldtoname': soldtonameChoice, 'alerts': alerts})
    return JsonResponse({'data' : {'listing': consolidatedAlerts, 'labels' : alert_labels}})

def template_need_one(request):
    template = loader.get_template('dashboard/template_need1.html')
    return HttpResponse(template.render({}, request))
