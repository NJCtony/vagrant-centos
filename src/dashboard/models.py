from django.db import models

# Create your models here.
class OrderSnapshot(models.Model):
    clm_code = models.CharField(max_length=16, default='')
    sold_to_name = models.CharField(max_length=16, default='')
    sales_name = models.CharField(max_length=16, default='')
    monat = models.CharField(max_length=16, default='')
    akt_day = models.DateField()
