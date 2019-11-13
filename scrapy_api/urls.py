from django.contrib import admin
from django.urls import path, include
from scrapy_api.views import crawl, cancel

urlpatterns = [
    path('', crawl, name='crawl_url'),
    path('cancel', cancel, name='cancel_url'),
]
