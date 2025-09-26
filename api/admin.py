from django.contrib import admin

from api.models import Employee, Shift, SwapRequest, ShiftSelection

# Register your models here.

admin.site.register(Employee)
admin.site.register(Shift)
admin.site.register(SwapRequest)
admin.site.register(ShiftSelection)