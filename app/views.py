from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from app.models import SendingProfile, TargetGroup, Target, PhishingPage, EmailTemplate, Campaign, CampaignResult
from app import forms
import requests, os, socketserver, threading, random, socket, time, shutil, re, ssl, json, ast
from uphish.settings import BASE_DIR, PHISHING_EMAIL_DIR, PHISHING_TEMPLATES_DIR
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, BaseHTTPRequestHandler
from django_q.tasks import async_task, result
from django.db.models import Q
from urllib import parse
from django.contrib.auth.decorators import login_required

# Global Variables
DEFAULT_USER_AGENT = "\"Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/60.0\""
DEFAULT_PORT = 8000
httpd = None

server_list = {}
server_details = {}

with open(str(BASE_DIR)+'/settings.json',"r") as infile:
    settings_dict = json.loads(infile.read())

# Supporting Functions & Classes
def port_check(port_number):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex(('127.0.0.1', port_number))

    if result != 0:
        return True
    else:
        return False

def port():
    port_number = random.randint(1025, 65535)

    if port_check(port_number) == True:
        return port_number
    else:
        port()

def start_server(server):
    server.serve_forever()

class MySimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = re.match(r'\/\?cid=[0-9]+&tid=[0-9]+', self.path)

        try:
            if self.path == path.group():
                self.path = '/'
        except AttributeError:
            pass

        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        # Pattern for /?cid=1&tid=1
        path = re.match(r'\/\?cid=[0-9]+&tid=[0-9]+', self.path)

        try:
            if self.path == path.group():
                # Get campaign_id
                campaign_id = parse.parse_qs(parse.urlparse(self.path).query)['cid'][0]

                # Get target_id
                target_id = parse.parse_qs(parse.urlparse(self.path).query)['tid'][0]

                # Update DB that the person has entered data
                campaign = Campaign.objects.get(id = campaign_id)
                target = Target.objects.get(id = target_id)

                CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(data_submitted_status = True)

                # Update DB with entered data
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                form_data = body.decode("utf-8")
                form_data_list = form_data.split('&')

                form_data_decoded_list = []

                for data in form_data_list:
                    form_data_decoded_list.append(parse.unquote(data))

                final_form_data = '; '.join(form_data_decoded_list)

                CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(data_submitted = final_form_data)

                # Redirect to the Redirect URL given by user after form submission
                self.send_response(301)
                self.send_header("location", campaign.redirect_url)
                self.end_headers()
        except AttributeError:
            pass

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
    return render(request, 'app/targets/targets.html', {'target_group':target_group, 'targets':targets})

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
    form = forms.PhishingPageForm(request.POST or None)

    if form.is_valid():
        # Download files from original website
        wget_command = "wget -e robots=off -E -H -k -K -p -nH --cut-dirs=100 -nv {} --user-agent {} --directory-prefix={}"

        template_folder_name = '_'.join(form.cleaned_data['name'].split()).lower()
        TEMPLATE_DIR = os.path.join(BASE_DIR, 'phishing_templates/{}'.format(template_folder_name))

        os.system(wget_command.format(form.cleaned_data['url_to_clone'],
                    DEFAULT_USER_AGENT, TEMPLATE_DIR))

        # Update DB details of the phishing page
        PhishingPage.objects.create(name = form.cleaned_data['name'],
                                    url_to_clone = form.cleaned_data['url_to_clone'],
                                    template_dir = TEMPLATE_DIR)

        # Rename HTML file to index.html if it is in another name (like login.html)
        for file in os.listdir(TEMPLATE_DIR):
            if file.endswith(".html") or file.endswith(".htm"):
                if file != 'index.html':
                    os.rename(TEMPLATE_DIR + "/" + file, TEMPLATE_DIR + "/index.html")

        ## Remove the string action="" inside a form in index.html
        ## This is to ensure do_POST() method in MySimpleHTTPRequestHandler works OK
        html_file = open(TEMPLATE_DIR + "/index.html", "r")
        html_file_content = html_file.read()
        new_html_file_content = re.sub('<form .*>',"<form method=\"POST\">",html_file_content)
        html_file.close()

        # Write new string to index.html
        new_html_file = open(TEMPLATE_DIR + "/index.html", "w")
        new_html_file.write(new_html_file_content)
        new_html_file.close()

        return redirect('app:phishing_pages')

    return render(request, 'app/phishing_pages/add_phishing_page.html', {'form':form})

