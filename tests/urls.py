from django.conf.urls import include, url

from rest_framework_tus.urls import urlpatterns as rest_framework_tus_urls

urlpatterns = [
    url(r'^', include(rest_framework_tus_urls, namespace='rest_framework_tus')),
]
