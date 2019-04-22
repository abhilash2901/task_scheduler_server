from __future__ import print_function
import datetime


import pytz
from pytz import timezone

from accounts.models import TechnicianAppointments
from task_scheduler.settings import TIME_ZONE, TECHNICIAN_DEFAULT_ADDRESS

eastern = timezone(TIME_ZONE)
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from django.core.files.base import ContentFile
from dateutil import tz
import dateutil
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_events_from_min_max(technician,start,end):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """

        creds = None
        if technician.token_pickle:
            with open(technician.token_pickle.path, 'rb') as token:

                creds = pickle.load(token)

        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        events_result = service.events().list(calendarId='primary', timeMin=start.isoformat(),
                                              maxResults=1000, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])


        # start_times = []
        # for event in events:
        #     start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
        #     start_times.append(start)
        # for event in events:
        #     start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
        #     end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))
        #
        #     TechnicianAppointments.objects.get_or_create(technician=technician,start_datetime=start,end=end)
        return events

def get_calender_events(technician):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    file_path = technician.credential.path
    is_authenticated = False
    import os
    # try:
    #     os.remove("token.pickle")
    # except:
    #     pass
    # if os.path.exists('token.pickle'):
    #     with open('token.pickle', 'rb') as token:
    #         # technician.token_pickle = token
    #         # technician.save()
    #         creds = pickle.load(token)
    if technician.token_pickle:
        with open(technician.token_pickle.path, 'rb') as token:
            # technician.token_pickle = token
            # technician.save()
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        is_authenticated = True
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                file_path, SCOPES)

            url = technician.auth_url
            creds = flow.run_local_server_with_url(host='localhost', auth_url=url)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            # technician.token_pickle = open('token.pickle')

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    utc = pytz.UTC
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    today = datetime.datetime.now()
    start = datetime.datetime(today.year, today.month, today.day - 1, tzinfo=tz.tzutc()).isoformat()
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=start,
                                          maxResults=1000, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    if is_authenticated:
        technician.token_pickle.save('token.pickle.txt', ContentFile(open('token.pickle', 'r').read()))

        technician.is_email_authenticated = True
        technician.save()

    # start_times = []
    # for event in events:
    #     start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
    #     start_times.append(start)
    # for event in events:
    #     start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
    #     end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))
    #
    #     TechnicianAppointments.objects.get_or_create(technician=technician,start_datetime=start,end=end)
    return events


def get_free_times(technician):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """

    print('Getting the upcoming 10 events')

    dates = []
    dates.append(datetime.datetime.now().date())
    c_date = datetime.datetime.now().date()
    c_date -= datetime.timedelta(days=1)
    for i in range(1, 10):
        c_date += datetime.timedelta(days=1)
        dates.append(c_date)
    appointments = []
    free_time = event_dates = []
    assigned_dates = []
    for now in dates:
        now_date = now
        now = now.isoformat()

        the_datetime = eastern.localize(
            datetime.datetime.strptime(str(now) + ' 08:00:00-04:00', '%Y-%m-%d %H:%M:%S-04:00'))
        the_datetime2 = eastern.localize(
            datetime.datetime.strptime(str(now) + ' 18:00:00-04:00', '%Y-%m-%d %H:%M:%S-04:00'))
        # the_datetime = tz.localize(datetime.datetime(2019, 4, 3, 0))
        # the_datetime2 = tz.localize(datetime.datetime(2019, 4, 4, 0))
        events = get_events_from_min_max(technician,the_datetime,the_datetime2)
        count = 0

        for event in events:

            start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
            end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))
            if start.date().day == 8:
                print(".")
            appointments.append({
                'start': start,
                'end': end
            })

            assigned_dates.append(now_date)

        # for now in dates:
        #     is_available = False
        #     for p in appointments:
        #         print("nowww",now)
        #         if now == p['start']:
        #             print("...............................",now)
        tp = [(the_datetime, the_datetime)]

        # tp = []
        for t in appointments:
            tp.append((t['start'], t['end']))
        tp.append((the_datetime2, the_datetime2))

        for i, v in enumerate(tp):
            if i > 0:
                if (tp[i][0] - tp[i - 1][1]) > datetime.timedelta(seconds=0):
                    tf_start = tp[i - 1][1]
                    delta = tp[i][0] - tp[i - 1][1]
                    tf_end = tf_start + delta
                    free_time.append((tf_start, tf_end))
                    if tf_start.date() <= datetime.datetime.now().date():
                        tf_start = datetime.datetime.strptime(str(tf_start).replace("+05:30","").replace("-04:00",""), '%Y-%m-%d %H:%M:%S')
                        tf_end = datetime.datetime.strptime(str(tf_end).replace("+05:30","").replace("-04:00",""), '%Y-%m-%d %H:%M:%S')
                    if tf_start.time() != the_datetime.time() and tf_end.time() != the_datetime2.time():
                        free_time.append((tf_start, tf_end))

    full_free_times = []
    for now in dates:
        if now not in assigned_dates:
            the_datetime = eastern.localize(
                datetime.datetime.strptime(str(now) + ' 08:00:00-04:00', '%Y-%m-%d %H:%M:%S-04:00'))
            the_datetime2 = eastern.localize(
                datetime.datetime.strptime(str(now) + ' 19:00:00-04:00', '%Y-%m-%d %H:%M:%S-04:00'))

            # free_time.append((the_datetime, the_datetime2))
            full_free_times.append((the_datetime, the_datetime2))

    return full_free_times,free_time


