import json

from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import Employee, Shift, SwapRequest, ShiftSelection
from api.serializers import EmployeeSerializer, ShiftSerializer, SwapRequestSerializer, ShiftSelectionSerializer, \
    MonthlyShiftSerializer


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
        shifts_data = request.data.get('data')
        month = shifts_data[0].get('month')
        year = shifts_data[0].get('year')

        Shift.objects.filter(month=month, year=year).delete()

        for shift_data in shifts_data:
            day = shift_data.get('day')
            month = shift_data.get('month')
            year = shift_data.get('year')
            if shift_data.get('morning_employee_id'):
                morning_employee = Employee.objects.get(id=shift_data.get('morning_employee_id'))
                try:
                    record = Shift.objects.get(day=day, month=month, year=year, shift_type=1)
                    record.employee = morning_employee
                    record.save()  # Save the changes
                except Shift.DoesNotExist:
                    Shift.objects.create(employee=morning_employee, day=day, month=month, year=year, shift_type=1)

            if shift_data.get('evening_employee_id'):
                evening_employee = Employee.objects.get(id=shift_data.get('evening_employee_id'))
                try:
                    record = Shift.objects.get(day=day, month=month, year=year, shift_type=2)
                    record.employee = evening_employee
                    record.save()  # Save the changes
                except Shift.DoesNotExist:
                    Shift.objects.create(employee=evening_employee, day=day, month=month, year=year, shift_type=2)

            if shift_data.get('night_employee_id'):
                night_employee = Employee.objects.get(id=shift_data.get('night_employee_id'))
                try:
                    record = Shift.objects.get(day=day, month=month, year=year, shift_type=3)
                    record.employee = night_employee
                    record.save()  # Save the changes
                except Shift.DoesNotExist:
                    Shift.objects.create(employee=night_employee, day=day, month=month, year=year, shift_type=3)

        return Response({'Message': 'Shifts data uploaded!'}, status=status.HTTP_201_CREATED)

class SwapRequestViewSet(viewsets.ModelViewSet):
    queryset = SwapRequest.objects.all()
    serializer_class = SwapRequestSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        requesting_employee = Employee.objects.get(id=request.data.get('requesting_employee_id'))
        requested_employee_id = request.data.get('requested_employee_id')
        shift = Shift.objects.get(id=request.data.get('shift_id'))
        requesting_employee_requests = SwapRequest.objects.filter(requesting_employee=requesting_employee)

        if requesting_employee_requests.count() == 5:
            print(requesting_employee_requests.count())
            return Response({'Message': 'Can not send more than 5 requests'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            swap_request, created = SwapRequest.objects.get_or_create(requesting_employee=requesting_employee, shift=shift)
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
        response = request.data.get('is_approved')
        print(response)
        if not swap_request.is_user_approved:
            if response:
                swap_request.is_user_approved = True
                swap_request.save()
                serializer = SwapRequestSerializer(swap_request)
                return Response(
                    {'Message': 'Request accepted by user!', 'obj': serializer.data}, status=status.HTTP_200_OK)

            else:
                swap_request.delete()
                return Response({'Message': 'Request refused by user and deleted'}, status=status.HTTP_204_NO_CONTENT)

        if not swap_request.is_admin_approved:
            if response:
                swap_request.is_admin_approved = True

                try:
                    requested_employee = Employee.objects.get(id=swap_request.requested_employee_id)
                    shift = Shift.objects.get(id=swap_request.shift.id)
                    shift.employee = requested_employee
                    shift.save()
                except Exception as e:
                    print(e)
                    return Response({'Message': 'Error updating shift after approval'}, status=status.HTTP_400_BAD_REQUEST)

                swap_request.save()
                serializer = SwapRequestSerializer(swap_request)
                return Response(
                    {'Message': 'Request accepted by admin!', 'obj': serializer.data}, status=status.HTTP_200_OK)

            else:
                swap_request.delete()
                return Response({'Message': 'Request refused by user and deleted'}, status=status.HTTP_204_NO_CONTENT)

class ShiftSelectionViewSet(viewsets.ModelViewSet):
    queryset = ShiftSelection.objects.all()
    serializer_class = ShiftSelectionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        shifts_data = request.data.get('data')
        month = shifts_data[0].get('month')
        year = shifts_data[0].get('year')
        employee = Employee.objects.get(id=shifts_data[0].get('employee'))

        ShiftSelection.objects.filter(employee=employee, month=month, year=year).delete()

        for shift_data in shifts_data:
            employee = Employee.objects.get(id=shift_data.get('employee'))
            day = shift_data.get('day')
            month = shift_data.get('month')
            year = shift_data.get('year')
            morning = shift_data.get('morning')
            evening = shift_data.get('evening')
            night = shift_data.get('night')

            try:
                ShiftSelection.objects.create(employee=employee,
                                              day=day,
                                              month=month,
                                              year=year,
                                              morning=morning,
                                              evening=evening,
                                              night=night)

            except Exception as e:
                print(e)
                return Response({'Message': 'Error creating shift request object...'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'Message': 'Shifts data uploaded!'}, status=status.HTTP_201_CREATED)

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

