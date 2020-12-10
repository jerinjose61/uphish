from django import forms
from app.models import SendingProfile, TargetGroup, Target, PhishingPage, EmailTemplate, Campaign

class SendingProfileForm(forms.ModelForm):
    name = forms.CharField(label='Name')
    email = forms.EmailField(label="Email ID")
    password = forms.CharField(label="Password")
    smtp_server = forms.CharField(label="SMTP Server")
    smtp_port = forms.IntegerField(label="SMTP Port")
    use_tls = forms.BooleanField(label="Use TLS?", required=False)

    class Meta:
        model = SendingProfile
        fields = '__all__'

class TargetGroupForm(forms.ModelForm):
    class Meta:
        model = TargetGroup
        fields = '__all__'

class TargetForm(forms.ModelForm):
    first_name = forms.CharField(label = 'First Name')
    last_name = forms.CharField(label = 'Second Name')
    email = forms.EmailField()

    class Meta:
        model = Target
        fields = ['first_name', 'last_name', 'email', 'designation']

class PhishingPageForm(forms.ModelForm):
    phishing_url = forms.CharField(label="Phishing URL (Without http / https)",
                                    widget=forms.TextInput(attrs={'placeholder':'www.example.com'}))
    use_tls = forms.BooleanField(label="Use TLS?", required=False)

    class Meta:
        model = PhishingPage
        fields = '__all__'

class EmailTemplateForm(forms.ModelForm):
    attachment = forms.FileField(required = False)
    class Meta:
        model = EmailTemplate
        fields = '__all__'

class CampaignForm(forms.ModelForm):
    from_email = forms.CharField(label = "From Name & Email", widget=forms.TextInput(attrs={'placeholder':'Jerin Jose <jerinjose@example.com>'}))

    class Meta:
        model = Campaign
        fields = '__all__'
        labels = {
            "target_group": "Target Group",
            "phishing_page": "Phishing Page",
            "email_template": "Email Template",
            "sending_profile": "Sending Profile",
            "redirect_url": "Redirect URL"
        }
