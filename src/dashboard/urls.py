from django.conf.urls import url

from . import views

app_name = 'dashboard' # namespacing to allow URL ReverseMatch
urlpatterns = [
    url(r'^$', views.overview, name='overview'),
    url(r'^login/', views.LoginView.as_view(), name='login'),
    url(r'^need-one/', views.need_one, name='needone'),
    url(r'^demand-change/', views.demand_change, name='demand_change'),

    # API Endpoints
    url(r'^api/clm/(?P<clm_code>[A-Z0-9]+)', views.api_clm_summary, name='api_clm_summary'),
    url(r'^api/records/demand/chart', views.api_records_demand_chart, name='api_records_demand_chart'),
    url(r'^api/records/demand/', views.api_records_demand, name='api_records_demand'),
    url(r'^api/records/supply/chart', views.api_records_supply_chart, name='api_records_supply_chart'),
    url(r'^api/records/supply/', views.api_records_supply, name='api_records_supply'),
    url(r'^api/alerts/demand/', views.api_alerts_demand, name='api_alerts_demand'),
    url(r'^api/alerts/supply/', views.api_alerts_supply, name='api_alerts_supply'),
    url(r'^api/bp/demand/', views.api_bp_demand, name='api_bp_demand'),
    url(r'^api/bp/supply/', views.api_bp_supply, name='api_bp_supply'),
]
