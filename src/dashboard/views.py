from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.views import generic
from django.views.generic import View
import operator, json, time

# Security
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

# Models
from .models import NeedOneRecord, BusinessPerformance, Profile, ClmSoldtoPair


# Forms
from .forms import LoginForm

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
            return redirect('dashboard:overview')
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
    pair_query = ClmSoldtoPair.objects.filter(clm_code=clm_code).order_by('soldtoname')
    for pair in pair_query:
        soldtonames.append(pair.soldtoname)

    return JsonResponse({'data' : {'clm_code': clm_code, 'settings': settings, 'soldtonames': soldtonames}})

def api_need_one_records(request):
    monat_list = [temp_dict['monat'] for temp_dict in NeedOneRecord.objects.values('monat').distinct()]
    soldtoname_available = [temp_dict['soldtoname'] for temp_dict in NeedOneRecord.objects.values('soldtoname').distinct()]
    soldtoname_choices = soldtoname_available

    summary = []
    for soldtoname_choice in soldtoname_choices:
        if soldtoname_choice in soldtoname_available:
            soldtoname_summary = {}
            sc_mean = [0.0,0.0,0.0]
            sc_count = [0,0,0]

            soldtoname_summary['soldtoname'] = soldtoname_choice
            soldtoname_summary['salesname_sc'] = []
            salesname_list = [temp_dict['salesname'] for temp_dict in NeedOneRecord.objects.filter(soldtoname = soldtoname_choice).values('salesname').distinct()]
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

def api_need_one_businessPerformance(request):
    bp_fields = ('bp',)

    # TODO: Soldtoname available should be restricted to CLM's access
    soldtoname_available = [temp_dict['soldtoname'] for temp_dict in BusinessPerformance.objects.values('soldtoname').distinct()]
    soldtoname_choices = soldtoname_available

    consolidatedBP = []

    for soldtonameChoice in soldtoname_choices:
        if soldtonameChoice in soldtoname_available:
            bp_entry = {}

            bp_filtered = BusinessPerformance.objects.filter(alert_type="Need 1", soldtoname = soldtonameChoice)
            bp_query = bp_filtered.values(*bp_fields)

            bp_entry['soldtoname'] = soldtonameChoice
            if bp_query.exists():
                bp_entry['bp'] = bp_query[0]['bp']
                if len(bp_query[0]) > 0:
                    print ("ERROR: api_need_one_businessPerformance")
            consolidatedBP.append(bp_entry)
    return JsonResponse({'data' : {'listing': consolidatedBP}})

def api_records_demand(request):
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
            oneEntry = False
            # Validate and verify soldtoindex
            if isInt(query_soldtoindex):
                query_soldtoindex = int(query_soldtoindex)
                print(query_soldtoindex)
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
                    if NeedOneRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice, salesname=salesname_item, monat=monat_item).values('sc_diff_umwteuro_percent').exists():
                        salesname_sc.append(NeedOneRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice,salesname=salesname_item, monat=monat_item) \
                        .values('sc_diff_umwteuro_percent')[0]['sc_diff_umwteuro_percent'])
                        # if len(NeedOneRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice,salesname=salesname_item, monat=monat_item) \
                        # .values('sc_diff_umwteuro_percent')) > 1:
                        #     print("Error(api_records_demand) : Multiple entries for", salesname_item, monat_item)
                    else:
                        salesname_sc.append(0.0) # fix: fill up missing values

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
            data.append(soldtoname_data)

            if oneEntry:
                break
        time_end = time.time() - time_now
        print('Time taken <api_records_demand>:', time_end)
    # return HttpResponse(soldtoname_available)
    return JsonResponse({'data' : data})

def api_alerts_demand(request):
    alert_fields = ('salesname','monat','alert_description', 'diff_umwteuro', 'sc_diff_umwteuro_percent') # Define field to be be shown

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

            num_decline_alerts = 2
            num_increase_alerts = 3
            decline_alert_count = 0
            increase_alert_count = 0

            soldtoname_data = {} # Each soldtoname is an entry into data
            soldtoname_data['soldtoname'] = soldtoname_choice

            alerts_query = NeedOneRecord.objects.filter(soldtoname = soldtoname_choice, alert_type="Need 1").values(*alert_fields)
            alerts_increase = alerts_query.filter(sc_diff_umwteuro_percent__gt = 0, sc_diff_umwteuro_percent__lt = 100).order_by('sc_diff_umwteuro_percent').reverse()
            alerts_decrease = alerts_query.filter(diff_umwteuro__lt = 0).order_by('diff_umwteuro')

            soldtoname_data['alerts'] = {'increase': list(alerts_increase), 'decrease': list(alerts_decrease)}
            data.append(soldtoname_data)

            if oneSoldtoname:
                break
        time_end = time.time() - time_now
        print('Time taken <api_alerts_demand>:', time_end)
    return JsonResponse({'data' : data})

def api_bp_demand(request):
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

            bp_query = BusinessPerformance.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice, alert_type="Need 1").values('bp')
            if len(bp_query) == 1:
                soldtoname_data['bp'] = bp_query.get()['bp']
            else:
                print("api_bp_demand: Missing BP")

            data.append(soldtoname_data)

            if oneSoldtoname:
                break
        time_end = time.time() - time_now
        print('Time taken <api_bp_demand>:', time_end)
    return JsonResponse({'data' : data})



def isInt(value):
    try:
        value = int(value)
        return True
    except:
        return False

def demand_change(request):
    template = loader.get_template('dashboard/demand_change.html')
    return HttpResponse(template.render({}, request))

@login_required
def overview(request):
    template = loader.get_template('dashboard/overview.html')
    return HttpResponse(template.render({}, request))
