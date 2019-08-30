from django.urls import path
from . import views_hzy, views_jcj

urlpatterns = [
    path('data/input/sanding_sawing', views_hzy.SandingSawing.as_view()),
    path('data/input/press_operation', views_hzy.PressOperation.as_view()),
    path('data/input/material_consumption', views_hzy.MaterialConsumption.as_view()),
    path('data/input/press_records', views_jcj.DataInputPressRecords.as_view()),
    path('data/input/material_records', views_jcj.DataInputMaterialRecords.as_view()),
    path('data/input/shutdown_records', views_jcj.DataInputShutdownRecords.as_view()),
    path('board/shutdown_stats', views_jcj.BoardShutdownStats.as_view()),
]
