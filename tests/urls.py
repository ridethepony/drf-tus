from django.urls import include, path

from rest_framework_tus.urls import urlpatterns as rest_framework_tus_urls

urlpatterns = [
    path('', include((rest_framework_tus_urls, 'rest_framework_tus_tests'), namespace='rest_framework_tus')),
]
