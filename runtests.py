#!/usr/bin/env python
import argparse
import os
import sys

import django

from django.conf import settings
from django.test.utils import get_runner


def runtests():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    django.setup()
    test_runner = get_runner(settings)
    failures = test_runner().run_tests(args.tests)
    sys.exit(bool(failures))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run tests')
    parser.add_argument(
        dest='tests',
        metavar='testcase',
        nargs='*',
        default=['tests'],
        help='an optional list of test cases to run'
    )

    args = parser.parse_args()
    runtests()
