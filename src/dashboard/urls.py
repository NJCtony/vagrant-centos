from django.conf.urls import url

from . import views

app_name = 'dashboard' # namespacing to allow URL ReverseMatch
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/', views.login, name='login'),
    url(r'^need-one/', views.need_one, name='needone'),
]
