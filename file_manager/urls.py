from django.urls import path
from .views import health_check, upload_xml


urlpatterns = [
    path("health_check/", health_check, name="health_check"),
    path("upload/xml/", upload_xml, name="upload_xml"),
]
