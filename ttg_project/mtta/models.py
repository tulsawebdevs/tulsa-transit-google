import logging
import os

from django.db import models
from django_extensions.db.fields.json import JSONField

logger = logging.getLogger(__name__)


class SignUp(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    
    def import_folder(self, folder, stdout=None):
        lines_dbf, patterns_dbf, patterns_shp, stops_dbf= (None, ) * 4
        stop_trips = []
        for path, dirs, files in os.walk(folder):
            for f in files:
                full_path = os.path.abspath(os.path.join(path, f))
                name = os.path.split(full_path)[-1].lower()
                if name in ('line.dbf', 'lines.dbf'):
                    lines_dbf = full_path
                elif name in ('pattern.dbf', 'patterns.dbf'):
                    patterns_dbf = full_path
                elif name in ('pattern.shp', 'patterns.shp'):
                    patterns_shp = full_path
                elif name in ('stop.dbf', 'stops.dbf'):
                    stops_dbf = full_path
                elif name.endswith('.txt'):
                    key_string = 'Stop Trips'
                    with open(full_path, 'r') as candidate:
                        first_bits = candidate.read(len(key_string))
                    if (first_bits == key_string):
                        stop_trips.append(full_path)
                    
        if not lines_dbf:
            raise Exception('No lined.dbf found in path %s' % folder)
        if not patterns_dbf:
            raise Exception('No patterns.dbf found in path %s' % folder)
        if not patterns_shp:
            raise Exception('No patterns.shp found in path %s' % folder)
        if not stops_dbf:
            raise Exception('No stops.dbf found in path %s' % folder)
        if not stop_trips:
            raise Exception('No schedules found in path %s' % folder)
        Line.import_dbf(self, lines_dbf)
        Pattern.import_dbf(self, patterns_dbf)
        Pattern.import_shp(self, patterns_shp)
        Stop.import_dbf(self, stops_dbf)
        for path in stop_trips:
            Trip.import_schedule(self, path)


class Line(models.Model):
    '''A transit line from lines.dbf'''
    signup = models.ForeignKey(SignUp)
    line_id = models.IntegerField()
    line_abbr = models.CharField(max_length=8)
    line_name = models.CharField(max_length=20)
    line_color = models.IntegerField()
    line_type = models.CharField(max_length=2)
    active = models.BooleanField(default=False)
    
    @classmethod
    def import_dbf(cls, signup, path):
        logger.info('Parsing Lines from %s...' % path)
        total = cls.objects.filter(signup=signup).count()
        logger.info('Parsed %d Lines.' % total)


class LineDir(models.Model):
    '''The two line directions for a Line from lines.dbf'''
    line_dir_id = models.IntegerField()  # LINEDIRID0, LINEDIRID1
    line = models.ForeignKey(Line)
    name = models.CharField(max_length=12)  # TPFIELD320, TPFIELD321


class Pattern(models.Model):
    '''The path the bus takes along the streets from pattern.*'''
    signup = models.ForeignKey(SignUp)
    pattern_id = models.IntegerField()
    name = models.CharField(max_length=2)
    linedir = models.ForeignKey(LineDir)
    raw_pattern = JSONField()
    
    @classmethod
    def import_dbf(cls, signup, path):
        logger.info('Parsing Patterns from %s...' % path)
        total = cls.objects.filter(signup=signup).count()
        logger.info('Parsed %d Patterns.' % total)

    @classmethod
    def import_shp(cls, signup, path):
        logger.info('Parsing Pattern Shapes from %s...' % path)
        total = cls.objects.filter(signup=signup).count()
        logger.info('Parsed %d Pattern Shapes.' % total)


class Stop(models.Model):
    '''A stop from stops.dbf'''
    signup = models.ForeignKey(SignUp)
    stop_id = models.IntegerField()
    stop_abbr = models.CharField(max_length=7)
    stop_name = models.CharField(max_length=20)
    node_abbr = models.CharField(max_length=4)
    site_name = models.CharField(max_length=20)
    lat = models.DecimalField(
        'Latitude', max_digits=13, decimal_places=8,
        help_text='WGS 84 latitude of stop or station')
    lon = models.DecimalField(
        'Longitude', max_digits=13, decimal_places=8,
        help_text='WGS 84 longtitude of stop or station')
    shape = models.ForeignKey(Pattern)

    @classmethod
    def import_dbf(cls, signup, path):
        logger.info('Parsing Stops from %s...' % path)
        total = cls.objects.filter(signup=signup).count()
        logger.info('Parsed %d Stops.' % total)


class Service(models.Model):
    signup = models.ForeignKey(SignUp)
    service_id = models.IntegerField()


class Trip(models.Model):
    linedir = models.ForeignKey(LineDir)
    service = models.ForeignKey(Service)
    seq = models.IntegerField()
    pattern = models.ForeignKey(Pattern)
    
    @classmethod
    def import_schedule(cls, signup, path):
        logger.info('Parsing Trips from %s...' % path)


class StopTrip(models.Model):
    trip = models.ForeignKey(Trip)
    stop = models.ForeignKey(Stop)
    seq = models.IntegerField()
    time = models.CharField(max_length=5, blank=True)
