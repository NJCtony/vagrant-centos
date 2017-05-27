from django.db import models

# Create your models here.
class OrderDifference(models.Model):
    clm_code = models.CharField(max_length=16, default='')
    soldtoname = models.CharField(max_length=16, default='')
    salesname = models.CharField(max_length=16, default='')
    monat = models.CharField(max_length=16, default='')
    akt_day = models.DateField()
    last_umwteuro_amt = models.FloatField(default=0)
    this_umwteuro_amt = models.FloatField(default=0)
    diff_umwteuro = models.FloatField(default=0)
    last_umwtpcs_amt = models.IntegerField(default=0)
    this_umwtpcs_amt = models.IntegerField(default=0)
    diff_umwtpcs = models.IntegerField(default=0)
    diff_umwtpcs_percent = models.FloatField(default=0)
    sc_diff_umwteuro_percent = models.FloatField(default=0)
    alert_type = models.CharField(max_length=16, default='')
    alert_description = models.CharField(max_length=64, default='')
