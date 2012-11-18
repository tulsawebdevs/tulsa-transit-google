from django.contrib import admin

from mtta.models import (
    AgencyInfo, Fare, FeedInfo, Line, LineDirection, Node, Pattern, Service,
    ServiceException, ShapeAttribute, SignUp, SignupExport, Stop, StopByLine,
    StopByPattern, Transfer, Trip, TripDay, TripStop, TripTime)


class LineAdmin(admin.ModelAdmin):
    raw_id_fields = ('signup',)
    list_filter = ('signup',)
    readonly_fields = ('attributes',)


class LineDirectionAdmin(admin.ModelAdmin):
    raw_id_fields = ('line',)
    list_filter = ('line__signup', 'line')


class NodeAdmin(admin.ModelAdmin):
    raw_id_fields = ('stops',)
    search_fields = (
        'node_id', 'node_abbr', 'node_name', 'stops__stop_abbr',
        'stops__node_abbr')
    list_display = ('__unicode__', 'node_name', 'node_abbr')


class PatternAdmin(admin.ModelAdmin):
    raw_id_fields = ('linedir',)
    readonly_fields = ('raw_pattern', 'fixed_pattern')
    list_filter = ('linedir__line__signup', 'linedir__line',)


class ServiceAdmin(admin.ModelAdmin):
    raw_id_fields = ('signup',)
    list_filter = ('signup',)


class SignUpAdmin(admin.ModelAdmin):
    pass


class SignupExportAdmin(admin.ModelAdmin):
    pass


class ShapeAttributeAdmin(admin.ModelAdmin):
    readonly_fields = ('attributes', )


class StopAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'stop_abbr', 'node_abbr', 'stop_name')
    raw_id_fields = ('signup',)
    list_filter = ('signup',)
    search_fields = ('stop_id', 'stop_abbr')
    readonly_fields = ('attributes',)


class StopByLineAdmin(admin.ModelAdmin):
    raw_id_fields = ('stop', 'linedir', 'node')
    search_fields = (
        'stop__stop_id', 'node__node_id', 'stop__stop_abbr',
        'stop__node_abbr', 'node__node_abbr')
    list_filter = ('stop__signup', 'linedir__line',)
    list_display = ('__unicode__', 'line', 'seq', 'stop', 'node')
    readonly_fields = ('attributes',)

    def line(self, instance):
        return str(instance.linedir.line)


class StopByPatternAdmin(admin.ModelAdmin):
    raw_id_fields = ('stop', 'linedir', 'pattern', 'node')
    search_fields = (
        'stop__stop_id', 'node__node_id', 'stop__stop_abbr',
        'stop__node_abbr', 'node__abbr')
    list_filter = ('stop__signup', 'linedir__line',)
    list_display = ('__unicode__', 'pattern', 'seq', 'line', 'stop', 'node')
    readonly_fields = ('attributes',)

    def line(self, instance):
        return str(instance.linedir.line)


class TransferAdmin(admin.ModelAdmin):
    raw_id_fields = ('from_stop', 'to_stop')
    search_fields = (
        'from_stop__stop_id', 'from_stop__stop_abbr',
        'to_stop__stop_id', 'to_stop__stop_id')
    list_filter = ('from_stop__signup',)
    list_display = (
        'from_stop', 'to_stop', 'transfer_type', 'min_transfer_time')
    list_display_links = ('transfer_type',)


class TripDayAdmin(admin.ModelAdmin):
    raw_id_fields = ('linedir', 'service')
    list_filter = ('service__signup', 'linedir__line',)
    list_display = ('__unicode__', 'linedir', 'service')


class TripStopAdmin(admin.ModelAdmin):
    raw_id_fields = ('tripday', 'stop', 'node', 'arrival')
    list_filter = ('stop__signup', 'tripday__linedir__line',)
    list_display = (
        '__unicode__', 'tripday', 'seq', 'stop_abbr', 'stop', 'node_abbr',
        'node')


class TripTimeAdmin(admin.ModelAdmin):
    raw_id_fields = ('trip', 'tripstop')
    list_filter = ('trip__tripday__linedir__line',)
    list_display = ('__unicode__', 'trip', 'tripstop', 'stop', 'time')

    def stop(self, instance):
        return str(instance.tripstop.stop)


class TripAdmin(admin.ModelAdmin):
    raw_id_fields = ('tripday', 'pattern')


admin.site.register(AgencyInfo)
admin.site.register(Fare)
admin.site.register(FeedInfo)
admin.site.register(Line, LineAdmin)
admin.site.register(LineDirection, LineDirectionAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(Pattern, PatternAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceException)
admin.site.register(ShapeAttribute, ShapeAttributeAdmin)
admin.site.register(SignUp, SignUpAdmin)
admin.site.register(SignupExport, SignupExportAdmin)
admin.site.register(Stop, StopAdmin)
admin.site.register(StopByLine, StopByLineAdmin)
admin.site.register(StopByPattern, StopByPatternAdmin)
admin.site.register(Transfer, TransferAdmin)
admin.site.register(Trip, TripAdmin)
admin.site.register(TripDay, TripDayAdmin)
admin.site.register(TripStop, TripStopAdmin)
admin.site.register(TripTime, TripTimeAdmin)
