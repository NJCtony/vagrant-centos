from django.conf.urls import url

from . import views

app_name = 'dashboard' # namespacing to allow URL ReverseMatch
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/', views.login, name='login'),
    url(r'^need-one/', views.need_one, name='needone'),

    url(r'^api/clm/', views.api_clm_summary, name='api_clm_summary'),
    url(r'^api/need-one/records', views.api_need_one_records, name='api_needone_records'),
    url(r'^api/need-one/alerts', views.api_need_one_alerts, name='api_needone_alerts'),
    url(r'^api/need-one/business_performance', views.api_need_one_businessPerformance, name='api_needone_businessPerformance'),
    url(r'^demand-change/', views.demand_change, name='demand_change'),
]
