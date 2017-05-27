from django.db import models

# Create your models here.
class OrderDifference(models.Model):
    clm_code = models.CharField(max_length=16, default=None)
    soldtoname = models.CharField(max_length=64, default=None)
    salesname = models.CharField(max_length=32, default=None)
    monat = models.CharField(max_length=16, default=None)
    akt_day = models.DateField()
    last_umwteuro_amt = models.FloatField(default=0)
    this_umwteuro_amt = models.FloatField(default=0)
    diff_umwteuro = models.FloatField(default=0)
    last_umwtpcs_amt = models.IntegerField(default=0)
    this_umwtpcs_amt = models.IntegerField(default=0)
    diff_umwtpcs = models.IntegerField(default=0)
    diff_umwtpcs_percent = models.FloatField(default=0)
    sc_diff_umwteuro_percent = models.FloatField(default=0)
    alert_type = models.CharField(max_length=16, default=None)
    alert_description = models.CharField(max_length=64, default=None)

class BusinessPerformance(models.Model):
    clm_code = models.CharField(max_length=16, default=None)
    soldtoname = models.CharField(max_length=64, default=None)
    bp = models.FloatField(default=0)
    monat = models.CharField(max_length=32, default=None)
