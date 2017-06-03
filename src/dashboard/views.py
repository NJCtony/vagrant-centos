from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.views import generic
from django.views.generic import View
from django.core import serializers
import operator, json, time

# Security
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

# Models
from .models import NeedOneRecord, BusinessPerformance, Profile


# Forms
from .forms import LoginForm

## Endpoints
class LoginView(View):
    form_class = LoginForm
    template_name = 'dashboard/login.html'

    # display blank form
    def get(self, request):
        form = self.form_class(None)
        auth_logout(request)
        try:
            del request.session['userid']
        except KeyError:
            pass
        return render(request, self.template_name, {'form': form})

    # process form data
    def post(self, request):
        form = self.form_class(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        # returns User object if credentials are correct
        user = authenticate(username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard:overview')

        return render(request, self.template_name, {
            'form': form,
            'error_message': 'The username and password provided do not match.'
        })

@login_required
def overview(request):
    # template = loader.get_template('dashboard/overview.html')
    query_id = 'k03'
    query_limit = '3'
    query_aggregate = '1'

    request.GET = request.GET.copy() # Make DjangoDict mutable

    # Params to get summary info
    request.GET.appendlist('id', query_id.upper())
    # Summary API
    clm_summary_json = api_clm_summary(request, query_id).content.decode('utf-8')
    clm_summary_model = json.loads(clm_summary_json)

    # Params for to limit and aggregate Alerts
    request.GET.appendlist('limit', query_limit)
    request.GET.appendlist('aggregate', query_aggregate)
    # Alerts API
    alerts_demand_json = api_alerts_demand(request).content.decode('utf-8')
    alerts_demand_model = json.loads(alerts_demand_json)

    # TODO: Tuple the BPs by company level
    bp_demand_json = api_bp_demand(request).content.decode('utf-8')
    bp_demand_model = json.loads(bp_demand_json)['data']
    bp_supply_json = api_bp_supply(request).content.decode('utf-8')
    bp_supply_model = json.loads(bp_supply_json)['data']
    bp_models = zip(bp_demand_model, bp_supply_model)

    context = {'clm_summary': clm_summary_model, 'bp_models': bp_models, 'alerts_demand': alerts_demand_model}
    return render(request, 'dashboard/overview.html', context)

def demand_change(request):
    # template = loader.get_template('dashboard/demand_change.html')

    records_demand_json = api_records_demand(request).content.decode('utf-8')
    alerts_demand_json = api_alerts_demand(request).content.decode('utf-8')
    alerts_demand_models = json.loads(alerts_demand_json)
    bp_demand_json = api_bp_demand(request).content.decode('utf-8')

    context = {'records_demand': records_demand_json, 'alerts_demand': alerts_demand_models, 'bp_demand': bp_demand_json}
    return render(request, 'dashboard/demand_change.html', context)

def need_one(request):
    num_decline_alerts = 2
    num_increase_alerts = 3
    decline_alert_count = 0
    increase_alert_count = 0

    records = NeedOneRecord.objects.all()
    alerts = []

    alerts_query = NeedOneRecord.objects.filter(alert_flag="1").order_by('diff_umwteuro')

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

## JSON API Endpoints
def api_clm_summary(request, clm_code): # For a specific CLM

    settings = {}
    try:
        profile = Profile.objects.get(clm_code=clm_code)
        settings['demand_up_threshold'] = profile.demand_up_threshold
        settings['demand_down_threshold'] = profile.demand_down_threshold
        settings['supply_down_threshold'] = profile.supply_down_threshold
    except:
        pass

    soldtonames = []
    pair_query = BusinessPerformance.objects.filter(clm_code=clm_code).order_by('soldtoname')
    for pair in pair_query:
        soldtonames.append(pair.soldtoname)

    return JsonResponse({'data' : {'clm_code': clm_code, 'settings': settings, 'soldtonames': soldtonames}})

def api_records_demand(request):
    return api_records(request, 'demand')
def api_records_supply(request):
    return api_records(request, 'supply')

def api_records(request, alert_type):
    query_id = request.GET.get('id')
    query_soldtoindex = request.GET.get('soldtoindex')
    query_image = request.GET.get('image')

    data = []
    if query_id:
        time_now = time.time()
        #TODO: Check validity of query_id
        clm_summary_json = api_clm_summary(request, query_id).content.decode('utf-8')
        clm_summary_dict = json.loads(clm_summary_json)
        soldtoname_list = clm_summary_dict['data']['soldtonames']

        for soldtoname_choice in soldtoname_list: # iterate ea soldtoname
            oneEntry = False
            # Validate and verify soldtoindex
            if isInt(query_soldtoindex):
                query_soldtoindex = int(query_soldtoindex)
                if query_soldtoindex < len(soldtoname_list):
                    soldtoname_choice = soldtoname_list[query_soldtoindex]
                    oneEntry = True

            # Each soldtoname is an entry into data
            soldtoname_data = {}
            sc_mean = [0.0, 0.0, 0.0]
            sc_count = [0, 0, 0]

            soldtoname_data['soldtoname'] = soldtoname_choice
            monat_list = [temp_dict['monat'] for temp_dict in NeedOneRecord.objects.values('monat').distinct()]
            soldtoname_data['labels'] = monat_list
            soldtoname_data['salesnames'] = []
            salesname_list = [temp_dict['salesname'] for temp_dict in NeedOneRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice).values('salesname').distinct()]
            for salesname_item in salesname_list: # iterate ea salesname

                salesname_sc = [] # set of structural-change-% for each sales-name
                for monat_item in monat_list:
                    if alert_type == 'demand':
                        if NeedOneRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice, salesname=salesname_item, monat=monat_item).values('sc_diff_umwteuro_percent').exists():
                            salesname_sc.append(NeedOneRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice,salesname=salesname_item, monat=monat_item) \
                            .values('sc_diff_umwteuro_percent')[0]['sc_diff_umwteuro_percent'])
                            # if len(NeedOneRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice,salesname=salesname_item, monat=monat_item) \
                            # .values('sc_diff_umwteuro_percent')) > 1:
                            #     print("Error(api_records_demand) : Multiple entries for", salesname_item, monat_item)
                        else:
                            salesname_sc.append(0.0) # fix: fill up missing values
                    elif alert_type == 'supply':
                        salesname_sc.append(50.0)

                for i in range(len(salesname_sc)):
                    if salesname_sc[i] != 0:
                        sc_mean[i] += salesname_sc[i]
                        sc_count[i] += 1

                soldtoname_data['salesnames'].append({'salesname': salesname_item, 'sc': salesname_sc})

            for i in range(len(sc_mean)):
                if sc_mean[i] > 0:
                    sc_mean[i] /= sc_count[i]
                sc_mean[i] = round(sc_mean[i], 1)

            soldtoname_data['means'] = sc_mean

            if query_image and oneEntry:
                soldtoname_data['image'] = True
                soldtoname_data['salesnames'] = []

            else:
                soldtoname_data['image'] = False

            data.append(soldtoname_data)

            if oneEntry:
                break
        time_end = time.time() - time_now
        print(alert_type, '- Time taken <api_records>:', time_end)
    # return HttpResponse(soldtoname_available)
    return JsonResponse({'data' : data})

