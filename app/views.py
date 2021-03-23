from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from app.models import (SendingProfile, TargetGroup, Target, PhishingPage,
                        EmailTemplate, Campaign, CampaignResult,
                        EmailOpenTimeLog, LinkClickTimeLog, DataSubmitted, ReportTimeLog)
from app import forms
import requests, os, re, json, ast, csv
from uphish.settings import BASE_DIR, PHISHING_EMAIL_DIR
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, BaseHTTPRequestHandler
from django_q.tasks import async_task, result
from django.db.models import Q
from urllib import parse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from app.encryption import generate_key, decrypt
from django.utils.http import urlsafe_base64_decode
from datetime import datetime
from app.filters import CampaignResultFilter

with open(str(BASE_DIR)+'/settings.json',"r") as infile:
    settings_dict = json.loads(infile.read())

# Django Views
@login_required
def home(request):
    campaigns = Campaign.objects.all()
    return render(request, 'app/home.html', {'campaigns':campaigns})

@login_required
def sending_profiles(request):
    sending_profiles = SendingProfile.objects.all()
    return render(request, 'app/sending_profile/sending_profiles.html',
                    {'sending_profiles':sending_profiles})

@login_required
def add_sending_profile(request):
    form = forms.SendingProfileForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('app:sending_profiles')

    return render(request, 'app/sending_profile/add_sending_profile.html',
                    {'form':form})

@login_required
def edit_sending_profile(request, pk):
    object = get_object_or_404(SendingProfile, pk = pk)
    form = forms.SendingProfileForm(request.POST or None, instance = object)

    if form.is_valid():
        form.save()
        return redirect('app:sending_profiles')

    return render(request, 'app/sending_profile/edit_sending_profile.html',
                    {'form':form})

@login_required
def delete_sending_profile(request, pk):
    sending_profile = SendingProfile.objects.get(pk=pk)

    if request.method == 'POST':
        sending_profile.delete()
        return redirect('app:sending_profiles')

    return render(request, 'app/sending_profile/delete_sending_profile.html',
                    {'sending_profile':sending_profile.name})

@login_required
def target_groups(request):
    target_groups = TargetGroup.objects.all()

    return render(request, 'app/target_groups/target_groups.html', {'target_groups':target_groups})

@login_required
def add_target_group(request):
    form = forms.TargetGroupForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('app:target_groups')

    return render(request, 'app/target_groups/add_target_group.html', {'form':form})

@login_required
def edit_target_group(request, pk):
    obj = get_object_or_404(TargetGroup, pk = pk)
    form = forms.TargetGroupForm(request.POST or None, instance = obj)

    if form.is_valid():
        form.save()
        return redirect('app:target_groups')

    return render(request, 'app/target_groups/edit_target_group.html', {'form':form})

@login_required
def delete_target_group(request, pk):
    target_group = TargetGroup.objects.get(pk = pk)

    if request.method == 'POST':
        target_group.delete()
        return redirect('app:target_groups')

    return render(request, 'app/target_groups/delete_target_group.html', {'target_group':target_group})

@login_required
def targets(request, pk):
    target_group = TargetGroup.objects.get(pk = pk)
    targets = Target.objects.filter(target_group = target_group)

    if request.method == "GET":
        return render(request, 'app/targets/targets.html', {'target_group':target_group, 'targets':targets})
    elif request.method == "POST":
        csv_file = request.FILES['csv_file']

        # Read file data
        file_data = csv_file.read().decode('UTF-8')

        # Split entire file data into lines
        lines = file_data.split("\n")

        # Loop over the lines
        for line in lines:
            # Split the line with "," as the delimiter. You will get a list of fields
            fields = line.split(",")

            target = Target.objects.create(first_name = fields[0],
                                            last_name = fields[1],
                                            email =  fields[2],
                                            designation = fields[3],
                                            target_group = target_group)

        return redirect('app:targets', pk=pk)

@login_required
def add_target(request, pk):
    target_group = TargetGroup.objects.get(pk = pk)
    form = forms.TargetForm(request.POST or None)

    if form.is_valid():
        target = Target.objects.create(first_name = form.cleaned_data['first_name'],
                                        last_name = form.cleaned_data['last_name'],
                                        email =  form.cleaned_data['email'],
                                        designation = form.cleaned_data['designation'],
                                        target_group = target_group)
        return redirect('app:targets', pk=pk)

    return render(request, 'app/targets/add_target.html', {'form':form, 'target_group':target_group})

