from django.db import models
from ckeditor.fields import RichTextField
from django_cryptography.fields import encrypt
# Create your models here.

class SendingProfile(models.Model):
    name = models.CharField(max_length = 1000)
    username = models.CharField(max_length = 2000, null = True)
    password = models.CharField(max_length = 1000)
    smtp_server = models.CharField(max_length = 1000)
    smtp_port = models.IntegerField()
    use_tls = models.BooleanField(default = True, null = True)

    def __str__(self):
        return self.name

class TargetGroup(models.Model):
    name = models.CharField(max_length = 1000)

    def __str__(self):
        return self.name

class Target(models.Model):
    first_name = models.CharField(max_length = 1000)
    last_name = models.CharField(max_length = 1000)
    email = models.EmailField()
    designation = models.CharField(max_length = 1000)
    target_group = models.ForeignKey(TargetGroup, on_delete = models.CASCADE)

    def __str__(self):
        return self.email

class PhishingPage(models.Model):
    name = models.CharField(max_length = 1000)
    phishing_url = models.CharField(max_length = 1000)

    def __str__(self):
        return self.name

class EmailTemplate(models.Model):
    name = models.CharField(max_length = 1000)
    subject = models.CharField(max_length = 1000)
    body = RichTextField()
    attachment = models.FileField(upload_to='attachments/', null = True, blank = True)

    def __str__(self):
        return self.name

class Campaign(models.Model):
    name = models.CharField(max_length = 1000, unique = True)
    from_email = models.CharField(max_length = 1000)
    target_group = models.ForeignKey(TargetGroup, on_delete = models.CASCADE)
    phishing_page = models.ForeignKey(PhishingPage, on_delete = models.CASCADE)
    email_template = models.ForeignKey(EmailTemplate, on_delete = models.CASCADE)
    sending_profile = models.ForeignKey(SendingProfile, on_delete = models.CASCADE)
    capture_data = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class CampaignResult(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete = models.CASCADE)
    target = models.ForeignKey(Target, on_delete = models.CASCADE)
    email_sent_status = models.BooleanField(null = True, default=False)
    email_sent_time = models.DateTimeField(null = True)
    email_open_status = models.BooleanField(null = True, default=False)
    link_clicked_status = models.BooleanField(null = True, default=False)
    data_submitted_status = models.BooleanField(null = True, default=False)
    reported = models.BooleanField(null = True, default=False)

    def __str__(self):
        return str(self.campaign)

class EmailOpenTimeLog(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete = models.CASCADE)
    target = models.ForeignKey(Target, on_delete = models.CASCADE)
    email_open_time = models.DateTimeField()

class LinkClickTimeLog(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete = models.CASCADE)
    target = models.ForeignKey(Target, on_delete = models.CASCADE)
    link_click_time = models.DateTimeField()

class DataSubmitted(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete = models.CASCADE)
    target = models.ForeignKey(Target, on_delete = models.CASCADE)
    data_submitted = encrypt(models.TextField(null = True))
    data_submit_time = models.DateTimeField()

class ReportTimeLog(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete = models.CASCADE)
    target = models.ForeignKey(Target, on_delete = models.CASCADE)
    report_time = models.DateTimeField()
