from django.urls import path
from .views import health_check, upload_xml, download_xml


urlpatterns = [
    path("health_check/", health_check, name="health_check"),
    path("upload/xml/", upload_xml, name="upload_xml"),
    path("xml/<int:file_id>/", download_xml, name="download_xml"),
]
