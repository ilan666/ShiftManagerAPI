from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from api.models import Employee, Shift, SwapRequest, ShiftSelection


class EmployeeSerializer(serializers.ModelSerializer):
    pending_requests = serializers.SerializerMethodField(method_name='get_pending_requests')
    sent_requests = serializers.SerializerMethodField(method_name='get_sent_requests')
    completed_requests = serializers.SerializerMethodField(method_name='get_completed_requests')
    processing_requests = serializers.SerializerMethodField(method_name='get_processing_requests')
    admin_requests = serializers.SerializerMethodField(method_name='get_admin_requests')
    shifts = serializers.SerializerMethodField(method_name='get_shifts')
    selected_shifts = serializers.SerializerMethodField(method_name='get_selected_shifts')

    class Meta:
        model = Employee
        fields = ('id',
                  'first_name',
                  'last_name',
                  'username',
                  'email',
                  'phone_number',
                  'date_joined',
                  'permissions',
                  'pending_requests',
                  'sent_requests',
                  'completed_requests',
                  'processing_requests',
                  'admin_requests',
                  'shifts',
                  'selected_shifts',
                  'password',)
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['password'] = make_password(password)
        employee = Employee.objects.create(**validated_data)
        Token.objects.create(user=employee)
        return employee

    def get_pending_requests(self, employee):
        swap_requests = SwapRequest.objects.filter(requested_employee_id=employee.id, is_user_approved=False)
        serializer = SwapRequestSerializer(swap_requests, many=True)
        return serializer.data

    def get_shifts(self, employee):
        shifts = Shift.objects.filter(employee=employee)
        serializer = ShiftSerializer(shifts, many=True)
        return serializer.data

    def get_sent_requests(self, employee):
        swap_requests = SwapRequest.objects.filter(requesting_employee=employee, is_admin_approved=False)
        serializer = SwapRequestSerializer(swap_requests, many=True)
        return serializer.data

    def get_completed_requests(self, employee):
        swap_requests = SwapRequest.objects.filter(requesting_employee=employee, is_user_approved=True, is_admin_approved=True)
        serializer = SwapRequestSerializer(swap_requests, many=True)
        return serializer.data

    def get_admin_requests(self, employee):
        if (employee.permissions == 'Admin'):
            swap_requests = SwapRequest.objects.filter(is_user_approved=True, is_admin_approved=False)
            serializer = SwapRequestSerializer(swap_requests, many=True)
            return serializer.data
        else:
            return []

    def get_selected_shifts(self, employee):
        selected_shifts = ShiftSelection.objects.filter(employee=employee)
        serializer = ShiftSelectionSerializer(selected_shifts, many=True)
        return serializer.data

    def get_processing_requests(self, employee):
        swap_requests = SwapRequest.objects.filter(requesting_employee=employee, is_admin_approved=False)
        serializer = SwapRequestSerializer(swap_requests, many=True)
        return serializer.data

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class EmployeeDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ('id', 'first_name', 'last_name')

class MonthlyShiftSerializer(serializers.ModelSerializer):
    employee = EmployeeDataSerializer(read_only=True)
    class Meta:
        model = Shift
        fields = '__all__'

class ShiftSelectionSerializer(serializers.ModelSerializer):
    employee = EmployeeDataSerializer(read_only=True)

    class Meta:
        model = ShiftSelection
        fields = '__all__'

class SwapRequestSerializer(serializers.ModelSerializer):
    requesting_employee = EmployeeDataSerializer(read_only=True)
    requested_employee = serializers.SerializerMethodField(method_name='get_requested_employee')
    shift = ShiftSerializer(read_only=True)

    class Meta:
        model = SwapRequest
        fields = ['id', 'requesting_employee', 'requested_employee', 'shift', 'is_user_approved', 'is_admin_approved']

    def get_requested_employee(self, obj):
        requested = Employee.objects.get(id=obj.requested_employee_id)
        serializer = EmployeeDataSerializer(requested, read_only=True)
        return serializer.data