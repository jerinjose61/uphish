from django.contrib import admin
from app import models
# Register your models here.

admin.site.register(models.SendingProfile)
admin.site.register(models.TargetGroup)
admin.site.register(models.Target)
admin.site.register(models.PhishingPage)
admin.site.register(models.EmailTemplate)
admin.site.register(models.Campaign)
admin.site.register(models.CampaignResult)
