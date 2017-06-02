from django.conf.urls import url

from . import views

app_name = 'dashboard' # namespacing to allow URL ReverseMatch
urlpatterns = [
    url(r'^$', views.overview, name='overview'),
    url(r'^login/', views.LoginView.as_view(), name='login'),
    url(r'^need-one/', views.need_one, name='needone'),

    url(r'^api/clm/(?P<clm_code>[A-Z0-9]+)', views.api_clm_summary, name='api_clm_summary'),
    url(r'^api/need-one/records', views.api_need_one_records, name='api_needone_records'),
    url(r'^api/need-one/alerts', views.api_need_one_alerts, name='api_needone_alerts'),
    url(r'^api/need-one/business_performance', views.api_need_one_businessPerformance, name='api_needone_businessPerformance'),

    url(r'^api/records/demand/', views.api_records_demand, name='api_records_demand'),
    url(r'^api/alerts/demand/', views.api_alerts_demand, name='api_alerts_demand'),
    url(r'^api/bp/demand/', views.api_bp_demand, name='api_bp_demand'),

    url(r'^demand-change/', views.demand_change, name='demand_change'),
]
