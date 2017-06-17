from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.views.generic import View
from django.core import serializers
import operator, json, time

# Security
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Models
from .models import DemandChangeRecord, SupplyChangeRecord, OrderDiscrepancyRecord, BusinessPerformance, Profile


# Forms
from .forms import LoginForm, UploadFileForm

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
            profile = Profile.objects.get(id=user.id)
            request.session['id'] = profile.clm_code

            return redirect('dashboard:overview')

        return render(request, self.template_name, {
            'form': form,
            'error_message': 'The username and password provided do not match.'
        })

class DefaultView(View):
    query_params = []
    def request_with_params(self, request_get):
        for k, v in self.query_params:
            request_get.appendlist(k, v)
        return request_get

@method_decorator(login_required, name='dispatch')
class OverviewView(DefaultView):
    template_name = 'dashboard/overview.html'
    query_params = [['id',''], ['limit','3'], ['aggregate','true']]

    def get(self, request):
        self.query_params[0][1] = request.session.get('id')

        # Load params into get request
        request.GET = request.GET.copy() # Make DjangoDict mutable
        request.GET = self.request_with_params(request.GET)

        # Summary API
        clm_summary_json = api_clm_summary(request, self.query_params[0][1]).content.decode('utf-8')
        clm_summary_model = json.loads(clm_summary_json)

        # Alerts API
        alerts_demand_json = api_alerts_demand(request).content.decode('utf-8')
        alerts_demand_model = json.loads(alerts_demand_json)
        alerts_supply_json = api_alerts_supply(request).content.decode('utf-8')
        alerts_supply_model = json.loads(alerts_supply_json)
        alerts_order_json = api_alerts_order(request).content.decode('utf-8')
        alerts_order_model = json.loads(alerts_order_json)

        bp_demand_json = api_bp_demand(request).content.decode('utf-8')
        bp_demand_model = json.loads(bp_demand_json)['data']
        bp_supply_json = api_bp_supply(request).content.decode('utf-8')
        bp_supply_model = json.loads(bp_supply_json)['data']
        bp_models = zip(bp_demand_model, bp_supply_model)

        context = {'clm_summary': clm_summary_model, 'bp_models': bp_models, \
        'alerts_demand': alerts_demand_model, 'alerts_supply': alerts_supply_model, 'alerts_order': alerts_order_model}
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
class DemandView(View):
    template_name = 'dashboard/demand_change.html'
    def get(self, request):
        # Params to get summary info
        query_id = request.GET['id'].upper()
        query_soldtoindex = request.GET['soldtoindex']

        # Summary API
        clm_summary_json = api_clm_summary(request, query_id).content.decode('utf-8')
        clm_summary_model = json.loads(clm_summary_json)

        records_demand_json = api_records_demand(request).content.decode('utf-8')
        alerts_demand_json = api_alerts_demand(request).content.decode('utf-8')
        alerts_demand_models = json.loads(alerts_demand_json)
        bp_demand_json = api_bp_demand(request).content.decode('utf-8')

        alerts_length_model = {'demand_increase': len(alerts_demand_models['data'][0]['alerts']['increase']), \
        'demand_decrease': len(alerts_demand_models['data'][0]['alerts']['decrease'])}

        context = {'clm_summary': clm_summary_model, 'records_demand': records_demand_json, 'alerts_demand': alerts_demand_models, 'bp_demand': bp_demand_json, 'alert_length': alerts_length_model, 'zoom_chart': False}
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
class SupplyView(View):
    template_name = 'dashboard/supply_change.html'

    def get(self, request):
        # Params to get summary info
        query_id = request.GET['id'].upper()

        # Summary API
        clm_summary_json = api_clm_summary(request, query_id).content.decode('utf-8')
        clm_summary_model = json.loads(clm_summary_json)

        records_supply_json = api_records_supply(request).content.decode('utf-8')
        alerts_supply_json = api_alerts_supply(request).content.decode('utf-8')
        alerts_supply_models = json.loads(alerts_supply_json)
        bp_supply_json = api_bp_supply(request).content.decode('utf-8')

        context = {'clm_summary': clm_summary_model, 'records_supply': records_supply_json, 'alerts_supply': alerts_supply_models, 'bp_supply': bp_supply_json, 'zoom_chart': True}
        return render(request, self.template_name, context)


## JSON API Endpoints
def api_clm_summary(request, clm_code=None): # For a specific CLM
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

            if alert_type == 'demand':
                sc_mean_up = [0.0, 0.0, 0.0]
                sc_mean_down = [0.0, 0.0, 0.0]
                sc_count_up = [0, 0, 0]
                sc_count_down = [0, 0, 0]
                soldtoname_data['soldtoname'] = soldtoname_choice
                monat_list = [temp_dict['monat'] for temp_dict in DemandChangeRecord.objects.values('monat').distinct()]
                soldtoname_data['labels'] = monat_list
                soldtoname_data['salesnames'] = []
                salesname_list = [temp_dict['salesname'] for temp_dict in DemandChangeRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice).values('salesname').distinct()]
                for salesname_item in salesname_list: # iterate ea salesname

                    salesname_sc = [] # set of structural-change-% for each sales-name
                    salesname_alert = []
                    salesname_this_umwteuro_amt = []
                    salesname_last_umwteuro_amt = []

                    for monat_item in monat_list:
                        if DemandChangeRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice, salesname=salesname_item, monat=monat_item).values('sc_diff_umwteuro_percent', 'alert_flag').exists():
                            record_query = DemandChangeRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice,salesname=salesname_item, monat=monat_item).values('sc_diff_umwteuro_percent', 'alert_flag', 'this_umwteuro_amt', 'last_umwteuro_amt')

                            salesname_sc.append(record_query[0]['sc_diff_umwteuro_percent'])
                            salesname_alert.append(record_query[0]['alert_flag'])
                            salesname_this_umwteuro_amt.append(record_query[0]['this_umwteuro_amt'])
                            salesname_last_umwteuro_amt.append(record_query[0]['last_umwteuro_amt'])
                            # if len(DemandChangeRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice,salesname=salesname_item, monat=monat_item) \
                            # .values('sc_diff_umwteuro_percent')) > 1:
                            #     print("Error(api_records_demand) : Multiple entries for", salesname_item, monat_item)
                        else:
                            salesname_sc.append(100.0) # fix: fill up missing values
                            salesname_alert.append(False)
                            # print('(WARNING) api_records_{}>: Filled missing value for {} {}'.format(alert_type, salesname_item, monat_item))

                    for i in range(len(salesname_sc)):
                        if salesname_sc[i] > 100:
                            sc_mean_up[i] += salesname_sc[i]
                            sc_count_up[i] += 1
                        elif salesname_sc[i] < 100:
                            sc_mean_down[i] += salesname_sc[i]
                            sc_count_down[i] += 1

                    soldtoname_data['salesnames'].append({'salesname': salesname_item, 'sc': salesname_sc, 'alert_flag': salesname_alert, 'this_umwteuro_amt': salesname_this_umwteuro_amt, 'last_umwteuro_amt':salesname_last_umwteuro_amt})

                for i in range(len(sc_mean_up)):
                    if sc_count_up[i] == 0 :
                        sc_mean_up[i] = 100
                    else :
                        sc_mean_up[i] /= sc_count_up[i]
                    sc_mean_up[i] = round(sc_mean_up[i], 1)

                for i in range(len(sc_mean_down)):
                    if sc_count_down[i] == 0 :
                        sc_mean_down[i] = 100
                    else :
                        sc_mean_down[i] /= sc_count_down[i]
                    sc_mean_down[i] = round(sc_mean_down[i], 1)

                soldtoname_data['means'] = sc_mean_up
                soldtoname_data['means2'] = sc_mean_down

            elif alert_type == 'supply':
                sc_mean = [0.0, 0.0, 0.0]
                sc_count = [0, 0, 0]
                sc_min = 100
                soldtoname_data['soldtoname'] = soldtoname_choice
                monat_list = [temp_dict['monat'] for temp_dict in SupplyChangeRecord.objects.values('monat').distinct()]
                soldtoname_data['labels'] = monat_list
                soldtoname_data['salesnames'] = []
                salesname_list = [temp_dict['salesname'] for temp_dict in SupplyChangeRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice).values('salesname').distinct()]
                for salesname_item in salesname_list: # iterate ea salesname

                    salesname_sc = [] # set of structural-change-% for each sales-name
                    salesname_alert = []
                    for monat_item in monat_list:
                        if SupplyChangeRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice, salesname=salesname_item, monat=monat_item).values('sc_diff_umatpcs_percentage', 'alert_flag').exists():
                            record_query = SupplyChangeRecord.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice,salesname=salesname_item, monat=monat_item) \
                            .values('sc_diff_umatpcs_percentage', 'alert_flag')

                            salesname_sc.append(record_query[0]['sc_diff_umatpcs_percentage'])
                            salesname_alert.append(record_query[0]['alert_flag'])
                        else:
                            salesname_sc.append(100) # fix: fill up missing values
                            print('(WARNING) api_records_{}>: Filled missing value for {} {}'.format(alert_type, salesname_item, monat_item))

                    for i in range(len(salesname_sc)):
                        sc_mean[i] += salesname_sc[i]
                        sc_count[i] += 1

                        if salesname_sc[i] < sc_min:
                            sc_min = salesname_sc[i]

                    soldtoname_data['salesnames'].append({'salesname': salesname_item, 'sc': salesname_sc, 'alert_flag': salesname_alert})

                for i in range(len(sc_mean)):
                    if sc_count[i] == 0 :
                        sc_mean[i] = 100
                    else :
                        sc_mean[i] /= sc_count[i]
                    sc_mean[i] = round(sc_mean[i], 1)

                soldtoname_data['means'] = sc_mean
                soldtoname_data['min'] = sc_min

            if query_image and oneEntry:
                soldtoname_data['image'] = True
                soldtoname_data['salesnames'] = []

            else:
                soldtoname_data['image'] = False

            data.append(soldtoname_data)

            if oneEntry:
                break
        time_end = time.time() - time_now
        print('Time taken <api_records_{}>: {}'.format(alert_type ,time_end))
    # return HttpResponse(soldtoname_available)
    return JsonResponse({'data' : data})

