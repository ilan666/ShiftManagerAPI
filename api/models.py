from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# Create your models here.
SHIFT_TYPES = [
    (1, 1),
    (2, 2),
    (3, 3),
]

PERMISSIONS = [
    ('Admin', 'Admin'),
    ('User', 'User'),
]

class Employee(AbstractUser):
    phone_number = models.CharField(max_length=11, blank=True, null=True, unique=True)
    permissions = models.CharField(max_length=5, blank=True, null=True, choices=PERMISSIONS, default=PERMISSIONS[0])
    date_joined = models.DateField(auto_now_add=True)

class Shift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    day = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(31)])
    month = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(9999)])
    shift_type = models.IntegerField(blank=True, null=True, choices=SHIFT_TYPES)

class ShiftSelection(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    day = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(31)])
    month = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(9999)])
    morning = models.BooleanField(default=False)
    evening = models.BooleanField(default=False)
    night = models.BooleanField(default=False)

class SwapRequest(models.Model):
    requesting_employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    requested_employee_id = models.IntegerField(blank=True, null=True)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    is_user_approved = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)