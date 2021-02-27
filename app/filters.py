import django_filters
from app.models import CampaignResult

class CampaignResultFilter(django_filters.FilterSet):
    class Meta:
        model = CampaignResult
        fields = ['target', 'email_sent_status', 'email_open_status',
                    'link_clicked_status', 'data_submitted_status', 'reported']
