from django.urls import path
from . import views

app_name = "checker"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("check-single/", views.check_single_view, name="check_single"),
    path("upload-txt/", views.upload_txt_view, name="upload_txt"),
    path("start-builtin/", views.start_builtin_scan_view, name="start_builtin"),
    path("stop-scan/", views.stop_scan_view, name="stop_scan"),
    path("clear-cache/", views.clear_cache_view, name="clear_cache"),
    path("download/<str:file_kind>/", views.download_txt_view, name="download_txt"),
    path("api/status/", views.api_status_view, name="api_status"),
    path("telegram-login/", views.telegram_auth_view, name="telegram_auth"),
]
