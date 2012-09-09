from django.contrib import admin

from mtta.models import (
    Line, LineDirection, Node, Pattern, Service, SignUp, Stop,
    StopByLine, StopByPattern, StopTrip, Trip)


class LineAdmin(admin.ModelAdmin):
    readonly_fields = ('signup',)


class LineDirectionAdmin(admin.ModelAdmin):
    readonly_fields = ('line',)


class NodeAdmin(admin.ModelAdmin):
    readonly_fields = ('stop',)


class PatternAdmin(admin.ModelAdmin):
    readonly_fields = ('linedir', 'raw_pattern', 'fixed_pattern')


class StopAdmin(admin.ModelAdmin):
    readonly_fields = ('signup',)


class StopByLineAdmin(admin.ModelAdmin):
    readonly_fields = ('stop', 'linedir', 'node')


class StopByPatternAdmin(admin.ModelAdmin):
    readonly_fields = ('stop', 'linedir', 'pattern', 'node')


admin.site.register(Line, LineAdmin)
admin.site.register(LineDirection, LineDirectionAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(Pattern, PatternAdmin)
admin.site.register(Service)
admin.site.register(SignUp)
admin.site.register(Stop, StopAdmin)
admin.site.register(StopByLine, StopByLineAdmin)
admin.site.register(StopByPattern, StopByPatternAdmin)
admin.site.register(StopTrip)
admin.site.register(Trip)
