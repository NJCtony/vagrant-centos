from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class NeedOneRecord(models.Model):
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

class NeedThreeRecord(models.Model):
    soldtoname = models.CharField(max_length=64, default=None)
    salesname = models.CharField(max_length=32, default=None)
    monat = models.CharField(max_length=16, default=None)
    wtpcs_amt = models.IntegerField(default=0)
    average = models.FloatField(default=0)
    alert_type = models.CharField(max_length=16, default=None)
    alert_description = models.CharField(max_length=64, default=None)

class BusinessPerformance(models.Model):
    clm_code = models.CharField(max_length=16, default=None)
    alert_type = models.CharField(max_length=16, default=None)
    soldtoname = models.CharField(max_length=64, default=None)
    bp = models.FloatField(default=0)
    monat = models.CharField(max_length=32, default=None)

class ClmSoldtoPair(models.Model):
    clm_code = models.CharField(max_length=16, default='')
    soldtoname = models.CharField(max_length=64, default=None)

    class Meta:
        unique_together = ("clm_code", "soldtoname")

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    clm_code = models.CharField(max_length=16, default='', unique=True)
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