def api_records_demand_chart(request):
    records_demand_json = api_records_demand(request).content.decode('utf-8')
    context = {'records_demand': records_demand_json}
    return render(request, 'dashboard/demand_change_chart.html', context)

def api_alerts_demand(request):
    return api_alerts(request, 'demand')
def api_alerts_supply(request):
    return api_alerts(request, 'supply')

def api_alerts(request, alert_type):
    demand_values = ('soldtoname', 'salesname', 'monat', 'diff_umwteuro', 'sc_diff_umwteuro_percent', 'diff_umwtpcs_percent') # Define field to be be shown

    query_id = request.GET.get('id')
    query_soldtoindex = request.GET.get('soldtoindex')
    query_limit = request.GET.get('limit')
    query_aggregate = request.GET.get('aggregate')

    data = []
    if query_id:
        time_now = time.time()

        #TODO: Check validity of query_id
        clm_summary_json = api_clm_summary(request, query_id).content.decode('utf-8')
        clm_summary_dict = json.loads(clm_summary_json)
        soldtoname_list = clm_summary_dict['data']['soldtonames']

        for soldtoname_choice in soldtoname_list: # iterate ea soldtoname
            oneSoldtoname = False

            # Validate and verify soldtoindex
            if isInt(query_soldtoindex):
                query_soldtoindex = int(query_soldtoindex)
                if query_soldtoindex < len(soldtoname_list) and query_soldtoindex >= 0:
                    soldtoname_choice = soldtoname_list[query_soldtoindex]
                    oneSoldtoname = True
                else:
                    print("api_alerts: Invalid soldtoindex")
                    break

            # Validate and verify query_limit
            if isInt(query_limit):
                query_limit = int(query_limit)
                if query_limit < 0:
                    print("api_alerts: Invalid query_limit")
                    break

            soldtoname_data = {} # Each soldtoname is an entry into data

            if query_aggregate and not oneSoldtoname:
                alerts_query = NeedOneRecord.objects.filter(alert_flag=1).values(*demand_values)
            else:
                alerts_query = NeedOneRecord.objects.filter(soldtoname = soldtoname_choice, alert_flag=1).values(*demand_values)

            if alert_type == 'demand':
                alerts_increase = alerts_query.filter(sc_diff_umwteuro_percent__gt = 0, sc_diff_umwteuro_percent__lt = 100).order_by('sc_diff_umwteuro_percent').reverse()
                alerts_decrease = alerts_query.filter(diff_umwteuro__lt = 0).order_by('diff_umwteuro')
                if query_limit:
                    alerts_increase = alerts_increase[:query_limit]
                    alerts_decrease = alerts_decrease[:query_limit]
                soldtoname_data['alerts'] = {'increase': list(alerts_increase), 'decrease': list(alerts_decrease)}

            elif alert_type == 'supply':
            #     alerts = alerts_query.filter(diff_umwtpcs_percent__lt = 0).order_by('diff_umwtpcs_percent')
            #     soldtoname_data['alerts'] = list(alerts)
                soldtoname_data['alerts'] = "Nothing yet"

            data.append(soldtoname_data)

            if oneSoldtoname or query_aggregate:
                break
        time_end = time.time() - time_now
        print(alert_type, '- Time taken <api_alerts>:', time_end)
    return JsonResponse({'data' : data})