def get_current_address(events, customer):
    current_date = datetime.datetime.now().date()
    time = datetime.datetime.now().time()

    # office_address = "philadelphia, pa"
    office_address = TECHNICIAN_DEFAULT_ADDRESS
    current_address = office_address
    previous_event = get_previous_event(events, current_date, time)
    next_event = get_next_event(events, current_date, time)

    if previous_event:
        previous_start = dateutil.parser.parse(previous_event['start'].get('dateTime', previous_event['start'].get('date')))
        previous_end = dateutil.parser.parse(previous_event['end'].get('dateTime', previous_event['end'].get('date')))
        previous_current_address = previous_event.get('location')
        previous_summery = previous_event.get('summary')

    next_summery = previous_summery = 'none'
    if next_event:
        next_start = dateutil.parser.parse(next_event['start'].get('dateTime', next_event['start'].get('date')))
        next_end = dateutil.parser.parse(next_event['end'].get('dateTime', next_event['end'].get('date')))
        next_current_address = next_event.get('location')
        next_summery = next_event.get('summary')

    for event in events:
        start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
        end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))

        if start.date() == current_date:
            if start.time() < time < end.time():

                if event.get('summary').lower() == 'break':
                    if next_event:
                        time_gap = next_start - end
                        time_gap = time_gap.seconds/(60)
                        if int(customer.time_for_job) > int(time_gap):
                            current_address = next_current_address
                            break
                        else:
                            current_address = office_address
                            break
                    else:
                        current_address = office_address
                        break
            else:
                if previous_event:
                    if previous_summery.lower() != 'break' and previous_summery.lower() != 'off':
                        if next_summery.lower() != 'break' and next_summery.lower() != 'off':
                            current_address = previous_current_address
                        else:
                            current_address = office_address

                    elif previous_summery.lower() == 'break':
                        time_gap = next_start - previous_end
                        time_gap = time_gap.seconds / (60)
                        if int(customer.time_for_job) > int(time_gap):
                            current_address = next_current_address
                            break
                        else:
                            current_address = office_address
                            break
                else:
                    current_address = office_address
                    break


    return current_address


def get_current_address_date(events, customer,current_date,time):

    # office_address = "philadelphia, pa"
    office_address = TECHNICIAN_DEFAULT_ADDRESS
    current_address = office_address
    previous_event = get_previous_event(events, current_date, time)
    next_event = get_next_event(events, current_date, time)

    if previous_event:
        previous_start = dateutil.parser.parse(previous_event['start'].get('dateTime', previous_event['start'].get('date')))
        previous_end = dateutil.parser.parse(previous_event['end'].get('dateTime', previous_event['end'].get('date')))
        previous_current_address = previous_event.get('location')
        previous_summery = previous_event.get('summary')

    next_summery = previous_summery = 'none'
    if next_event:
        next_start = dateutil.parser.parse(next_event['start'].get('dateTime', next_event['start'].get('date')))
        next_end = dateutil.parser.parse(next_event['end'].get('dateTime', next_event['end'].get('date')))
        next_current_address = next_event.get('location')
        next_summery = next_event.get('summary')

    for event in events:
        start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
        end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))

        if start.date() == current_date:
            if start.time() < time < end.time():
                if event.get('summary').lower() == 'break':
                    if next_event:
                        time_gap = next_start - end
                        time_gap = time_gap.seconds/(60)
                        if int(customer.time_for_job) > int(time_gap):
                            current_address = next_current_address
                            break
                        else:
                            current_address = office_address
                            break
                    else:
                        current_address = office_address
                        break
            else:
                if previous_event:
                    if previous_summery.lower() != 'break' and previous_summery.lower() != 'off':
                        if next_summery.lower() != 'break' and next_summery.lower() != 'off':
                            current_address = previous_current_address
                        else:
                            current_address = office_address

                    elif previous_summery.lower() == 'break':
                        time_gap = next_start - previous_end
                        time_gap = time_gap.seconds / (60)
                        if int(customer.time_for_job) > int(time_gap):
                            current_address = next_current_address
                            break
                        else:
                            current_address = office_address
                            break
                else:
                    current_address = office_address
                    break


    return current_address


def get_previous_event(events, current_date, time):
    """

    :param events:
    :param current_date:
    :param time:
    :return:
    """
    previous_event = {}
    for event in events:
        start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
        end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))

        if start.date() == current_date:
            if end.time() <= time:
                previous_event = event

    return previous_event


def get_next_event(events, current_date, time):
    """

    :param events:
    :param current_date:
    :param time:
    :return:
    """
    next_event = {}
    for event in events:
        start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
        end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))

        if start.date() == current_date:
            if start.time() >= time:
                next_event = event
                break
    return next_event