@login_required
def edit_target(request, pk):
    target = Target.objects.get(pk = pk)
    form = forms.TargetForm(request.POST or None, instance = target)

    if form.is_valid():
        form.save()
        return redirect('app:targets', pk = target.target_group.pk)

    return render(request, 'app/targets/edit_target.html', {'form':form, 'target_group':target.target_group})

@login_required
def delete_target(request, pk):
    target = Target.objects.get(pk = pk)

    if request.method == 'POST':
        target.delete()
        return redirect('app:targets', pk = target.target_group.pk)

    return render(request, 'app/targets/delete_target.html', {'target':target, 'target_group':target.target_group})

@login_required
def phishing_pages(request):
    phishing_pages = PhishingPage.objects.all()

    return render(request, 'app/phishing_pages/phishing_pages.html', {'phishing_pages':phishing_pages})

@login_required
def add_phishing_page(request):
    if request.method == "POST":
        form = forms.PhishingPageForm(request.POST or None)

        if form.is_valid():
            form.save()
            return redirect('app:phishing_pages')
    else:
        form = forms.PhishingPageForm()

    return render(request, 'app/phishing_pages/add_phishing_page.html', {'form':form})

@login_required
def edit_phishing_page(request, pk):
    phishing_page = PhishingPage.objects.get(pk = pk)
    if request.method == "POST":
        form = forms.PhishingPageForm(request.POST, instance = phishing_page)

        if form.is_valid():
            form.save()

            return redirect('app:phishing_pages')
    else:
        form = forms.PhishingPageForm(instance = phishing_page)

        return render(request, 'app/phishing_pages/edit_phishing_page.html', {'form':form})

@login_required
def delete_phishing_page(request, pk):
    phishing_page = PhishingPage.objects.get(pk = pk)

    if request.method == 'POST':
        # Delete entry from database
        PhishingPage.objects.get(pk = phishing_page.pk).delete()

        return redirect('app:phishing_pages')

    return render(request, 'app/phishing_pages/delete_phishing_page.html', {'phishing_page':phishing_page})

@login_required
def email_templates(request):
    email_templates = EmailTemplate.objects.all()
    return render(request, 'app/email_templates/email_templates.html', {'email_templates':email_templates})

@login_required
def add_email_template(request):
    if request.method == 'POST':
        form = forms.EmailTemplateForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()

            # Write the body to html file in phishing_emails directory
            os.chdir(PHISHING_EMAIL_DIR)
            html_file_name = form.cleaned_data['name'] + ".html"
            email_html_file = open(html_file_name, "w")
            email_html_file.write(form.cleaned_data['body'])
            email_html_file.close()

            if ast.literal_eval(settings_dict['USE_TLS']) == True:
                # Append the string for image tracker in html file (HTTPS)
                image_tracker_string = ("\n\n<img src=" +
                                        "\'https://{{ host }}/track_email/{{ campaign_id }}/{{ target_id }}/\'" +
                                        "height=1px width=1px>")
            else:
                # Append the string for image tracker in html file (HTTP)
                image_tracker_string = ("\n\n<img src=" +
                                        "\'http://{{ host }}/track_email/{{ campaign_id }}/{{ target_id }}/\'" +
                                        "height=1px width=1px>")

            email_html_file = open(html_file_name, "a")
            email_html_file.write(image_tracker_string)
            email_html_file.close()

            return redirect('app:email_templates')
    else:
        form = forms.EmailTemplateForm()

    return render(request, 'app/email_templates/add_email_template.html', {'form':form})

@login_required
def view_email_template(request, pk):
    email_template = EmailTemplate.objects.get(pk = pk)
    return render(request, 'app/email_templates/view_email_template.html',
                    {'email_template':email_template})

