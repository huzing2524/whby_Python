from django.urls import path
from . import views

urlpatterns = [
    path('annual_plan/main', views.AnnualPlanMain.as_view()),
    path('schedule/main', views.ScheduleMain.as_view()),
    path('workshop/main', views.WorkshopMain.as_view()),
    path('section/main', views.SectionMain.as_view()),
    path('product/main', views.ProductMain.as_view()),
]
