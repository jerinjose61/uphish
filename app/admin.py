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
admin.site.register(models.EmailOpenTimeLog)
admin.site.register(models.LinkClickTimeLog)
admin.site.register(models.DataSubmitTimeLog)
admin.site.register(models.ReportTimeLog)