@login_required
def edit_email_template(request, pk):
    email_template = EmailTemplate.objects.get(pk = pk)

    if request.method == 'POST':
        form = forms.EmailTemplateForm(request.POST, request.FILES, instance = email_template)

        if form.is_valid():
            form.save()

            # Write to html file in phishing_emails directory. This will overwrite the contents.
            os.chdir(PHISHING_EMAIL_DIR)
            html_file_name = form.cleaned_data['name'] + ".html"
            email_html_file = open(html_file_name, "w")
            email_html_file.write(form.cleaned_data['body'])
            email_html_file.close()

            if ast.literal_eval(settings_dict['USE_TLS']) == True:
                # Append the string for image tracker in html file (HTTPS)
                image_tracker_string = ("\n\n<img src=" +
                                        "\'https://{{ host }}/track_email/{{ campaign_id }}/{{ target_id }}/\'" +
                                        "height=1px width=1px>")
            else:
                # Append the string for image tracker in html file (HTTP)
                image_tracker_string = ("\n\n<img src=" +
                                        "\'http://{{ host }}/track_email/{{ campaign_id }}/{{ target_id }}/\'" +
                                        "height=1px width=1px>")

            email_html_file = open(html_file_name, "a")
            email_html_file.write(image_tracker_string)
            email_html_file.close()

            return redirect('app:email_templates')
    else:
        form = forms.EmailTemplateForm(instance = email_template)

    return render(request, 'app/email_templates/edit_email_template.html', {'form':form})

@login_required
def delete_email_template(request, pk):
    email_template = EmailTemplate.objects.get(pk = pk)

    if request.method == 'POST':
        email_template.delete()

        # Remove email html file from system
        html_file_name = email_template.name + ".html"
        os.chdir(PHISHING_EMAIL_DIR)
        os.remove(html_file_name)

        return redirect('app:email_templates')

    return render(request, 'app/email_templates/delete_email_template.html', {'email_template':email_template})

@login_required
def add_campaign(request):
    form = forms.CampaignForm(request.POST or None)

    if form.is_valid():
        form.save()

        campaign_name = form.cleaned_data['name']
        from_email = form.cleaned_data['from_email']
        target_group = form.cleaned_data['target_group']
        phishing_page = form.cleaned_data['phishing_page']
        email_template = form.cleaned_data['email_template']
        sending_profile = form.cleaned_data['sending_profile']

        # Task to send Email using the selected email template to the target groups using the sending profile
        async_task('app.tasks.launch_campaign', campaign_name,
        from_email, target_group, phishing_page,
        email_template, sending_profile)

        return redirect('app:home')

    return render(request, 'app/campaigns/add_campaign.html', {'form':form})

@login_required
def delete_campaign(request, pk):
    campaign = Campaign.objects.get(pk = pk)

    if request.method == 'POST':
        campaign.delete()

        return redirect('app:home')

    return render(request, 'app/campaigns/delete_campaign.html', {'campaign':campaign})

@login_required
def campaign_details(request, pk):
    campaign = Campaign.objects.get(pk = pk)
    targets = CampaignResult.objects.filter(campaign = campaign)

    target_count = targets.count()
    sent_count = CampaignResult.objects.filter(Q(campaign = campaign) & Q(email_sent_status = True)).count()
    open_count = CampaignResult.objects.filter(Q(campaign = campaign) & Q(email_open_status = True)).count()
    click_count = CampaignResult.objects.filter(Q(campaign = campaign) & Q(link_clicked_status = True)).count()
    data_count = CampaignResult.objects.filter(Q(campaign = campaign) & Q(data_submitted_status = True)).count()
    reported_count = CampaignResult.objects.filter(Q(campaign = campaign) & Q(reported = True)).count()

    return render(request, 'app/campaigns/campaign_details.html', {'campaign':campaign, 'targets':targets,
                                                                    'target_count':target_count,
                                                                    'sent_count':sent_count,
                                                                    'open_count':open_count,
                                                                    'click_count':click_count,
                                                                    'data_count':data_count,
                                                                    'reported_count':reported_count})
@login_required
def campaign_targets(request, pk):
    campaign = Campaign.objects.get(pk=pk)
    targets = Target.objects.filter(target_group = campaign.target_group)

    return render(request, 'app/campaigns/campaign_targets.html',
                    {"campaign":campaign, "targets":targets})

