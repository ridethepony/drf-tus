leukeleu-drf-tus
================

A [tus](https://tus.io) library for [Django REST Framework](https://www.django-rest-framework.org).


Quickstart
----------

Install drf-tus:

    pip install leukeleu-drf-tus

Add it to your `INSTALLED_APPS`:

    INSTALLED_APPS = (
        ...
        'rest_framework_tus',
        ...
    )

Add the middleware to `MIDDLEWARE`:

    MIDDLEWARE = (
        ...
        'rest_framework_tus.middleware.TusMiddleware',
        ...
    )

Add drf-tus's URL patterns:

    urlpatterns = [
        ...
        path('', include('rest_framework_tus.urls', namespace='rest_framework_tus')),
        ...
    ]


Features
--------

This library implements the following TUS API v1.0.0 protocols:

* [Core Protocol](http://tus.io/protocols/resumable-upload.html#core-protocol)
* [Creation Protocol](http://tus.io/protocols/resumable-upload.html#creation)
* [Expiration Protocol](http://tus.io/protocols/resumable-upload.html#expiration)
* [Checksum Protocol](http://tus.io/protocols/resumable-upload.html#checksum)
* [Termination Protocol](http://tus.io/protocols/resumable-upload.html#termination)


Running Tests
-------------

Does the code actually work?

    docker compose exec python make coveragetest
