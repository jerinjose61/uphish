from django.urls import path
from app import views

app_name = 'app'

urlpatterns = [
    path('', views.home, name='home'),
    path('sending_profiles/', views.sending_profiles, name = 'sending_profiles'),
    path('add_sending_profile/', views.add_sending_profile, name = 'add_sending_profile'),
    path('edit_sending_profile/<slug:pk>/', views.edit_sending_profile, name = 'edit_sending_profile'),
    path('delete_sending_profile/<slug:pk>/', views.delete_sending_profile, name = 'delete_sending_profile'),
    path('target_groups/', views.target_groups, name = 'target_groups'),
    path('add_target_group/', views.add_target_group, name = 'add_target_group'),
    path('edit_target_group/<slug:pk>/', views.edit_target_group, name = 'edit_target_group'),
    path('delete_target_group/<slug:pk>/', views.delete_target_group, name = 'delete_target_group'),
    path('targets/<slug:pk>/', views.targets, name = 'targets'),
    path('add_target/<slug:pk>/', views.add_target, name = 'add_target'),
    path('edit_target/<slug:pk>/', views.edit_target, name = 'edit_target'),
    path('delete_target/<slug:pk>/', views.delete_target, name = 'delete_target'),
    path('phishing_pages/', views.phishing_pages, name = 'phishing_pages'),
    path('add_phishing_page/', views.add_phishing_page, name = 'add_phishing_page'),
    path('delete_phishing_page/<slug:pk>/', views.delete_phishing_page, name = 'delete_phishing_page'),
    path('email_templates/', views.email_templates, name = 'email_templates'),
    path('add_email_template/', views.add_email_template, name = 'add_email_template'),
    path('edit_email_template/<slug:pk>/', views.edit_email_template, name = 'edit_email_template'),
    path('delete_email_template/<slug:pk>/', views.delete_email_template, name = 'delete_email_template'),
    path('add_campaign/', views.add_campaign, name = 'add_campaign'),
    path('delete_campaign/<slug:pk>/', views.delete_campaign, name = 'delete_campaign'),
    path('track_email/<slug:campaign_id>/<slug:target_id>/', views.track_email, name = 'track_email'),
    path('track_link/', views.track_link, name='track_link'),
    path('track_data/', views.track_data, name='track_data'),
    path('campaign_details/<slug:pk>/', views.campaign_details, name = 'campaign_details'),
    path('target_phish_details/<slug:campaign_id>/<slug:target_id>/', views.target_phish_details, name = 'target_phish_details'),
    path('target_reported/<slug:campaign_id>/<slug:target_id>/', views.target_reported, name = 'target_reported'),
]
