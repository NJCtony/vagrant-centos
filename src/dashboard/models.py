from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class DemandChangeRecord(models.Model):
    clm_code = models.CharField(max_length=16, default=None)
    soldtoname = models.CharField(max_length=64, default=None)
    salesname = models.CharField(max_length=32, default=None)
    monat = models.CharField(max_length=16, default=None)
    akt_day = models.DateField()
    last_umwteuro_amt = models.FloatField(default=0)
    this_umwteuro_amt = models.FloatField(default=0)
    diff_umwteuro = models.FloatField(default=0)
    sc_diff_umwteuro_percent = models.FloatField(default=0)
    alert_flag = models.NullBooleanField()

class SupplyChangeRecord(models.Model):
    clm_code = models.CharField(max_length=16, default=None)
    soldtoname = models.CharField(max_length=64, default=None)
    salesname = models.CharField(max_length=32, default=None)
    monat = models.CharField(max_length=32, default=None)
    akt_day = models.DateField()
    this_umwtpcs_3WPeriod = models.IntegerField(default=0)
    last_umwtpcs_3WPeriod = models.IntegerField(default=0)
    diff_umwtpcs_3WPeriod = models.IntegerField(default=0)
    this_umatpcs_3WPeriod = models.IntegerField(default=0)
    last_umatpcs_3WPeriod = models.IntegerField(default=0)
    diff_umatpcs_3WPeriod = models.IntegerField(default=0)
    diff_umatpcs_3WPeriod_percent = models.FloatField(default=0)
    alert_flag = models.NullBooleanField()

class OrderDiscrepancyAlerts(models.Model):
    alert_id = models.IntegerField(default=0)
    clm_code = models.CharField(max_length=16, default=None)
    soldtoname = models.CharField(max_length=64, default=None)
    salesname = models.CharField(max_length=32, default=None)
    monat = models.CharField(max_length=16, default=None)
    wtpcs_amt = models.IntegerField(default=0)
    average = models.FloatField(default=0)
    num_sd_diff = models.FloatField(default=0)
    abs_num_sd_diff = models.FloatField(default=0)
    percentage_deviation = models.FloatField(default=0)
    upper_control_limit = models.FloatField(default=0)
    lower_control_limit = models.FloatField(default=0)
    alert_flag = models.NullBooleanField()

class OrderDiscrepancyGraphData(models.Model):
    alert_id = models.IntegerField(default=0)
    clm_code = models.CharField(max_length=16, default=None)
    soldtoname = models.CharField(max_length=64, default=None)
    salesname = models.CharField(max_length=32, default=None)
    monat = models.CharField(max_length=16, default=None)
    wtpcs_amt = models.IntegerField(default=0)

class BusinessPerformance(models.Model):
    clm_code = models.CharField(max_length=16, default=None)
    soldtoname = models.CharField(max_length=64, default=None)
    bp_demand_this_quarter = models.CharField(max_length=16, default=None)
    bp_demand_next_quarter = models.CharField(max_length=16, default=None)
    current_quarter = models.CharField(max_length=16, default=None)
    next_quarter = models.CharField(max_length=16, default=None)
    bp_supply = models.FloatField(default=0)
    bp_order = models.FloatField(default=0)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    clm_code = models.CharField(max_length=16, default='')
    demand_up_threshold = models.FloatField(default=10)
    demand_down_threshold = models.FloatField(default=50000)
    supply_down_threshold = models.FloatField(default=93)

    def __str__(self):
        return '%s %s %s %s' %(self.clm_code, self.demand_up_threshold, self.demand_down_threshold, self.supply_down_threshold)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    if created:
        instance.profile.save()
