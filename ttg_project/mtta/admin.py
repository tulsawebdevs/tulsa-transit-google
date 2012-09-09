from django.contrib import admin

from mtta.models import (
    Line, LineDirection, Pattern, Service, SignUp, Stop, StopTrip, Trip)

admin.site.register(Line)
admin.site.register(LineDirection)
admin.site.register(Pattern)
admin.site.register(Service)
admin.site.register(SignUp)
admin.site.register(Stop)
admin.site.register(StopTrip)
admin.site.register(Trip)