def api_bp_demand(request):
    return api_bp(request, 'demand')
def api_bp_supply(request):
    return api_bp(request, 'supply')

def api_bp(request, alert_type):
    query_id = request.GET.get('id')
    query_soldtoindex = request.GET.get('soldtoindex')

    data = []
    if query_id:
        time_now = time.time()

        #TODO: Check validity of query_id
        clm_summary_json = api_clm_summary(request, query_id).content.decode('utf-8')
        clm_summary_dict = json.loads(clm_summary_json)
        soldtoname_list = clm_summary_dict['data']['soldtonames']

        for soldtoname_choice in soldtoname_list: # iterate ea soldtoname
            oneSoldtoname = False
            # Validate and verify soldtoindex
            if isInt(query_soldtoindex):
                query_soldtoindex = int(query_soldtoindex)
                print(query_soldtoindex)
                if query_soldtoindex < len(soldtoname_list):
                    soldtoname_choice = soldtoname_list[query_soldtoindex]
                    oneSoldtoname = True

            soldtoname_data = {} # Each soldtoname is an entry into data
            soldtoname_data['soldtoname'] = soldtoname_choice

            bp_query = BusinessPerformance.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice).values('bp_{}'.format(alert_type))

            if len(bp_query) == 1:
                soldtoname_data['bp'] = bp_query.get()['bp_{}'.format(alert_type)]
            else:
                print("api_bp: Missing BP")

            data.append(soldtoname_data)

            if oneSoldtoname:
                break
        time_end = time.time() - time_now
        print(alert_type, '- Time taken <api_bp>:', time_end)
    return JsonResponse({'data' : data})

## Helper Functions
def isInt(value):
    try:
        value = int(value)
        return True
    except:
        return False
