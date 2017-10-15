import json
import logging
from datetime import datetime
from unicodedata import normalize
import itertools

from fpdf import FPDF

from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.mail import send_mail
# from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import detail_route, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser

from common.views import (CsrfExemptSessionAuthentication,
                          StandardResultsSetPagination)
from .models import Request, FileRequest
from .serializers import RequestSerializer, RequestFileSerializer

User = get_user_model()
logger = logging.getLogger('db')


def handle_request_id_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except ValueError:
            return Response({
                'success': False,
                'message': 'Id is not provided.',
            }, 400)

        except Request.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Request does not exist.',
            }, 404)

    return wrapper


class PDF(FPDF):
    def __init__(self, title='Title', font='Arial'):
        self.title = title
        self.font = font
        super().__init__()

    def header(self):
        self.set_font(self.font, style='B', size=14)  # Arial bold 15
        self.cell(0, 10, self.title, align='C')       # Title
        self.ln(10)                                   # Line break

    def footer(self):
        self.set_y(-15)  # Position at 1.5 cm from bottom
        self.set_font(self.font, size=8)  # Arial 8
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + ' of {nb}', 0, 0, 'C')

    def info_row(self, title, value):
        self.set_font(self.font, style='B', size=11)
        self.cell(35, 10, title + ':')
        self.set_font(self.font, size=11)
        self.cell(0, 10, value)
        self.ln(6)

    def multi_info_row(self, title, value):
        self.set_font(self.font, style='B', size=11)
        self.ln(3)
        self.cell(35, 4, title + ':')
        self.set_font(self.font, size=11)
        self.multi_cell(0, 5, value)
        self.ln(6)

    def table_row(self, index, name, barcode, type, depth, bold=False):
        if bold:
            self.set_font(self.font, style='B', size=11)
        else:
            self.set_font(self.font, size=11)
        self.cell(10, 10, str(index))
        self.cell(60, 10, name)
        self.cell(40, 10, barcode)
        self.cell(35, 10, type)
        self.cell(0, 10, str(depth))
        self.ln(6)


@login_required
def get_files(request):
    """ Get the list of files for the given request id. """
    file_ids = json.loads(request.GET.get('file_ids', '[]'))
    error = ''
    data = []

    try:
        files = [f for f in FileRequest.objects.all() if f.id in file_ids]
        data = [
            {
                'id': file.id,
                'name': file.name,
                'size': file.file.size,
                'path': settings.MEDIA_URL + file.file.name,
            }
            for file in files
        ]

    except Exception as e:
        error = 'Could not get the attached files.'
        logger.exception(e)

    return JsonResponse({'success': not error, 'error': error, 'data': data})


@csrf_exempt
@login_required
def upload_files(request):
    """ Upload request files. """
    file_ids = []
    error = ''

    if request.method == 'POST' and any(request.FILES):
        try:
            for file in request.FILES.getlist('files'):
                f = FileRequest(name=file.name, file=file)
                f.save()
                file_ids.append(f.id)

        except Exception as e:
            error = 'Could not upload the files.'
            logger.exception(e)

    return JsonResponse({
        'success': not error,
        'error': error,
        'fileIds': file_ids
    })