@login_required
def campaign_targets_sent(request, pk):
    campaign = Campaign.objects.get(pk=pk)
    targets_sent = CampaignResult.objects.filter(Q(campaign = campaign) &
                    Q(email_sent_status = True))

    return render(request, 'app/campaigns/campaign_targets_sent.html',
                    {"campaign":campaign, "targets_sent":targets_sent})

@login_required
def campaign_targets_opened(request, pk):
    campaign = Campaign.objects.get(pk=pk)
    targets_opened = CampaignResult.objects.filter(Q(campaign = campaign) &
                    Q(email_open_status = True))

    targets_open_details = {}

    for target in targets_opened:
        target_open_time = EmailOpenTimeLog.objects.filter(Q(campaign = campaign)
                            & Q(target = target.target))

        targets_open_details[target.target]  = target_open_time

    return render(request, 'app/campaigns/campaign_targets_opened.html',
                    {"campaign":campaign, "targets_open_details":targets_open_details})

@login_required
def campaign_targets_clicked(request, pk):
    campaign = Campaign.objects.get(pk=pk)
    targets_clicked = CampaignResult.objects.filter(Q(campaign = campaign) &
                    Q(link_clicked_status = True))

    targets_clicked_details = {}

    for target in targets_clicked:
        target_click_time = LinkClickTimeLog.objects.filter(Q(campaign = campaign)
                            & Q(target = target.target))

        targets_clicked_details[target.target]  = target_click_time

    return render(request, 'app/campaigns/campaign_targets_clicked.html',
                    {"campaign":campaign,
                    "targets_clicked_details":targets_clicked_details})

@login_required
def campaign_targets_submitted_data(request, pk):
    campaign = Campaign.objects.get(pk=pk)
    targets_submitted_data = CampaignResult.objects.filter(Q(campaign = campaign) &
                    Q(data_submitted_status = True))

    targets_submitted_data_details = {}

    for target in targets_submitted_data:
        data_submitted = DataSubmitted.objects.filter(Q(campaign = campaign)
                            & Q(target = target.target))

        targets_submitted_data_details[target.target]  = data_submitted

    return render(request, 'app/campaigns/campaign_targets_submitted_data.html',
                    {"campaign":campaign,
                    "targets_submitted_data_details":targets_submitted_data_details})

@login_required
def campaign_targets_reported(request, pk):
    campaign = Campaign.objects.get(pk=pk)
    targets_reported = CampaignResult.objects.filter(Q(campaign = campaign) &
                    Q(reported = True))

    targets_reported_details = {}

    for target in targets_reported:
        target_report_time = ReportTimeLog.objects.filter(Q(campaign = campaign)
                            & Q(target = target.target))

        targets_reported_details[target.target]  = target_report_time

    return render(request, 'app/campaigns/campaign_targets_reported.html',
                    {"campaign":campaign,
                    "targets_reported_details":targets_reported_details})

@login_required
def target_phish_details(request, campaign_id, target_id):
    campaign = Campaign.objects.get(pk = campaign_id)
    target = Target.objects.get(pk = target_id)

    target_details = CampaignResult.objects.get(Q(campaign = campaign) & Q(target = target))
    email_open_times = EmailOpenTimeLog.objects.filter(Q(campaign = campaign) & Q(target = target))
    link_click_times = LinkClickTimeLog.objects.filter(Q(campaign = campaign) & Q(target = target))
    data_submitted = DataSubmitted.objects.filter(Q(campaign = campaign) & Q(target = target))
    report_times = ReportTimeLog.objects.filter(Q(campaign = campaign) & Q(target = target))

    return render(request, 'app/campaigns/target_phish_details.html', {'target':target_details,
                    'email_open_times':email_open_times, 'link_click_times':link_click_times,
                    'data_submitted':data_submitted, 'report_times':report_times})

@login_required
def target_phish_details_from_filter(request, campaign_id, target_id):
    campaign = Campaign.objects.get(pk = campaign_id)
    target = Target.objects.get(pk = target_id)

    target_details = CampaignResult.objects.get(Q(campaign = campaign) & Q(target = target))
    email_open_times = EmailOpenTimeLog.objects.filter(Q(campaign = campaign) & Q(target = target))
    link_click_times = LinkClickTimeLog.objects.filter(Q(campaign = campaign) & Q(target = target))
    data_submitted = DataSubmitted.objects.filter(Q(campaign = campaign) & Q(target = target))
    report_times = ReportTimeLog.objects.filter(Q(campaign = campaign) & Q(target = target))

    return render(request, 'app/campaigns/target_phish_details_from_filter.html', {'target':target_details,
                    'email_open_times':email_open_times, 'link_click_times':link_click_times,
                    'data_submitted':data_submitted, 'report_times':report_times})

@login_required
def target_reported(request, campaign_id, target_id):
    campaign = Campaign.objects.get(pk = campaign_id)
    target = Target.objects.get(pk = target_id)

    target_details = CampaignResult.objects.get(Q(campaign = campaign) & Q(target = target))

    if (target_details.reported == False) or (target_details.reported == None):
        CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(reported = True)
        ReportTimeLog.objects.create(campaign = campaign, target = target, report_time = datetime.now())
    else:
        CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(reported = False)

    return redirect('app:target_phish_details', campaign.id, target.id)

@login_required
def target_reported_from_filter(request, campaign_id, target_id):
    campaign = Campaign.objects.get(pk = campaign_id)
    target = Target.objects.get(pk = target_id)

    target_details = CampaignResult.objects.get(Q(campaign = campaign) & Q(target = target))

    if (target_details.reported == False) or (target_details.reported == None):
        CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(reported = True)
        ReportTimeLog.objects.create(campaign = campaign, target = target, report_time = datetime.now())
    else:
        CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(reported = False)

    return redirect('app:target_phish_details_from_filter', campaign.id, target.id)

# Download Campaign Report
@login_required
def download_campaign_report(request, pk):
    campaign = Campaign.objects.get(pk = pk)
    campaign_results = CampaignResult.objects.filter(campaign = campaign)

    #Write data to csv
    currentDT = str(datetime.now())[0:16]
    response = HttpResponse(content_type='text/csv')
    response_string = 'attachment; filename="{} - Phishing Campaign Report - {}.csv"'
    response['Content-Disposition'] = response_string.format(campaign.name, currentDT)

    writer = csv.writer(response)

    # Writing the report header fields
    writer.writerow(['Target Name', 'Email ID', 'Designation',
                    'Sent', 'Sent Time',
                    'Opened', 'Open Count', 'Open Time',
                    'Clicked', 'Click Count', 'Click Time',
                    'Submitted Data', 'Submitted Data Count', 'Submitted Data Values', 'Submitted Data Time',
                    'Reported', 'Reported Time'])

    for campaign_result in campaign_results:
        # Open Count & Time
        email_open_time_logs = EmailOpenTimeLog.objects.filter(Q(campaign = campaign) & Q(target=campaign_result.target))
        email_open_count = email_open_time_logs.count()

        email_open_time = ''
        for email_open_time_log in email_open_time_logs:
            email_open_time += str(email_open_time_log.email_open_time) + '\n'

        # Click Count & Time
        link_click_time_logs = LinkClickTimeLog.objects.filter(Q(campaign = campaign) & Q(target=campaign_result.target))
        link_click_count = link_click_time_logs.count()

        link_click_time = ''
        for link_click_time_log in link_click_time_logs:
            link_click_time += str(link_click_time_log.link_click_time) + '\n'

        # Submitted Data Values & Time
        submitted_data_logs = DataSubmitted.objects.filter(Q(campaign = campaign) & Q(target = campaign_result.target))
        submitted_data_count = submitted_data_logs.count()
        submitted_data_values = ''
        submitted_data_times = ''

        for submitted_data_log in submitted_data_logs:
            submitted_data_values += submitted_data_log.data_submitted + '\n'
            submitted_data_times += str(submitted_data_log.data_submit_time) + '\n'

        # Reported Time
        reported_time_logs = ReportTimeLog.objects.filter(Q(campaign = campaign) & Q(target = campaign_result.target))
        reported_time = ''

        for reported_time_log in reported_time_logs:
            reported_time += str(reported_time_log.report_time) + '\n'

        writer.writerow([campaign_result.target.first_name + ' ' + campaign_result.target.last_name,
                        campaign_result.target.email, campaign_result.target.designation,
                        campaign_result.email_sent_status, campaign_result.email_sent_time,
                        campaign_result.email_open_status, email_open_count, email_open_time,
                        campaign_result.link_clicked_status, link_click_count, link_click_time,
                        campaign_result.data_submitted_status, submitted_data_count, submitted_data_values, submitted_data_times,
                        campaign_result.reported, reported_time])

    return response

