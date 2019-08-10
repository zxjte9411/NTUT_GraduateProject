# from django.conf.urls import include, url
from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path("", views.home, name='home'),
    path("contact", views.contact, name='contact'),
    path("trading", views.trading, name='trading'),
    path("withdraw", views.withdraw, name='withdraw'),
    path("stockPoint", views.stockPoint, name='stockPoint')
]
