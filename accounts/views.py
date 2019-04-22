# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import dateutil.parser
import json
import random
import string
import pytz
from dateutil.tz import tzoffset
from django.contrib.auth import login as auth_login, REDIRECT_FIELD_NAME, logout as auth_logout
# from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import deprecate_current_app
from django.db.models import Q
import datetime
from django.http import HttpResponse
from django.shortcuts import redirect

from task_scheduler.settings import TECHNICIAN_DEFAULT_ADDRESS

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
from google_auth_oauthlib.flow import InstalledAppFlow
# Create your views here.
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
# from django.utils.http import is_safe_url
from django.views.decorators.cache import never_cache
# from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from accounts.calender_api import get_calender_events, get_free_times, get_current_address, get_current_address_date
from accounts.distance_api import get_distance_n_duration
from accounts.forms import TechnicianAdd, CustomerAdd
from accounts.models import UserDetails, Role
from task_scheduler import settings

utc = pytz.UTC


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):

        context = super(DashboardView, self).get_context_data(**kwargs)

        if self.request.user.user_details.role.role_name == 'Admin':
            context['users_list'] = UserDetails.objects.filter(~Q(role__role_name__in=['Customer']))
        else:
            context['users_list'] = UserDetails.objects.filter(~Q(role__role_name__in=['Admin', 'Technician']))
        return context

    def post(self, request, *args, **kwargs):
        """

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        import datetime
        import pytz
        utc = pytz.UTC
        response = {}
        if request.POST.get('type') == 'assign_job':
            tech = UserDetails.objects.filter(role__role_name='Technician').first()
            from_time = request.POST.get('from_time')
            end_time = request.POST.get('end_time')
            from_time = datetime.datetime.strptime(from_time, "%d/%m/%Y %H:%M")
            end_time = datetime.datetime.strptime(end_time, "%d/%m/%Y %H:%M")
            schedule_list = tech.techinican.all()
            is_scheduled = False
            message = ''
            status = False

            response['message'] = message
            response['status'] = status
        else:
            UserDetails.objects.get(id=request.POST.get('id')).delete()
            response['message'] = "success"
        return HttpResponse(json.dumps(response), content_type="application/json")


class TechnicianView(TemplateView):
    template_name = 'technicians/technicians-list.html'

    def get_context_data(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        context = super(TechnicianView, self).get_context_data(**kwargs)
        context['users_list'] = UserDetails.objects.filter(role__role_name='Technician')
        # SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        # from google_auth_oauthlib.flow import InstalledAppFlow
        # flow = InstalledAppFlow.from_client_secrets_file(
        #     UserDetails.objects.filter(role__role_name='Technician')[1].credential.path, SCOPES)
        #
        # url = flow.get_auth_url()
        # test = UserDetails.objects.filter(role__role_name='Technician')[0]
        # test.auth_url = url
        # test.save()
        return context


class AddTechnicianView(TemplateView):
    template_name = 'technicians/add-technician.html'

    def get_context_data(self, **kwargs):
        context = super(AddTechnicianView, self).get_context_data(**kwargs)
        context['technician_form'] = TechnicianAdd()
        return context

    def post(self, request, *args, **kwargs):
        context = {}
        technician_form = TechnicianAdd(request.POST)
        if technician_form.is_valid():
            user_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            user = User.objects.create(first_name=request.POST.get('first_name'),
                                       last_name=request.POST.get('last_name'),
                                       email=request.POST.get('email'), username=user_name)

            user_details = UserDetails.objects.create(user=user, address=request.POST.get('address'),
                                                      phone_number=request.POST.get('phone_number'),
                                                      email_password=request.POST.get('email_password'),
                                                      credential=request.FILES['credential'],
                                                      role=Role.objects.get(role_name='Technician'))

            flow = InstalledAppFlow.from_client_secrets_file(
                user_details.credential.path, SCOPES)

            url = flow.get_auth_url()
            user_details.auth_url = url.replace("Please visit this URL to authorize this application: ", "")
            user_details.save()
            return redirect('/manage-technicians/')
        context['technician_form'] = technician_form
        return TemplateResponse(request, self.template_name, context)


class CustomerView(TemplateView):
    template_name = 'customers/customer-list.html'

    def get_context_data(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        context = super(CustomerView, self).get_context_data(**kwargs)
        context['users_list'] = UserDetails.objects.filter(role__role_name='Customer')
        return context


class TechnicianAvailability(TemplateView):
    template_name = 'technicians/technician_availability.html'

    def get_context_data(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        user_detail = UserDetails.objects.get(id=kwargs.get('technician_pk'))

        context = super(TechnicianAvailability, self).get_context_data(**kwargs)
        users_list = []
        customer = UserDetails.objects.get(id=kwargs.get('technician_pk'))
        events = get_calender_events(customer)
        # print(events)
        # events = [{u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-07T04:00:00+05:30'}, u'created': u'2019-04-07T06:40:51.000Z', u'iCalUID': u'16plqqbhndoet48rmuqk5fpbsn@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=MTZwbHFxYmhuZG9ldDQ4cm11cWs1ZnBic24gYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-07T06:40:51.196Z', u'summary': u'BREAK', u'start': {u'dateTime': u'2019-04-07T03:00:00+05:30'}, u'etag': u'"3109238502392000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'16plqqbhndoet48rmuqk5fpbsn'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-07T10:45:00+05:30'}, u'created': u'2019-04-07T06:48:12.000Z', u'iCalUID': u'3ocgg2r67i9jjlulqiidi7m358@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=M29jZ2cycjY3aTlqamx1bHFpaWRpN20zNTggYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 1, u'updated': u'2019-04-07T07:33:25.096Z', u'summary': u'at karamana', u'start': {u'dateTime': u'2019-04-07T10:15:00+05:30'}, u'etag': u'"3109244810192000"', u'location': u'Karamana, Thiruvananthapuram, Kerala, India', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'3ocgg2r67i9jjlulqiidi7m358'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-07T13:00:00+05:30'}, u'created': u'2019-04-07T06:41:02.000Z', u'iCalUID': u'4l42k182auhtb80li0ogc2i9rq@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=NGw0MmsxODJhdWh0YjgwbGkwb2djMmk5cnEgYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 2, u'updated': u'2019-04-07T07:33:27.952Z', u'summary': u'TEST1', u'start': {u'dateTime': u'2019-04-07T12:00:00+05:30'}, u'etag': u'"3109244815904000"', u'location': u'Sreekariyam, Thiruvananthapuram, Kerala, India', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'4l42k182auhtb80li0ogc2i9rq'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-09T01:30:00+05:30'}, u'created': u'2019-04-02T20:56:32.000Z', u'iCalUID': u'0hgb8h3vge141tui51u0h7j86r@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=MGhnYjhoM3ZnZTE0MXR1aTUxdTBoN2o4NnIgYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-02T21:13:12.885Z', u'summary': u'test day 10', u'start': {u'dateTime': u'2019-04-09T00:30:00+05:30'}, u'etag': u'"3108479185770000"', u'location': u'Sreekariyam, Thiruvananthapuram, Kerala, India', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'0hgb8h3vge141tui51u0h7j86r'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-09T10:30:00+05:30'}, u'created': u'2019-04-04T17:55:34.000Z', u'iCalUID': u'5kk2kool8coefgd2mnl5fhpbuc@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=NWtrMmtvb2w4Y29lZmdkMm1ubDVmaHBidWMgYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-04T17:55:34.229Z', u'summary': u'wertyu', u'start': {u'dateTime': u'2019-04-09T09:30:00+05:30'}, u'etag': u'"3108801068458000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'5kk2kool8coefgd2mnl5fhpbuc'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-09T15:30:00+05:30'}, u'created': u'2019-04-04T17:55:37.000Z', u'iCalUID': u'7qq636q7s4v95b5pmo58n8poij@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=N3FxNjM2cTdzNHY5NWI1cG1vNThuOHBvaWogYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-04T17:55:37.696Z', u'summary': u'qwertyu', u'start': {u'dateTime': u'2019-04-09T14:30:00+05:30'}, u'etag': u'"3108801075392000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'7qq636q7s4v95b5pmo58n8poij'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-10T08:00:00+05:30'}, u'created': u'2019-04-04T18:18:28.000Z', u'iCalUID': u'1tcf55kgvcn4t358dvkvmq9v8r@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=MXRjZjU1a2d2Y240dDM1OGR2a3ZtcTl2OHIgYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 1, u'updated': u'2019-04-04T18:23:54.408Z', u'summary': u'tr', u'start': {u'dateTime': u'2019-04-10T07:00:00+05:30'}, u'etag': u'"3108804468816000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'1tcf55kgvcn4t358dvkvmq9v8r'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-10T11:00:00+05:30'}, u'created': u'2019-04-04T18:18:36.000Z', u'iCalUID': u'1orpbusrntan37gofad518ajtu@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=MW9ycGJ1c3JudGFuMzdnb2ZhZDUxOGFqdHUgYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-04T18:18:36.930Z', u'summary': u'tr3', u'start': {u'dateTime': u'2019-04-10T10:00:00+05:30'}, u'etag': u'"3108803833860000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'1orpbusrntan37gofad518ajtu'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-10T13:00:00+05:30'}, u'created': u'2019-04-04T18:18:43.000Z', u'iCalUID': u'3hqn5gfge2blk5gu8ieredc6jg@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=M2hxbjVnZmdlMmJsazVndThpZXJlZGM2amcgYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-04T18:18:43.088Z', u'summary': u'tr4', u'start': {u'dateTime': u'2019-04-10T12:00:00+05:30'}, u'etag': u'"3108803846176000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'3hqn5gfge2blk5gu8ieredc6jg'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-10T15:30:00+05:30'}, u'created': u'2019-04-04T18:18:54.000Z', u'iCalUID': u'6cqjupgt6rtul67opr0apicvah@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=NmNxanVwZ3Q2cnR1bDY3b3ByMGFwaWN2YWggYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-04T18:18:54.951Z', u'summary': u'tr5', u'start': {u'dateTime': u'2019-04-10T14:30:00+05:30'}, u'etag': u'"3108803869902000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'6cqjupgt6rtul67opr0apicvah'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-10T17:30:00+05:30'}, u'created': u'2019-04-04T18:19:06.000Z', u'iCalUID': u'2n747n9lus2ajjfg60e5q38cbm@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=Mm43NDduOWx1czJhampmZzYwZTVxMzhjYm0gYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-04T18:19:06.452Z', u'summary': u'tr6', u'start': {u'dateTime': u'2019-04-10T16:30:00+05:30'}, u'etag': u'"3108803892904000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'2n747n9lus2ajjfg60e5q38cbm'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-10T20:00:00+05:30'}, u'created': u'2019-04-04T18:19:11.000Z', u'iCalUID': u'7mc5ng0rsa5o7iveum2uq527vq@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=N21jNW5nMHJzYTVvN2l2ZXVtMnVxNTI3dnEgYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-04T18:19:11.878Z', u'summary': u'tr7', u'start': {u'dateTime': u'2019-04-10T19:00:00+05:30'}, u'etag': u'"3108803903756000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'7mc5ng0rsa5o7iveum2uq527vq'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-10T22:00:00+05:30'}, u'created': u'2019-04-04T18:19:17.000Z', u'iCalUID': u'5gegqblqr9budbprjuh62u54i6@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=NWdlZ3FibHFyOWJ1ZGJwcmp1aDYydTU0aTYgYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-04T18:19:17.655Z', u'summary': u'tr8', u'start': {u'dateTime': u'2019-04-10T21:00:00+05:30'}, u'etag': u'"3108803915310000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'5gegqblqr9budbprjuh62u54i6'}, {u'status': u'confirmed', u'kind': u'calendar#event', u'end': {u'dateTime': u'2019-04-13T01:30:00+05:30'}, u'created': u'2019-04-02T21:01:00.000Z', u'iCalUID': u'10jb83n1u227fhil792q1akoft@google.com', u'reminders': {u'useDefault': True}, u'extendedProperties': {u'private': {u'everyoneDeclinedDismissed': u'-1'}}, u'htmlLink': u'https://www.google.com/calendar/event?eid=MTBqYjgzbjF1MjI3ZmhpbDc5MnExYWtvZnQgYWJoaXRoYUBzcGVyaWNvcm4uY29t', u'sequence': 0, u'updated': u'2019-04-02T21:01:00.336Z', u'summary': u'test 13', u'start': {u'dateTime': u'2019-04-13T00:30:00+05:30'}, u'etag': u'"3108477720672000"', u'organizer': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'creator': {u'self': True, u'email': u'abhitha@spericorn.com'}, u'id': u'10jb83n1u227fhil792q1akoft'}]
        users_list.append({'user': user_detail, 'events': events})
        context['user_detail'] = user_detail
        sorted_events = []
        for event in events:
            # import arrow
            start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
            end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))
            # if arrow.get(start).date() == datetime.now().date():
            # start = datetime.strptime(str(dateutil.parser.parse(start)), '%Y-%m-%d %H:%M:%S+05:30')
            # end = datetime.strptime(str(dateutil.parser.parse(end)), '%Y-%m-%d %H:%M:%S+05:30')
            difference = start.date() - datetime.datetime.now().date()
            if difference.days <= 10:
                sorted_events.append(
                    {'location': event.get('location'), 'summary': event.get('summary'), 'start': start, 'end': end})

        context['events'] = sorted_events
        return context


class EditTechnicianView(TemplateView):
    template_name = 'technicians/add-technician.html'

    def get_context_data(self, **kwargs):
        context = super(EditTechnicianView, self).get_context_data(**kwargs)
        user_details = UserDetails.objects.get(pk=kwargs.get('customer_pk'))
        context['technician_form'] = TechnicianAdd(initial=user_details)
        context['user_detail_id'] = user_details.id
        return context

    def post(self, request, *args, **kwargs):
        context = {}
        customer_form = TechnicianAdd(request.POST)
        if customer_form.is_valid():
            user_details = UserDetails.objects.get(pk=request.POST.get('user_detail_id'))

            user = user_details.user
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.save()
            user_details.address = request.POST.get('address')
            user_details.email_password = request.POST.get('email_password')
            if request.FILES.get('credential'):
                user_details.credential = request.FILES.get('credential')
            user_details.phone_number = request.POST.get('phone_number')
            user_details.save()
            return redirect('/manage-technicians/')
        context['customer_form'] = customer_form
        return TemplateResponse(request, self.template_name, context)


class EditCustomerView(TemplateView):
    template_name = 'customers/add-customer.html'

    def get_context_data(self, **kwargs):
        context = super(EditCustomerView, self).get_context_data(**kwargs)
        user_details = UserDetails.objects.get(pk=kwargs.get('customer_pk'))
        context['technician_form'] = CustomerAdd(initial=user_details)
        context['user_detail_id'] = user_details.id
        return context

    def post(self, request, *args, **kwargs):
        context = {}
        customer_form = CustomerAdd(request.POST)
        if customer_form.is_valid():
            user_details = UserDetails.objects.get(pk=request.POST.get('user_detail_id'))

            user_details.address = request.POST.get('address')
            user_details.time_for_job = request.POST.get('time_for_job')
            user_details.save()
            return redirect('/assign-technician/' + str(user_details.id))
        context['customer_form'] = customer_form
        return TemplateResponse(request, self.template_name, context)


class AddCustomerView(TemplateView):
    template_name = 'customers/add-customer.html'

    def get_context_data(self, **kwargs):
        context = super(AddCustomerView, self).get_context_data(**kwargs)
        context['customer_form'] = TechnicianAdd()
        return context

    def post(self, request, *args, **kwargs):
        context = {}
        customer_form = CustomerAdd(request.POST)
        # if customer_form.is_valid():
        user_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        user = User.objects.create(username=user_name)

        user_details = UserDetails.objects.create(user=user, address=request.POST.get('address'),
                                                  time_for_job=request.POST.get('time_for_job'),
                                                  role=Role.objects.get(role_name='Customer'))
        return redirect('/assign-technician/' + str(user_details.id))
        # context['customer_form'] = customer_form
        # return TemplateResponse(request, self.template_name, context)


class AssignTechnicianView(TemplateView):
    template_name = 'technicians/assign_technician.html'

    def get_context_data(self, **kwargs):
        """

        :param kwargs:
        :return:
        """

        context = super(AssignTechnicianView, self).get_context_data(**kwargs)
        users_list = []

        import datetime
        customer = UserDetails.objects.get(id=kwargs.get('customer_pk'))
        c_date = datetime.datetime.now().date()
        # tstart = datetime.datetime.strptime(str(c_date) + ' 9:00:00', '%Y-%d-%m %H:%M:%S')
        tstart =  datetime.datetime.strptime(str(c_date) + ' 9:00:00', '%Y-%m-%d %H:%M:%S')
        # tstop = datetime.datetime.strptime(str(c_date) + ' 18:00:00', '%Y-%d-%m %H:%M:%S')
        tstop = datetime.datetime.strptime(str(c_date) + ' 18:00:00', '%Y-%m-%d %H:%M:%S')
        for user in UserDetails.objects.filter(role__role_name='Technician'):
            events = free_time = full_free_times = []

            c_date_af_10 = c_date + datetime.timedelta(days=10)

            c_date_af_10 = c_date_af_10.isoformat()
            # eastern = timezone(TIME_ZONE)
            # c_date_af_10 = eastern.localize(
            #     datetime.datetime.strptime(str(c_date_af_10) + ' 18:00:00-04:00', '%Y-%m-%d %H:%M:%S-04:00'))
            try:
                if user.token_pickle:
                    events = get_calender_events(user,event_count=250,timeMax=c_date_af_10)
                    full_free_times, free_time = get_free_times(user,events)
            except Exception as e:
                print(e, ";;;;;")

            sorted_events = []

            # current_address = get_current_address(events, customer)
            # if not current_address:
            #     current_address = TECHNICIAN_DEFAULT_ADDRESS
            count = 1
            from_office_distance_dict = get_distance_n_duration(TECHNICIAN_DEFAULT_ADDRESS, customer.address)
            for event in events:
                try:
                    start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
                    end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))
                    if start.date() >= datetime.datetime.now().date():
                        count += 1
                        sorted_events.append(
                            {'location': event.get('location'), 'summary': event.get('summary'), 'start': start,
                             'end': end})
                except:
                    pass

            # distance_dict = get_distance_n_duration(current_address, customer.address)
            try:
                sorted_free_time = []
                sorted_fullfree_time = []
                filtered_free_time = []
                uniq_date = assigned_date = []
                for f_t in free_time:

                    if f_t[0].date() not in uniq_date and f_t[0].date() >= datetime.datetime.now().date():
                        uniq_date.append(f_t[0].date())
                        assigned_date.append(f_t[0].date())

                sorted_f_ts = []
                for f_t in free_time:
                    total_minutes = time_diff(f_t[0].time(),
                                              f_t[1].time()).total_seconds() / 60
                    if int(customer.time_for_job) <= int(total_minutes):
                        sorted_f_ts.append(f_t)
                free_time = sorted_f_ts
                for u_d in uniq_date:
                    times = []
                    end_time = []
                    start_time = []
                    for f_t in free_time:
                        if f_t[0].date() == u_d:
                            if f_t[0].time() not in start_time and f_t[1].time() not in end_time:
                                f_start_time = f_t[0]+datetime.timedelta(minutes=1)
                                current_addrs = get_current_address_date(events, customer, f_t[0].date(),
                                                                         f_start_time.time())

                                if not current_addrs:
                                    current_addrs = TECHNICIAN_DEFAULT_ADDRESS
                                if current_addrs == TECHNICIAN_DEFAULT_ADDRESS:
                                    distance_dict = from_office_distance_dict
                                else:
                                    distance_dict = get_distance_n_duration(current_addrs, customer.address,f_t[0])
                                if distance_dict:
                                    duration = distance_dict
                                    is_hours = False
                                    if len(duration.split('hour')) == 2:
                                        is_hours = True
                                    elif len(duration.split('hours')) == 2:
                                        is_hours = True

                                    try:
                                        mins = int(duration.split('mins')[0])
                                    except:
                                        mins = 0

                                    if mins <= 30 and not is_hours:

                                        if mins > 20:
                                            color = 'red'
                                        elif mins > 15:
                                            color = 'yellow'
                                        else:
                                            color = 'green'
                                        if f_t[0].time().hour <= tstop.time().hour and f_t[1].time().hour >= tstart.time().hour:
                                            times.append({'start': f_t[0].time(), 'end': f_t[1].time(),
                                                          'current_addrs': current_addrs,'duration_mins': mins,'color':color})
                                end_time.append(f_t[1].time())
                                start_time.append(f_t[0].time())
                    if times:
                        sorted_free_time.append({'date': u_d, 'times': times})
                uniq_date = []

                # for f_t in full_free_times:
                #     if f_t[0].date() not in uniq_date:
                #         uniq_date.append(f_t[0].date())

                # for u_d in uniq_date:
                #     times = []
                #     end_time = []
                #     start_time = []
                #     for f_t in full_free_times:
                #         if f_t[0].date() == u_d:
                #             if f_t[0].time() not in start_time and f_t[1].time() not in end_time:
                #                 distance_dict = get_distance_n_duration(TECHNICIAN_DEFAULT_ADDRESS, customer.address)
                #                 if distance_dict:
                #                     duration = distance_dict['rows'][0]['elements'][0]['duration']['text']
                #                     is_hours = False
                #                     if len(duration.split('hour')) == 2:
                #                         is_hours = True
                #                     elif len(duration.split('hours')) == 2:
                #                         is_hours = True
                #
                #                     try:
                #                         mins = int(duration.split('mins')[0])
                #                     except:
                #                         mins = 0
                #
                #                     if mins <= 30 and not is_hours:
                #
                #                         if mins > 20:
                #                             color = 'red'
                #                         elif mins > 15:
                #                             color = 'yellow'
                #                         else:
                #                             color = 'green'
                #                         times.append({'start': f_t[0].time(), 'end': f_t[1].time(),
                #                                       'current_addrs': TECHNICIAN_DEFAULT_ADDRESS, 'duration_mins': mins,
                #                                       'color': color})
                #                 end_time.append(f_t[1].time())
                #                 start_time.append(f_t[0].time())
                #     if u_d not in assigned_date:
                #         sorted_fullfree_time.append({'date': u_d, 'times': times})
                uniq_date = []
                for y in sorted_free_time:
                    if y['date'] not in uniq_date:
                        uniq_date.append(y['date'])
                        filtered_free_time.append(y)
                sorted_free_time = filtered_free_time
                if free_time:
                    total_minutes = time_diff(free_time[0][0].time(),
                                              free_time[0][1].time()).total_seconds() / 60
                    if True:
                        start_time = free_time[0][0].time()
                        is_available = True
                        if is_available:
                            users_list.append({'user': user, 'current_address': '',
                                               'free_date': free_time[0][0].date(),
                                               'free_times': free_time,
                                               'sorted_free_time': sorted_free_time,
                                               'sorted_fullfree_time': sorted_fullfree_time,
                                               'free_end': free_time[0][1].time(), 'free_start': start_time,
                                               'events': sorted_events, 'color': '', 'mins': '',
                                               'duration': ''})
            except Exception as e:
                print e, "Here"
                pass

            distance_dict = None

            import pytz
            from pytz import timezone

            from accounts.models import TechnicianAppointments
            from task_scheduler.settings import TIME_ZONE

            eastern = timezone(TIME_ZONE)
            the_datetime = eastern.localize(
                datetime.datetime.strptime(str("2019-04-09") + ' 11:00:00-04:00', '%Y-%m-%d %H:%M:%S-04:00'))

        from dateutil.tz import tzoffset
        import datetime



        u_dates = []
        for dates in users_list:
            for n in dates.get('sorted_free_time'):
                if n.get('date') not in u_dates:
                    u_dates.append(n.get('date'))
            for n in dates.get('sorted_fullfree_time'):
                if n.get('date') not in u_dates:
                    u_dates.append(n.get('date'))
        context['users_list'] = users_list
        context['customer'] = customer
        context['u_dates'] = u_dates
        return context


@deprecate_current_app
@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name='sign-in.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    if request.method == 'GET' and request.user.is_authenticated():
        return redirect('/dashboard/')
    redirect_to = request.POST.get(redirect_field_name,
                                   request.GET.get(redirect_field_name, ''))

    if request.method == "POST":
        form = authentication_form(request, data=request.POST)
        if form.is_valid():
            # Ensure the user-originating redirection url is safe.
            # if not is_safe_url(url=redirect_to, host=request.get_host()):
            #     redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())
            return redirect('/')


    else:
        form = authentication_form(request)
    context = {
        'form': form,
        redirect_field_name: redirect_to,
    }
    if extra_context is not None:
        context.update(extra_context)

    return TemplateResponse(request, template_name, context)


def time_diff(start, end):
    from datetime import datetime, time as datetime_time, timedelta

    if isinstance(start, datetime_time):  # convert to datetime
        assert isinstance(end, datetime_time)
        start, end = [datetime.combine(datetime.min, t) for t in [start, end]]
    if start <= end:  # e.g., 10:33:26-11:15:49
        return end - start
    else:  # end < start e.g., 23:55:00-00:25:00
        end += timedelta(1)  # +day
        assert end > start
        return end - start


def logout(request):
    """

    :param request:
    :return:
    """

    auth_logout(request)
    return redirect(settings.LOGIN_REDIRECT_URL)