# FIlter Campaign Result
@login_required
def filter(request, pk):
    campaign = Campaign.objects.get(pk = pk)
    campaign_results = CampaignResult.objects.filter(campaign = campaign)
    campaign_result_filter = CampaignResultFilter(request.GET, queryset = campaign_results)

    return render(request, 'app/campaigns/filter.html', {'filter': campaign_result_filter,
                    'campaign':campaign})

# Function to track if email was opened
def track_email(request, encrypted_campaign_id, encrypted_target_id):
    # # Decode & then decrypt encrypted_campaign_id and encrypted_target_id
    # First decode & decrypt campaign_id
    decoded_campaign_id = urlsafe_base64_decode(encrypted_campaign_id)

    key = generate_key()
    campaign_id = int(decrypt(decoded_campaign_id, key))

    # First decode & decrypt campaign_id (key is same as before)
    decoded_target_id = urlsafe_base64_decode(encrypted_target_id)
    target_id = int(decrypt(decoded_target_id, key))

    campaign = Campaign.objects.get(id = campaign_id)
    target = Target.objects.get(id = target_id)

    CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(email_open_status = True)
    EmailOpenTimeLog.objects.create(campaign = campaign, target = target,
                                    email_open_time = datetime.now())

    return HttpResponse('Email Opened!')

# API End Point to know from FastAPI phsihing app that link has been clicked
@csrf_exempt
def track_link(request):
    # Get CID and TID from FastAPI Phishing App
    encrypted_cid = request.POST.get("cid")
    encrypted_tid = request.POST.get("tid")

    # # Decode & then decrypt encrypted_cid and encrypted_tid
    # First decode & decrypt campaign_id
    decoded_cid = urlsafe_base64_decode(encrypted_cid)

    key = generate_key()
    cid = int(decrypt(decoded_cid, key))

    # First decode & decrypt campaign_id (key is same as before)
    decoded_tid = urlsafe_base64_decode(encrypted_tid)
    tid = int(decrypt(decoded_tid, key))

    # Update DB that the link is clicked
    campaign = Campaign.objects.get(id = cid)
    target = Target.objects.get(id = tid)

    CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(link_clicked_status = True)

    # In some cases, the tracker image may not be automatically loaded by email clients
    # So, when the person click on the link, we will assume that the person has opened the email
    CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(email_open_status = True)

    LinkClickTimeLog.objects.create(campaign = campaign, target = target,
                                    link_click_time = datetime.now())

    return HttpResponse('Phishing Link Clicked!')

# API End Point to know from FastAPI phishing app that data has been submitted
# API End Point to know the submitted data
@csrf_exempt
def track_data(request):
    # Get CID, TID & submitted data from FastAPI Phishing App
    encrypted_cid = request.POST.get("cid")
    encrypted_tid = request.POST.get("tid")
    submitted_data = request.POST.get("submitted_data")

    # # Decode & then decrypt encrypted_cid and encrypted_tid
    # First decode & decrypt campaign_id
    decoded_cid = urlsafe_base64_decode(encrypted_cid)

    key = generate_key()
    cid = int(decrypt(decoded_cid, key))

    # First decode & decrypt campaign_id (key is same as before)
    decoded_tid = urlsafe_base64_decode(encrypted_tid)
    tid = int(decrypt(decoded_tid, key))

    # Update DB that the data is submitted and enter the submitted data
    campaign = Campaign.objects.get(id = cid)
    target = Target.objects.get(id = tid)

    CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(data_submitted_status = True)

    if campaign.capture_data == True:
        DataSubmitted.objects.create(campaign = campaign, target = target,
                                        data_submitted = submitted_data,
                                        data_submit_time = datetime.now())
    else:
        DataSubmitted.objects.create(campaign = campaign, target = target,
                                        data_submit_time = datetime.now())

    return HttpResponse('Data Submitted!')
