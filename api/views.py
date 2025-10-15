from httplib2 import Credentials
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from google_auth_oauthlib.flow import Flow
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from googleapiclient.discovery import build

from api.models import Employee, Shift, SwapRequest, ShiftSelection
from api.serializers import EmployeeSerializer, ShiftSerializer, SwapRequestSerializer, ShiftSelectionSerializer, \
    MonthlyShiftSerializer

CREDENTIALS_PATH = '../smapp/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']

def google_calendar_init(request):
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_CLIENT_SECRETS_FILE,
        scopes=settings.GOOGLE_API_SCOPES,
        redirect_uri=settings.REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    request.session['state'] = state
    return redirect(authorization_url)

def google_calendar_redirect(request):
    state = request.session['state']

    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_CLIENT_SECRETS_FILE,
        scopes=settings.GOOGLE_API_SCOPES,
        state=state,
        redirect_uri=settings.REDIRECT_URI
    )

    flow.fetch_token(authorization_response=request.build_absolute_uri())

    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)

    return HttpResponse('Calendar integration complete. You can now use Google Calendar with your Django app.')

def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

def list_events(request):
    credentials = Credentials(**request.session['credentials'])
    service = build('calendar', 'v3', credentials=credentials)

    events_result = service.events().list(calendarId='primary', maxResults=10).execute()
    events = events_result.get('items', [])

    return HttpResponse(events)

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        authentication_classes=[TokenAuthentication]
    )
    def get_current(self, request):
        user = request.user
        serializer = EmployeeSerializer(user, context={'request': request})
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        try:
            employee = Employee.objects.get(pk=kwargs['pk'])
            if request.data.get('username'):
                employee.username = request.data.get('username')
            if request.data.get('email'):
                employee.email = request.data.get('email')
            if request.data.get('phone_number'):
                employee.phone_number = request.data.get('phone_number')
            if request.data.get('password'):
                employee.set_password(request.data.get('password'))
            if request.data.get('permissions'):
                employee.permissions = request.data.get('permissions')
            employee.save()
            serializer = EmployeeSerializer(employee, context={'request': request})
            return Response({'Message': 'Employee Updated!', 'Employee': serializer.data}, status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'Message': 'Could not update employee!'}, status.HTTP_400_BAD_REQUEST)

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @action(
        detail=False,
        methods=['POST'],
        permission_classes=[IsAuthenticated],
        authentication_classes=[TokenAuthentication]
    )
    def get_monthly_shifts(self, request):
        request_month = request.data.get('month')
        request_year = request.data.get('year')
        db_shifts = Shift.objects.filter(month=request_month, year=request_year)
        serializer = MonthlyShiftSerializer(db_shifts, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        day = request.data.get('day')
        month = request.data.get('month')
        year = request.data.get('year')
        morningEmployee = ''
        eveningEmployee = ''
        nightEmployee = ''
        if request.data.get('morning_employee_id') != -1:
            morningEmployee = Employee.objects.get(id=request.data.get('morning_employee_id'))
        if request.data.get('evening_employee_id') != -1:
            eveningEmployee = Employee.objects.get(id=request.data.get('evening_employee_id'))
        if request.data.get('night_employee_id') != -1:
            nightEmployee = Employee.objects.get(id=request.data.get('night_employee_id'))
        shifts = Shift.objects.filter(day=day, month=month, year=year)

        if shifts:
            for shift in shifts:
                shift.delete()

        if morningEmployee:
            Shift.objects.create(employee=morningEmployee, day=day, month=month, year=year, shift_type=1)

        if eveningEmployee:
            Shift.objects.create(employee=eveningEmployee, day=day, month=month, year=year, shift_type=2)

        if nightEmployee:
            Shift.objects.create(employee=nightEmployee, day=day, month=month, year=year, shift_type=3)

        if not morningEmployee and not eveningEmployee and not nightEmployee:
            return Response(status.HTTP_204_NO_CONTENT)

        return Response(status.HTTP_200_OK)


class SwapRequestViewSet(viewsets.ModelViewSet):
    queryset = SwapRequest.objects.all()
    serializer_class = SwapRequestSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        requesting_employee = Employee.objects.get(id=request.data.get('requesting_employee_id'))
        requested_employee_id = request.data.get('requested_employee_id')
        shift = Shift.objects.get(id=request.data.get('shift_id'))
        requesting_employee_requests = SwapRequest.objects.filter(requesting_employee=requesting_employee, completed=False)

        if requesting_employee_requests.count() == 5:
            print(requesting_employee_requests.count())
            return Response({'Message': 'Can not send more than 5 requests'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            swap_request, created = SwapRequest.objects.get_or_create(requesting_employee=requesting_employee, shift=shift, completed=False, is_user_approved=False)
            swap_request.requested_employee_id = requested_employee_id
            swap_request.save()
            serializer = SwapRequestSerializer(swap_request)

            if created:
                return Response({'Message': 'Swap request created', 'obj': serializer.data}, status=status.HTTP_201_CREATED)

            return Response({'Message': 'Swap Request Updated!',
                             'obj': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'Message': 'Swap Request creation Failed!'}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        swap_request = self.get_object()
        print(swap_request)
        approving = request.data.get('approving')
        response = request.data.get('is_approved')
        if approving == 'Employee':
            if not response:
                swap_request.is_user_approved = False
                swap_request.completed = True
                swap_request.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            swap_request.is_user_approved = True
            swap_request.save()
            return Response(status=status.HTTP_200_OK)

        if approving == 'Admin':
            if not response:
                swap_request.is_admin_approved = False
                swap_request.completed = True
                swap_request.save()
                return Response(status=status.HTTP_204_NO_CONTENT)

            swap_request.is_admin_approved = True
            swap_request.completed = True
            swap_request.save()

            try:
                requested_employee = Employee.objects.get(id=swap_request.requested_employee_id)
                shift = Shift.objects.get(id=swap_request.shift.id)
                shift.employee = requested_employee
                shift.save()
                return Response(status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({'Message': 'Error updating shift after approval'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        authentication_classes=[TokenAuthentication]
    )
    def get_admin_requests(self, request):
        swap_requests = SwapRequest.objects.filter(is_user_approved=True, is_admin_approved=False, completed=False)
        serializer = SwapRequestSerializer(swap_requests, many=True)
        return Response(serializer.data)

class ShiftSelectionViewSet(viewsets.ModelViewSet):
    queryset = ShiftSelection.objects.all()
    serializer_class = ShiftSelectionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        employee = Employee.objects.get(id=request.data.get('employee'))
        day = request.data.get('day')
        month = request.data.get('month')
        year = request.data.get('year')
        morning = request.data.get('morning')
        evening = request.data.get('evening')
        night = request.data.get('night')

        try:
            existing = ShiftSelection.objects.get(employee=employee, day=day, month=month, year=year)

            if not morning and not evening and not night:
                existing.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            existing.morning = morning
            existing.evening = evening
            existing.night = night
            existing.save()
            return Response(status=status.HTTP_200_OK)

        except:
            ShiftSelection.objects.create(employee=employee, day=day, month=month, year=year, morning=morning, evening=evening, night=night)
            return Response(status=status.HTTP_201_CREATED)


    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[TokenAuthentication]
            )
    def get_data(self, request, *args, **kwargs):
        month = request.data.get('month')
        year = request.data.get('year')
        data = ShiftSelection.objects.filter(month=month, year=year)
        serializer = ShiftSelectionSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False,
            methods=['POST'],
            permission_classes=[IsAuthenticated],
            authentication_classes=[TokenAuthentication]
            )
    def get_user_data(self, request, *args, **kwargs):
        employee = Employee.objects.get(id=request.user.id)
        month = request.data.get('month')
        year = request.data.get('year')
        data = ShiftSelection.objects.filter(employee=employee, month=month, year=year)
        serializer = ShiftSelectionSerializer(data, many=True)
        return Response(serializer.data)

