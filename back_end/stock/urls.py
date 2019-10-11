# from django.conf.urls import include, url
from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path("", views.home, name='home'),
    path("contact", views.contact, name='contact'),
    path("trading", views.trading, name='trading'),
    path("withdraw", views.withdraw, name='withdraw'),
    path("withdraw/detail", views.detail, name='withdraw_detail'),
    path("stockPoint", views.stockPoint, name='stockPoint'),
    path("__", views.remote_ip_address, name='remote_ip_address')
]
