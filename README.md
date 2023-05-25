leukeleu-drf-tus
================

A Tus (tus.io) library for Django Rest Framework

Quickstart
----------

Install drf-tus:

    pip install drf-tus

Add it to your `INSTALLED_APPS`:

    INSTALLED_APPS = (
        ...
        'rest_framework_tus',
        ...
    )

Add the middleware to `MIDDLEWARE` (or `MIDDLEWARE_CLASSES` for Django < 1.10)

    MIDDLEWARE = (
        ...
        'rest_framework_tus.middleware.TusMiddleware',
        ...
    )

Add drf-tus's URL patterns:

    urlpatterns = [
        ...
        url(r'^', include('rest_framework_tus.urls', namespace='rest_framework_tus')),
        ...
    ]

Features
--------

This library implements the following TUS API v1.0.0 protocols:

* Core Protocol (http://tus.io/protocols/resumable-upload.html#core-protocol)
* Creation Protocol (http://tus.io/protocols/resumable-upload.html#creation)
* Expiration Protocol (http://tus.io/protocols/resumable-upload.html#expiration)
* Checksum Protocol (http://tus.io/protocols/resumable-upload.html#checksum)
* Termination Protocol (http://tus.io/protocols/resumable-upload.html#termination)


Running Tests
-------------

Does the code actually work?

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox
