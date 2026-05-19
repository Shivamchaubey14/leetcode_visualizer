from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('problem/<slug:slug>/', views.detail, name='detail'),
    path('api/run/<slug:slug>/', views.run_code, name='run_code'),
    path('api/steps/<slug:slug>/', views.get_steps, name='get_steps'),
]