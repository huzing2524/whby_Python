# -*- coding: utf-8 -*-
# @Time   : 19-6-22 上午10:36
# @Author : huziying
# @File   : urls.py

from django.urls import path

from . import views

urlpatterns = [
    path('rights', views.Rights.as_view()),
]