def api_records_demand_chart(request):
    records_demand_json = api_records_demand(request).content.decode('utf-8')

    # Redirect link from Overview page to Detailed page
    query_id = request.GET.get('id')
    query_soldtoindex = request.GET.get('soldtoindex')
    redirect_link = get_redirect_link(query_id, query_soldtoindex, 'demand')

    context = {'records_demand': records_demand_json, 'redirect_link':redirect_link}
    return render(request, 'dashboard/chart_demand.html', context)

def api_records_supply_chart(request):
    records_supply_json = api_records_supply(request).content.decode('utf-8')

    # Redirect link from Overview page to Detailed page
    query_id = request.GET.get('id')
    query_soldtoindex = request.GET.get('soldtoindex')
    redirect_link = get_redirect_link(query_id, query_soldtoindex, 'supply')

    context = {'records_supply': records_supply_json,  'redirect_link':redirect_link}
    return render(request, 'dashboard/chart_supply.html', context)

def get_redirect_link(query_id, query_soldtoindex, alert_type):
    # Redirect link from Overview page to Detailed page
    if alert_type == 'demand':
        base_url = reverse('dashboard:demand_change')
    elif alert_type == 'supply':
        base_url = reverse('dashboard:supply_change')
    else:
        return ""
    redirect_link = "{}?id={}&soldtoindex={}".format(base_url, query_id, query_soldtoindex)
    return redirect_link
def get_chart_link(query_id, query_soldtoindex, alert_type):
    # Link to chart to embed into iframe
    if alert_type == 'demand':
        base_url = reverse('dashboard:api_records_demand_chart')
    elif alert_type == 'supply':
        base_url = reverse('dashboard:api_records_supply_chart')
    else:
        return ""
    chart_link = "{}?id={}&soldtoindex={}&image=1".format(base_url, query_id, query_soldtoindex)
    return chart_link

def api_alerts_demand(request):
    return api_alerts(request, 'demand')
def api_alerts_supply(request):
    return api_alerts(request, 'supply')
def api_alerts_order(request):
    return api_alerts(request, 'order')

