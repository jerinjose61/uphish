from app.models import Target, Campaign, CampaignResult
from django.template.loader import render_to_string
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage, send_mail
import os, socket, json
from uphish.settings import PHISHING_EMAIL_DIR, MEDIA_ROOT, BASE_DIR
import smtplib

with open(str(BASE_DIR)+'/settings.json',"r") as infile:
    settings_dict = json.loads(infile.read())

def launch_campaign(campaign_name, from_email, target_group, email_template, sending_profile):
    smtp_server = sending_profile.smtp_server
    smtp_port = sending_profile.smtp_port
    email = sending_profile.email
    password = sending_profile.password
    use_tls = sending_profile.use_tls
    email_backend = EmailBackend(host=smtp_server, port=smtp_port, username=email,
                     password=password, use_tls=use_tls)

    host = settings_dict['HOST']

    subject = email_template.subject
    targets = list(Target.objects.filter(target_group = target_group))

    campaign = Campaign.objects.get(name=campaign_name)

    for target in targets:
        email_html_file_name = email_template.name + ".html"
        html_message = render_to_string(email_html_file_name, context={'host':host,
                                                                        'campaign_id':campaign.id,
                                                                        'target_id':target.id})

        try:
            email = EmailMessage(subject = subject, body = html_message, from_email = from_email,
            to = [target,], connection = email_backend)
            if email_template.attachment:
                email.attach_file(str(MEDIA_ROOT) + "/" + str(email_template.attachment))
            email.content_subtype = 'html'
            email.send()
            CampaignResult.objects.create(campaign = campaign, target = target,
                                            email_sent_status = True)
        except smtplib.SMTPException:
            CampaignResult.objects.create(campaign = campaign, target = target,
                                            email_sent_status = False)
