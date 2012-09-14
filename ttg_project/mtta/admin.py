from django.contrib import admin

from mtta.models import (
    SignUp, Line, LineDirection, Pattern, Stop, Node, StopByLine,
    StopByPattern, Service, TripDay, TripStop, Trip, TripTime)


class LineAdmin(admin.ModelAdmin):
    raw_id_fields = ('signup',)
    list_filter = ('signup',)


class LineDirectionAdmin(admin.ModelAdmin):
    raw_id_fields = ('line',)
    list_filter = ('line__signup', 'line')


class NodeAdmin(admin.ModelAdmin):
    raw_id_fields = ('stop',)
    search_fields = ('node_id', 'abbr', 'stop__stop_abbr', 'stop__node_abbr')
    list_display = ('__unicode__', 'stop', 'name')


class PatternAdmin(admin.ModelAdmin):
    raw_id_fields = ('linedir',)
    read_only_fields = ('raw_pattern', 'fixed_pattern')
    list_filter = ('linedir__line__signup', 'linedir__line',)


class ServiceAdmin(admin.ModelAdmin):
    raw_id_fields = ('signup',)
    list_filter = ('signup',)


class SignUpAdmin(admin.ModelAdmin):
    pass


class StopAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'stop_abbr', 'node_abbr', 'stop_name')
    raw_id_fields = ('signup',)
    list_filter = ('signup',)
    search_fields = ('stop_id', 'stop_abbr')


class StopByLineAdmin(admin.ModelAdmin):
    raw_id_fields = ('stop', 'linedir', 'node')
    search_fields = (
        'stop__stop_id', 'node__node_id', 'stop__stop_abbr',
        'stop__node_abbr', 'node__node_abbr')
    list_filter = ('stop__signup', 'linedir__line',)
    list_display = ('__unicode__', 'line', 'seq', 'stop', 'node')
    
    def line(self, instance):
        return str(instance.linedir.line)


class StopByPatternAdmin(admin.ModelAdmin):
    raw_id_fields = ('stop', 'linedir', 'pattern', 'node')
    search_fields = (
        'stop__stop_id', 'node__node_id', 'stop__stop_abbr',
        'stop__node_abbr', 'node__node_abbr')
    list_filter = ('stop__signup', 'linedir__line',)
    list_display = ('__unicode__', 'pattern', 'seq', 'line', 'stop', 'node')
    
    def line(self, instance):
        return str(instance.linedir.line)


class TripDayAdmin(admin.ModelAdmin):
    raw_id_fields = ('linedir', 'service')
    list_filter = ('service__signup', 'linedir__line',)
    list_display = ('__unicode__', 'linedir', 'service')


class TripStopAdmin(admin.ModelAdmin):
    raw_id_fields = ('tripday', 'stop', 'node')
    list_filter = ('stop__signup', 'tripday__linedir__line',)
    list_display = ('__unicode__', 'tripday', 'seq', 'stop_abbr', 'stop', 'node_abbr', 'node')


class TripTimeAdmin(admin.ModelAdmin):
    raw_id_fields = ('trip', 'tripstop')
    list_filter = ('trip__tripday__linedir__line',)
    list_display = ('__unicode__', 'trip', 'tripstop', 'time')


class TripAdmin(admin.ModelAdmin):
    raw_id_fields = ('tripday', 'pattern')


admin.site.register(Line, LineAdmin)
admin.site.register(LineDirection, LineDirectionAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(Pattern, PatternAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(SignUp, SignUpAdmin)
admin.site.register(Stop, StopAdmin)
admin.site.register(StopByLine, StopByLineAdmin)
admin.site.register(StopByPattern, StopByPatternAdmin)
admin.site.register(TripDay, TripDayAdmin)
admin.site.register(TripStop, TripStopAdmin)
admin.site.register(Trip, TripAdmin)
admin.site.register(TripTime, TripTimeAdmin)
