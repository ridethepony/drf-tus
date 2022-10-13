from django.urls import include, re_path

from rest_framework_tus.urls import urlpatterns as rest_framework_tus_urls

urlpatterns = [
    re_path(r'^', include((rest_framework_tus_urls, 'rest_framework_tus_tests'), namespace='rest_framework_tus')),
]
