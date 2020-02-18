"""whby URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import view
from . import board_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('whapi/', include('rights.urls')),
    path('whapi/', include('fundamental.urls')),
    path('whapi/', include('data_input.urls')),
    path('whapi/product/target', view.TragetDiff.as_view()),
    path('whapi/product/target/type', view.TragetDiffType.as_view()),
    path('whapi/product/batch', view.ProductBatch.as_view()),
    path('whapi/product/quality', view.ProductQuality.as_view()),
    path('whapi/board/product_daily_report', board_view.DailyReport.as_view()),
    path('whapi/board/product_output', board_view.OutPut.as_view()),
    path('whapi/board/product_incoming_quality', board_view.IncomingQuality.as_view()),
]