@login_required
def start_phishing_server(request, pk):
    phishing_page = PhishingPage.objects.get(pk = pk)

    os.chdir(phishing_page.template_dir)
    handler = MySimpleHTTPRequestHandler

    global server_details
    global server_list

    if port_check(DEFAULT_PORT) == True:
        try:
            server = socketserver.TCPServer(("", DEFAULT_PORT), handler)
            server_thread = threading.Thread(target=start_server, args=(server,), daemon=True)
            server_thread.start()

            server_details['server'] = server
            server_details['server_thread'] = server_thread
            server_details['port'] = DEFAULT_PORT
        except socketserver.socket.error as exc:
            if exc.args[0] == 48:
                port_number = port()
                server = socketserver.TCPServer(("", port_number), handler)
                server_thread = threading.Thread(target=start_server, args=(server,), daemon=True)
                server_thread.start()

                server_details['server'] = server
                server_details['server_thread'] = server_thread
                server_details['port'] = port_number
    else:
        port_number = port()
        server = socketserver.TCPServer(("", port_number), handler)
        server_thread = threading.Thread(target=start_server, args=(server,), daemon=True)
        server_thread.start()

        server_details['server'] = server
        server_details['server_thread'] = server_thread
        server_details['port'] = port_number

    server_list[phishing_page.name] = server_details

    host = settings_dict['HOST']

    PhishingPage.objects.filter(pk = phishing_page.pk).update(server_status = True,
                                port_number = server_details['port'],
                                site_url = "http://" + host + ":" + str(server_details['port']))

    return redirect('app:phishing_pages')

@login_required
def stop_phishing_server(request, pk):
    phishing_page = PhishingPage.objects.get(pk = pk)

    try:
        # Get details of server of this phishing page
        global server_list
        server = server_list[phishing_page.name]['server']

        # Stop the server
        server.shutdown()
        server.server_close()

        PhishingPage.objects.filter(pk = phishing_page.pk).update(server_status = False,
                                    port_number = None,
                                    site_url = None)
    except KeyError:
        PhishingPage.objects.filter(pk = phishing_page.pk).update(port_number = None,
                                    site_url = None)

    return redirect('app:phishing_pages')

@login_required
def delete_phishing_page(request, pk):
    phishing_page = PhishingPage.objects.get(pk = pk)

    if request.method == 'POST':
        if phishing_page.server_status == True:
            try:
                # Get details of server of this phishing page
                global server_list
                server = server_list[phishing_page.name]['server']

                # Stop the server
                server.shutdown()
                server.server_close()

                # Delete entry from database
                PhishingPage.objects.get(pk = phishing_page.pk).delete()

                # Delete folder from phishing_templates
                shutil.rmtree(phishing_page.template_dir)
            except KeyError:
                pass
        else:
            PhishingPage.objects.get(pk = phishing_page.pk).delete()

            # Delete folder from phishing_templates
            shutil.rmtree(phishing_page.template_dir)

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
                # Append the string for image tracker in html file
                image_tracker_string = ("\n\n<img src=" +
                                        "\'https://{{ host }}/track_email/{{ campaign_id }}/{{ target_id }}/\'" +
                                        "height=1px width=1px>")
            else:
                # Append the string for image tracker in html file
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
                # Append the string for image tracker in html file
                image_tracker_string = ("\n\n<img src=" +
                                        "\'https://{{ host }}/track_email/{{ campaign_id }}/{{ target_id }}/\'" +
                                        "height=1px width=1px>")
            else:
                # Append the string for image tracker in html file
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
        email_template = form.cleaned_data['email_template']
        sending_profile = form.cleaned_data['sending_profile']
        redirect_url = form.cleaned_data['redirect_url']

        # Task to send Email using the selected email template to the target groups using the sending profile
        async_task('app.tasks.launch_campaign', campaign_name, from_email, target_group, email_template, sending_profile)

        return redirect('app:home')

    return render(request, 'app/campaigns/add_campaign.html', {'form':form})

@login_required
def delete_campaign(request, pk):
    campaign = Campaign.objects.get(pk = pk)

    if request.method == 'POST':
        campaign.delete()

        return redirect('app:home')

    return render(request, 'app/campaigns/delete_campaign.html', {'campaign':campaign})

def track_email(request, campaign_id, target_id):
    campaign = Campaign.objects.get(id = campaign_id)
    target = Target.objects.get(id = target_id)

    CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(email_open_status = True)

    return HttpResponse('Phished!')

def track_link(request, campaign_id, target_id):
    campaign = Campaign.objects.get(id = campaign_id)
    target = Target.objects.get(id = target_id)

    CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(link_clicked_status = True)

    # In some cases, the tracker image may not be automatically loaded by email clients
    # So, when the person click on the link, we will assume that the person has opened the email
    CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(email_open_status = True)

    phishing_url = campaign.phishing_page.site_url + "/?cid=" + campaign_id + "&tid=" + target_id + ""
    return redirect(phishing_url)

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
def target_phish_details(request, campaign_id, target_id):
    campaign = Campaign.objects.get(pk = campaign_id)
    target = Target.objects.get(pk = target_id)

    target_details = CampaignResult.objects.get(Q(campaign = campaign) & Q(target = target))

    return render(request, 'app/campaigns/target_phish_details.html', {'target':target_details})

@login_required
def target_reported(request, campaign_id, target_id):
    campaign = Campaign.objects.get(pk = campaign_id)
    target = Target.objects.get(pk = target_id)

    target_details = CampaignResult.objects.get(Q(campaign = campaign) & Q(target = target))

    if (target_details.reported == False) or (target_details.reported == None):
        CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(reported = True)
    else:
        CampaignResult.objects.filter(Q(campaign = campaign) & Q(target = target)).update(reported = False)

    return redirect('app:target_phish_details', campaign.id, target.id)
