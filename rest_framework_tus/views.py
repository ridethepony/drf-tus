import json
import logging

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import mixins, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.metadata import BaseMetadata
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from rest_framework_tus.parsers import TusUploadStreamParser

from . import constants
from . import settings as tus_settings
from . import (signals, states, tus_api_checksum_algorithms, tus_api_extensions, tus_api_version,
               tus_api_version_supported)
from .exceptions import Conflict
from .models import get_upload_model
from .serializers import UploadSerializer
from .utils import checksum_matches, encode_upload_metadata

logger = logging.getLogger(__name__)


def has_required_tus_header(request):
    return hasattr(request, constants.TUS_RESUMABLE_FIELD_NAME)


def add_expiry_header(upload, headers):
    if upload.expires:
        headers['Upload-Expires'] = upload.expires.strftime('%a, %d %b %Y %H:%M:%S %Z')


class UploadMetadata(BaseMetadata):
    def determine_metadata(self, request, view):
        return {
            'Tus-Resumable': tus_api_version,
            'Tus-Version': ','.join(tus_api_version_supported),
            'Tus-Extension': ','.join(tus_api_extensions),
            'Tus-Max-Size': getattr(view, 'max_file_size', tus_settings.TUS_MAX_FILE_SIZE),
            'Tus-Checksum-Algorithm': ','.join(tus_api_checksum_algorithms),
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'PATCH,HEAD,GET,POST,OPTIONS',
            'Access-Control-Expose-Headers': 'Tus-Resumable,upload-length,upload-metadata,Location,Upload-Offset',
            'Access-Control-Allow-Headers':
                'Tus-Resumable,upload-length,upload-metadata,Location,Upload-Offset,content-type',
            'Cache-Control': 'no-store'
        }


class TusHeadMixin:
    def info(self, request, *args, **kwargs):
        # Validate tus header
        if not has_required_tus_header(request):
            return Response('Missing "{}" header.'.format('Tus-Resumable'), status=status.HTTP_400_BAD_REQUEST)

        try:
            upload = self.get_object()
        except Http404:
            # Instead of simply trowing a 404, we need to add a cache-control header to the response
            return Response('Not found.', headers={'Cache-Control': 'no-store'}, status=status.HTTP_404_NOT_FOUND)

        headers = {
            'Upload-Offset': upload.upload_offset,
            'Cache-Control': 'no-store'
        }

        if upload.upload_length >= 0:
            headers['Upload-Length'] = upload.upload_length

        if upload.upload_metadata:
            headers['Upload-Metadata'] = encode_upload_metadata(json.loads(upload.upload_metadata))

        # Add upload expiry to headers
        add_expiry_header(upload, headers)

        try:
            assert upload.get_or_create_temporary_file()
        except AssertionError:
            del headers['Upload-Offset']
            return Response(headers=headers, status=status.HTTP_410_GONE)

        return Response(headers=headers, status=status.HTTP_200_OK)