def api_alerts(request, alert_type):
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

            if alert_type == 'demand':
                demand_values = ('soldtoname', 'salesname', 'monat', 'diff_umwteuro', 'sc_diff_umwteuro_percent', 'diff_umwteuro') # Define field to be be shown

                if query_aggregate and not oneSoldtoname:
                    alerts_query = DemandChangeRecord.objects.filter(alert_flag=1).values(*demand_values)
                else:
                    alerts_query = DemandChangeRecord.objects.filter(soldtoname = soldtoname_choice, alert_flag=1).values(*demand_values)

                alerts_increase = alerts_query.filter(sc_diff_umwteuro_percent__gt = 110, sc_diff_umwteuro_percent__lt = 200).order_by('sc_diff_umwteuro_percent').reverse()
                alerts_decrease = alerts_query.filter(diff_umwteuro__lt = -50000).order_by('diff_umwteuro')
                if query_limit:
                    alerts_increase = alerts_increase[:query_limit]
                    alerts_decrease = alerts_decrease[:query_limit]
                soldtoname_data['alerts'] = {'increase': list(alerts_increase), 'decrease': list(alerts_decrease)}

            elif alert_type == 'supply':
                supply_values = ('soldtoname', 'salesname', 'alert_percentage', 'this_umatpcs_3WPeriod', 'last_umatpcs_3WPeriod') # Define field to be be shown

                if query_aggregate and not oneSoldtoname:
                    alerts_query = SupplyChangeRecord.objects.filter(alert_flag=1).values(*supply_values)
                else:
                    alerts_query = SupplyChangeRecord.objects.filter(soldtoname = soldtoname_choice, alert_flag=1).values(*supply_values)

                alerts = alerts_query.order_by('alert_percentage')
                if query_limit:
                    alerts = alerts[:query_limit]
                soldtoname_data['alerts'] = list(alerts)

            elif alert_type == 'order':
                order_values = ('soldtoname', 'salesname', 'monat', 'wtpcs_amt', 'num_sd_diff') # Define field to be be shown

                if query_aggregate and not oneSoldtoname:
                    alerts_query = OrderDiscrepancyRecord.objects.filter(alert_flag=1).values(*order_values)
                else:
                    alerts_query = OrderDiscrepancyRecord.objects.filter(soldtoname = soldtoname_choice, alert_flag=1).values(*order_values)

                alerts = alerts_query.order_by('abs_num_sd_diff').reverse()
                if query_limit:
                    alerts = alerts[:query_limit]

                for alert in alerts:
                    if alert['num_sd_diff'] >= 0:
                        alert['color'] = 'green'
                        alert['direction'] = 'up'
                    else:
                        alert['color'] = 'red'
                        alert['direction'] = 'down'

                soldtoname_data['alerts'] = list(alerts)

            data.append(soldtoname_data)

            if oneSoldtoname or query_aggregate:
                break
        time_end = time.time() - time_now
        print('Time taken <api_alerts_{}>: {}'.format(alert_type ,time_end))
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

        for soldtoindex_choice in range(len(soldtoname_list)): # iterate ea soldtoname
            soldtoname_choice = soldtoname_list[soldtoindex_choice]
            oneSoldtoname = False
            # Validate and verify soldtoindex
            if isInt(query_soldtoindex):
                query_soldtoindex = int(query_soldtoindex)
                print('SOLDTOINDEX', query_soldtoindex)
                if query_soldtoindex < len(soldtoname_list):
                    soldtoname_choice = soldtoname_list[query_soldtoindex]
                    oneSoldtoname = True

            soldtoname_data = {} # Each soldtoname is an entry into data
            soldtoname_data['soldtoname'] = soldtoname_choice
            soldtoname_data['redirect_link'] = get_redirect_link(query_id, soldtoindex_choice, alert_type)
            soldtoname_data['chart_link'] = get_chart_link(query_id, soldtoindex_choice, alert_type)

            bp_query = BusinessPerformance.objects.filter(clm_code=query_id, soldtoname=soldtoname_choice).values('bp_{}'.format(alert_type))

            if len(bp_query) == 1:
                soldtoname_data['bp'] = bp_query.get()['bp_{}'.format(alert_type)]
            else:
                print("api_bp: Missing BP")

            data.append(soldtoname_data)

            if oneSoldtoname:
                break
        time_end = time.time() - time_now
        print('Time taken <api_bp_{}>: {}'.format(alert_type ,time_end))
    return JsonResponse({'data' : data})

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.POST['title'], request.FILES['file'])
            return redirect('dashboard:overview')
    else:
        form = UploadFileForm()
    return render(request, 'dashboard/upload.html', {'form': form})

def handle_uploaded_file(title, f):
    with open('uploads/{}'.format(title), 'ab') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

## Helper Functions
def isInt(value):
    try:
        value = int(value)
        return True
    except:
        return False
