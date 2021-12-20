from django.urls import path
from .views import HomeView
from .views import process_request

app_name = "checker"

urlpatterns = [
    path("", HomeView.as_view(), name='home-view'),
    path("result/", process_request, name="process")
]