class TusCreateMixin(mixins.CreateModelMixin):
    def create(self, request, *args, **kwargs):
        # Validate tus header
        if not has_required_tus_header(request):
            return Response('Missing "{}" header.'.format('Tus-Resumable'), status=status.HTTP_400_BAD_REQUEST)

        # Get file size from request
        upload_length = getattr(request, constants.UPLOAD_LENGTH_FIELD_NAME, None)

        # Validate upload_length
        max_file_size = getattr(self, 'max_file_size', tus_settings.TUS_MAX_FILE_SIZE)

        if upload_length is None:  # We want to allow 0
            # If upload_length is not given, we expect the defer header!
            if getattr(request, constants.UPLOAD_DEFER_LENGTH_FIELD_NAME, -1) != 1:
                return Response('Missing "{Upload-Defer-Length}" header.', status=status.HTTP_400_BAD_REQUEST)
        else:
            if upload_length > max_file_size:
                return Response('Invalid "Upload-Length". Maximum value: {}.'.format(tus_settings.TUS_MAX_FILE_SIZE),
                                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # Get metadata from request
        upload_metadata = getattr(request, constants.UPLOAD_METADATA_FIELD_NAME, {})

        # Get data from metadata
        filename = upload_metadata.get(tus_settings.TUS_FILENAME_METADATA_FIELD, '')

        # Validate the filename
        filename = self.validate_filename(filename)

        # Retrieve serializer
        serializer = self.get_serializer(data={
            'upload_length': upload_length,
            'upload_metadata': json.dumps(upload_metadata),
            'filename': filename,
        })

        # Validate serializer
        serializer.is_valid(raise_exception=True)

        # Create upload object
        self.perform_create(serializer)

        # Get upload from serializer
        upload = serializer.instance

        # Prepare response headers
        headers = self.get_success_headers(serializer.data)

        # Maybe we're auto-expiring the upload...
        if tus_settings.TUS_UPLOAD_EXPIRES is not None:
            upload.expires = timezone.now() + tus_settings.TUS_UPLOAD_EXPIRES
            upload.save()

        # Add upload expiry to headers
        add_expiry_header(upload, headers)

        # Validate headers
        headers = self.validate_success_headers(headers)

        # By default, don't include a response body
        if not tus_settings.TUS_RESPONSE_BODY_ENABLED:
            return Response(headers=headers, status=status.HTTP_201_CREATED)

        return Response(serializer.data, headers=headers, status=status.HTTP_201_CREATED)

    def get_success_headers(self, data):
        try:
            return {'Location': reverse('rest_framework_tus:api:upload-detail', kwargs={'guid': data['guid']})}
        except (TypeError, KeyError):
            return {}

    def validate_success_headers(self, headers):
        """
        Handler to validate success headers before the response is sent. Should throw a ValidationError if
          something's off.

        :param dict headers:
        :return dict: The headers
        """
        return headers

    def validate_filename(self, filename):
        """
        Handler to validate the filename. Should throw a ValidationError if something's off.

        :param six.text_type filename:
        :return six.text_type: The filename
        """
        return filename


class TusPatchMixin(mixins.UpdateModelMixin):
    def get_chunk(self, request):
        if TusUploadStreamParser in self.parser_classes:
            if 'chunk' in request.data:
                return request.data['chunk']
        return request.body

    def validate_chunk(self, offset, chunk_bytes):
        """
        Handler to validate chunks before they are actually written to the buffer file. Should throw a ValidationError
          if something's off.

        :param int offset:
        :param six.binary_type chunk_bytes:
        :return six.binary_type: The chunk_bytes
        """
        return chunk_bytes

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed

    def partial_update(self, request, *args, **kwargs):
        # Validate tus header
        if not has_required_tus_header(request):
            return Response('Missing "{}" header.'.format('Tus-Resumable'), status=status.HTTP_400_BAD_REQUEST)

        # Validate content type
        if not self._is_valid_content_type(request):
            return Response('Invalid value for "Content-Type" header: {}. Expected "{}".'.format(
                request.META['CONTENT_TYPE'], TusUploadStreamParser.media_type), status=status.HTTP_400_BAD_REQUEST)

        # Retrieve object
        upload = self.get_object()

        # Get upload_offset
        upload_offset = getattr(request, constants.UPLOAD_OFFSET_NAME)

        # Validate upload_offset
        if upload_offset != upload.upload_offset:
            raise Conflict

        # Make sure there is a tempfile for the upload
        assert upload.get_or_create_temporary_file()

        # Change state
        if upload.state == states.INITIAL:
            upload.start_receiving()
            upload.save()

        # Get chunk from request
        chunk_bytes = self.get_chunk(request)

        # Check for data
        if not chunk_bytes:
            return Response('No data.', status=status.HTTP_400_BAD_REQUEST)

        # Check checksum  (http://tus.io/protocols/resumable-upload.html#checksum)
        upload_checksum = getattr(request, constants.UPLOAD_CHECKSUM_FIELD_NAME, None)
        if upload_checksum is not None:
            if upload_checksum[0] not in tus_api_checksum_algorithms:
                return Response('Unsupported Checksum Algorithm: {}.'.format(
                    upload_checksum[0]), status=status.HTTP_400_BAD_REQUEST)
            elif not checksum_matches(upload_checksum[0], upload_checksum[1], chunk_bytes):
                return Response('Checksum Mismatch.', status=460)

        # Run chunk validator
        chunk_bytes = self.validate_chunk(upload_offset, chunk_bytes)

        # Check for data
        if not chunk_bytes:
            return Response('No data. Make sure "validate_chunk" returns data.', status=status.HTTP_400_BAD_REQUEST)

        # Write file
        chunk_size = int(request.META.get('CONTENT_LENGTH', 102400))
        try:
            upload.write_data(chunk_bytes, chunk_size)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        headers = {
            'Upload-Offset': upload.upload_offset,
        }

        if upload.upload_length == upload.upload_offset:
            # Trigger signal
            signals.received.send(sender=upload.__class__, instance=upload)

        # Add upload expiry to headers
        add_expiry_header(upload, headers)

        # By default, don't include a response body
        if not tus_settings.TUS_RESPONSE_BODY_ENABLED:
            return Response(headers=headers, status=status.HTTP_204_NO_CONTENT)

        # Create serializer
        serializer = self.get_serializer(instance=upload)

        return Response(serializer.data, headers=headers, status=status.HTTP_204_NO_CONTENT)

    def _is_valid_content_type(self, request):
        return request.META['CONTENT_TYPE'] == TusUploadStreamParser.media_type


class TusTerminateMixin(mixins.DestroyModelMixin):
    def destroy(self, request, *args, **kwargs):
        # Retrieve object
        upload = self.get_object()

        # When the upload is still saving, we're not able to destroy the entity
        if upload.state == states.SAVING:
            return Response(_('Unable to terminate upload while in state "{}".'.format(upload.state)),
                            status=status.HTTP_409_CONFLICT)

        # Destroy object
        self.perform_destroy(upload)

        return Response(status=status.HTTP_204_NO_CONTENT)


class UploadViewSet(TusCreateMixin,
                    TusPatchMixin,
                    TusHeadMixin,
                    TusTerminateMixin,
                    GenericViewSet):
    serializer_class = UploadSerializer
    metadata_class = UploadMetadata
    lookup_field = 'guid'
    lookup_value_regex = '[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}'
    parser_classes = [TusUploadStreamParser]

    def get_queryset(self):
        return get_upload_model().objects.all()