class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer
    pagination_class = StandardResultsSetPagination
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get_queryset(self):
        queryset = Request.objects.prefetch_related(
            'user', 'libraries', 'samples', 'files'
        ).order_by('-create_time')

        # If a search query is given
        search_query = self.request.query_params.get('query', None)
        if search_query:
            # TODO: implements this
            # fields = [f for f in Request._meta.fields
            #           if isinstance(f, CharField) or isinstance(f, TextField)]
            # queries = [Q(**{f.name: search_query}) for f in fields]
            # qs = Q()
            # for query in queries:
            #     qs = qs | query
            # queryset = queryset.filter(qs)
            pass

        if self.request.user.is_staff:
            # Show only those Requests, whose libraries and samples
            # haven't reached status 6 yet
            # TODO: find a way to hide requests
            # queryset = [x for x in queryset if x.statuses.count(6) == 0]
            pass
        else:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def list(self, request):
        """
        * GET /api/requests/
            Get the list of requests for a given page number.

        :type page: int
        :param page: page number (`optional`). If omitted, equals 1 by default.

        :rtype: dict
        :returns: a list of requests.
            For example::

                {
                    "count": 1,
                    "next": null,
                    "previous": null,
                    "results": [
                        {
                            "pk": 1,
                            "name": "Request 1",
                            "user": 1,
                            "user_full_name": "Admin",
                            "create_time": "2017-10-10T20:10:33.388942Z",
                            "description": "some description",
                            "total_sequencing_depth": 10,
                            "files": [],
                            "restrict_permissions": false,
                            "deep_seq_request_name": "",
                            "deep_seq_request_path": ""
                        }
                    ]
                }
        """
        queryset = self.get_queryset()
        # page = self.paginate_queryset(queryset)

        try:
            page = self.paginate_queryset(queryset)
        except NotFound:
            page = None

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        * POST /api/requests/
            Create a request.

        :type description: str
        :param description: request description

        :type records: array
        :param records: list of libraries and samples.
            For example::

                [
                    {
                        "pk": 1,
                        "record_type": "Library"
                    },
                    {
                        "pk": 2,
                        "record_type": "Sample"
                    }
                ]

        :type files: array
        :param files: list of attached files.
            For example::

                [

                ]

        :rtype: dict
        :returns: the confirmation of success or an error message

        .. note::

            All ``POST`` data should be put into a dict with the key ``data``.
            For example::

                {
                    "data": {
                        "description": "",
                        "records": [],
                        "files": []
                    }
                }
        """
        post_data = self._get_post_data(request)
        post_data.update({'user': request.user.pk})
        serializer = self.serializer_class(data=post_data)

        if serializer.is_valid():
            serializer.save()
            return Response({'success': True}, 201)

        else:
            return Response({
                'success': False,
                'message': 'Invalid payload.',
                'errors': serializer.errors,
            }, 400)

    @detail_route(methods=['post'])
    def edit(self, request, pk=None):
        """
        * POST /api/requests/{pk}/edit/
            Update request with a given id.

        :type pk: int
        :param pk: request id

        :type description: str
        :param description: request description

        :type records: array
        :param records: list of libraries and samples.
            For example::

                [
                    {
                        "pk": 1,
                        "record_type": "Library"
                    },
                    {
                        "pk": 2,
                        "record_type": "Sample"
                    }
                ]

        :type files: array
        :param files: list of attached files.
            For example::

                [

                ]

        :rtype: dict
        :returns: the confirmation of success or an error message

        .. note::

            All ``POST`` data should be put into a dict with the key ``data``.
            For example::

                {
                    "data": {
                        "pk": 1,
                        "description": "",
                        "records": [],
                        "files": []
                    }
                }
        """
        instance = self.get_object()
        post_data = self._get_post_data(request)
        post_data.update({'user': instance.user.pk})

        serializer = self.get_serializer(data=post_data, instance=instance)

        if serializer.is_valid():
            serializer.save()
            return Response({'success': True})

        else:
            return Response({
                'success': False,
                'message': 'Invalid payload.',
                'errors': serializer.errors,
            }, 400)

    @detail_route(methods=['post'])
    def samples_submitted(self, request, pk=None):
        """
        * POST /api/requests/{pk}/samples_submitted/
            Update the value ``samples_submitted`` of a request
            with a given id.

        :type pk: int
        :param pk: request id

        :type result: bool
        :param result: value of ``samples_submitted``

        :rtype: dict
        :returns: the confirmation of success or an error message
        """
        instance = self.get_object()
        post_data = self._get_post_data(request)
        instance.samples_submitted = post_data['result']
        instance.save(update_fields=['samples_submitted'])
        return Response({'success': True})

    @detail_route(methods=['get'])
    def get_records(self, request, pk=None):
        """
        * GET /api/requests/{pk}/get_records/
            Get the list of submitted libraries and samples for a request
            with a given id.

        :type pk: int
        :param pk: request id

        :rtype: list of dicts
        :returns: the list of libraries and samples.
            For example::

                [
                    {
                        "pk": 1,
                        "record_type": "Sample",
                        "name": "Sample",
                        "barcode": "17S000001",
                        "is_converted": false
                    }
                ]
        """
        instance = self.get_object()
        data = [{
            'pk': obj.pk,
            'record_type': obj.__class__.__name__,
            'name': obj.name,
            'barcode': obj.barcode,
            'is_converted': True
            if hasattr(obj, 'is_converted') and obj.is_converted else False,
        } for obj in instance.records]

        data = sorted(data, key=lambda x: x['barcode'][3:])
        return Response(data)

    @detail_route(methods=['get'])
    def get_files(self, request, pk=None):
        """
        * GET /api/requests/{pk}/get_files/
            Get the list of attached files for a request with a given id.

        :type pk: int
        :param pk: request id

        :rtype: list of dicts
        :returns: the list of libraries and samples.
            For example::

                [
                    {
                        "id": 1,
                        "name": "image.png",
                        "size": 133234,
                        "path": "/media/request_files/2017/10/10/image.png"
                    }
                ]
        """
        instance = self.get_object()
        files = instance.files.all().order_by('name')
        serializer = RequestFileSerializer(files, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def download_deep_sequencing_request(self, request, pk=None):
        """
        * GET /api/requests/{pk}/download_deep_sequencing_request/
            Generate a deep sequencing request form in PDF for a request
            with a given id.

        :type pk: int
        :param pk: request id

        :rtype: file
        :returns: a generated PDF file.
        """
        instance = self.get_object()
        user = instance.user
        organization = user.organization.name if user.organization else ''
        cost_unit = ', '.join(sorted(
            user.cost_unit.values_list('name', flat=True)
        ))
        objects = list(itertools.chain(
            instance.samples.all(), instance.libraries.all()
        ))
        records = [{
            'name': obj.name,
            'type': obj.__class__.__name__,
            'barcode': obj.barcode,
            'depth': obj.sequencing_depth,
        } for obj in objects]
        records = sorted(records, key=lambda x: x['barcode'][3:])

        pdf = PDF('Deep Sequencing Request')
        pdf.set_draw_color(217, 217, 217)
        pdf.alias_nb_pages()
        pdf.add_page()

        # Deep Sequencing Request info
        pdf.info_row('Request Name', instance.name)
        pdf.info_row('Date', datetime.now().strftime('%d.%m.%Y'))
        pdf.info_row('User', user.get_full_name())
        pdf.info_row('Phone', user.phone if user.phone else '')
        pdf.info_row('Email', user.email)
        pdf.info_row('Organization', organization)
        pdf.info_row('Cost Unit(s)', cost_unit)
        pdf.multi_info_row('Description', instance.description)

        y = pdf.get_y()
        pdf.line(pdf.l_margin + 1, y, pdf.fw - pdf.r_margin - 1, y)

        # List of libraries/samples
        heading = 'List of libraries/samples to be submitted for sequencing'
        pdf.set_font('Arial', style='B', size=13)
        pdf.ln(5)
        pdf.cell(0, 10, heading, align='C')
        pdf.ln(10)

        pdf.table_row('#', 'Name', 'Barcode', 'Type',
                      'Sequencing Depth (M)', True)

        for i, record in enumerate(records):
            pdf.table_row(i + 1, record['name'], record['barcode'],
                          record['type'], record['depth'])

        pdf.ln(10)
        y = pdf.get_y()
        pdf.line(pdf.l_margin + 1, y, pdf.fw - pdf.r_margin - 1, y)
        pdf.ln(30)

        # Ensure there is enough space for the signature
        if pdf.get_y() > 265:
            pdf.add_page()
            pdf.ln(20)

        # Signature
        pdf.set_draw_color(0, 0, 0)
        y = pdf.get_y()
        x1_date = pdf.fw / 2
        x2_date = x1_date + 45
        x1_signature = x2_date + 5
        x2_signature = pdf.fw - pdf.r_margin - 1
        pdf.line(x1_date, y, x2_date, y)
        pdf.line(x1_signature, y, x2_signature, y)

        pdf.set_x(x1_date + (x2_date - x1_date) / 2 - 6)
        pdf.cell(12, 10, '(Date)')
        pdf.set_x(x1_signature + 2)
        pdf.cell(0, 10, '(Principal Investigator)')

        pdf = pdf.output(dest='S').encode('latin-1')

        # Generate response
        request_name = normalize(
            'NFKD', instance.name
        ).encode('ASCII', 'ignore').decode('utf-8')
        f_name = request_name + '_Deep_Sequencing_Request.pdf'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s"' % f_name

        return response

    @detail_route(methods=['post'])
    def upload_deep_sequencing_request(self, request, pk=None):
        """
        * POST /api/requests/{pk}/upload_deep_sequencing_request/
            Upload a deep sequencing request for a request with a given id.

        :type pk: int
        :param pk: request id

        :rtype: dict
        :returns: a dict with the uploaded file's details.
            For example::

                {
                    "success": true,
                    "name": "ds.pdf",
                    "path": "/media/deep_sequencing_requests/2017/10/10/ds.pdf"
                }
        """
        instance = self.get_object()

        if not any(request.FILES):
            return JsonResponse({
                'success': False,
                'message': 'File is missing.'
            }, status=400)

        instance.deep_seq_request = request.FILES.get('file')
        instance.save()

        file_name = instance.deep_seq_request.name.split('/')[-1]
        file_path = settings.MEDIA_URL + instance.deep_seq_request.name

        instance.libraries.all().update(status=1)
        instance.samples.all().update(status=1)

        return JsonResponse({
             'success': True,
             'name': file_name,
             'path': file_path
        })

    @detail_route(methods=['post'])
    @permission_classes((IsAdminUser))
    def send_email(self, request, pk=None):
        """ Send an email to the user. """
        error = ''

        instance = self.get_object()
        subject = request.data.get('subject', '')
        message = request.data.get('message', '')
        include_failed_records = json.loads(request.POST.get(
            'include_failed_records', 'false'))
        records = []

        # TODO: check if it's possible to send emails at all

        try:
            if subject == '' or message == '':
                raise ValueError('Email subject and/or message is missing.')

            if include_failed_records:
                records = list(instance.libraries.filter(status=-1)) + \
                    list(instance.samples.filter(status=-1))
                records = sorted(records, key=lambda x: x.barcode[3:])

            send_mail(
                subject=subject,
                message='',
                html_message=render_to_string('email.html', {
                    'full_name': instance.user.get_full_name(),
                    'message': message,
                    'records': records,
                }),
                # from_email=settings.SERVER_EMAIL,
                from_email='deepseq@ie-freiburg.mpg.de',
                recipient_list=[instance.user.email],
            )

        except Exception as e:
            error = str(e)
            logger.exception(e)

        return JsonResponse({'success': not error, 'error': error})

    def _get_post_data(self, request):
        post_data = {}
        if request.is_ajax():
            post_data = request.data.get('data', {})
            if isinstance(post_data, str):
                post_data = json.loads(post_data)
        else:
            post_data = json.loads(request.data.get('data', '{}'))
        return post_data
