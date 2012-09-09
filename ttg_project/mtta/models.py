import logging
import os

from django.db import models
from django_extensions.db.fields.json import JSONField
import dbfpy.dbf
import shapefile

logger = logging.getLogger(__name__)


class SignUp(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    def import_folder(self, folder, stdout=None):
        data_file = dict()
        names = (
            ('lines.dbf', 'line.dbf'),
            ('patterns.shp', 'pattern.shp'),
            ('stops.dbf', 'stop.dbf'),
            ('stopsbyline.dbf',),
            ('stopsbypattern.dbf',),
        )
        stop_trips = []
        for path, dirs, files in os.walk(folder):
            for f in files:
                full_path = os.path.abspath(os.path.join(path, f))
                name = os.path.split(full_path)[-1].lower()
                for nameset in names:
                    if name in nameset:
                        data_file[nameset[0]] = full_path
                if name.endswith('.txt'):
                    key_string = 'Stop Trips'
                    with open(full_path, 'r') as candidate:
                        first_bits = candidate.read(len(key_string))
                    if (first_bits == key_string):
                        stop_trips.append(full_path)

        for nameset in names:
            key = nameset[0]
            if key not in data_file.keys():
                raise Exception('No %s found in path %s' % (key, folder))
        if not stop_trips:
            raise Exception('No schedules found in path %s' % folder)
        Line.import_dbf(self, data_file['lines.dbf'])
        Pattern.import_shp(self, data_file['patterns.shp'])
        Stop.import_dbf(self, data_file['stops.dbf'])
        StopByLine.import_dbf(self, data_file['stopsbyline.dbf'])
        StopByPattern.import_dbf(self, data_file['stopsbypattern.dbf'])
        for path in stop_trips:
            Trip.import_schedule(self, path)

    def __unicode__(self):
        return "%s - %s" % (self.id, self.name or '(No Name)')


class Line(models.Model):
    '''A transit line from lines.dbf'''
    signup = models.ForeignKey(SignUp)
    line_id = models.IntegerField(db_index=True)
    line_abbr = models.CharField(max_length=8)
    line_name = models.CharField(max_length=30)
    line_color = models.IntegerField()
    line_type = models.CharField(max_length=2)
    
    class Meta:
        unique_together = ('signup', 'line_id')

    def __unicode__(self):
        return "%s - %s - %s" % (
            self.signup_id, self.line_abbr, self.line_name)

    @classmethod
    def import_dbf(cls, signup, path):
        logger.info('Parsing Lines from %s...' % path)
        db_f = dbfpy.dbf.Dbf(path, readOnly=True)
        line_cnt, line_dir_cnt = 0, 0
        for record in db_f:
            line_id = record['LineID']
            line_abbr = record['LineAbbr']
            line_name = unicode(record['LineName'], encoding='latin-1')
            line_color = record['LineColor']
            line_type = record['LineType']
            line = cls.objects.create(
                signup=signup, line_id=line_id, line_abbr=line_abbr,
                line_name=line_name, line_color=line_color,
                line_type=line_type)
            line_cnt += 1
            linedir_id0 = record['LineDirId0']
            if linedir_id0:
                LineDirection.objects.create(
                    line=line, linedir_id=linedir_id0, 
                    name=record['TPFIELD320'])
                linedir_cnt +=1
            linedir_id1 = record['LineDirId1']
            if linedir_id1:
                LineDirection.objects.create(
                    line=line, linedir_id=linedir_id1,
                    name=record['TPFIELD321'])
                line_dir_cnt += 1
        logger.info(
            'Parsed %d Lines, %s LineDirections.' % (line_cnt, line_dir_cnt))


class LineDirection(models.Model):
    '''The two line directions for a Line from lines.dbf'''
    linedir_id = models.IntegerField(db_index=True)
    line = models.ForeignKey(Line)
    name = models.CharField(max_length=20)
    
    class Meta:
        unique_together = ('linedir_id', 'line')

    def __unicode__(self):
        return "%s - %s - %s" % (
            self.line, self.linedir_id, self.name)


class Pattern(models.Model):
    '''The path the bus takes along the streets from pattern.*'''
    pattern_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=5)
    linedir = models.ForeignKey(LineDirection)
    raw_pattern = JSONField(default=[])
    fixed_pattern = JSONField(blank=True, default=[])
    
    class Meta:
        unique_together = ('linedir', 'pattern_id')

    def __unicode__(self):
        return "%s - %s - %s" % (
            self.linedir, self.pattern_id, self.name)

    @classmethod
    def import_shp(cls, signup, path):
        logger.info('Parsing Pattern Shapes from %s...' % path)
        sf = shapefile.Reader(path)
        assert sf.shapeType == 3  # PolyLine
        shapes = sf.shapes()
        PATTERN_ID_FIELD = 1
        PATTERN_FIELD = 2
        LINEDIR_ID_FIELD = 3
        assert sf.fields[PATTERN_ID_FIELD][0] == 'PatternId'
        assert sf.fields[PATTERN_FIELD][0] == 'Pattern'
        assert sf.fields[LINEDIR_ID_FIELD][0] == 'LineDirId'
        pattern_cnt, point_cnt = 0, 1
        for record, shape in zip(sf.records(), shapes):
            assert shape.shapeType == 3
            pattern_id = record[PATTERN_ID_FIELD - 1]
            pattern = record[PATTERN_FIELD - 1]
            linedir_id = record[LINEDIR_ID_FIELD - 1]
            linedir = LineDirection.objects.get(
                line__signup=signup, linedir_id=linedir_id)
            # Pattern is a sequence of point pairs
            parts = []
            part = None
            for seq, (lon, lat) in enumerate(shape.points):
                if seq in shape.parts:
                    # Start of a new shape
                    if part:
                        # Parts could have more than 2 points, but MTTA
                        # data has only 2-point parts
                        assert len(part) == 2
                        if part[0] != part[1]:
                            # If not a point
                            part.sort()
                            parts.append((part[0], part[1]))
                    part = []
                part.append((lat, lon))
            if part:
                parts.append((part[0], part[1]))
            points = parts
            point_cnt += 2 * len(parts)
            cls.objects.create(
                pattern_id=pattern_id, name=pattern, linedir=linedir,
                raw_pattern=points)
            pattern_cnt += 1
        logger.info(
            'Parsed %d Shapes with a total of %d points.' % (
                pattern_cnt, point_cnt))


class Stop(models.Model):
    '''A stop from stops.dbf'''
    signup = models.ForeignKey(SignUp)
    stop_id = models.IntegerField(db_index=True)
    stop_abbr = models.CharField(max_length=7)
    stop_name = models.CharField(max_length=50)
    node_abbr = models.CharField(max_length=8, blank=True)
    site_name = models.CharField(max_length=50, blank=True)
    lat = models.DecimalField(
        'Latitude', max_digits=13, decimal_places=8,
        help_text='WGS 84 latitude of stop or station')
    lon = models.DecimalField(
        'Longitude', max_digits=13, decimal_places=8,
        help_text='WGS 84 longtitude of stop or station')

    class Meta:
        unique_together = ('signup', 'stop_id')

    def __unicode__(self):
        return "%s - %s - %s" % (
            self.signup.id, self.stop_id, self.stop_name)

    @classmethod
    def import_dbf(cls, signup, path):
        logger.info('Parsing Stops from %s...' % path)
        db_f = dbfpy.dbf.Dbf(path, readOnly=True)
        stop_cnt = 0
        for record in db_f:
            stop_id = record['StopID']
            stop_abbr = record['StopAbbr']
            stop_name = unicode(record['StopName'], encoding='latin-1')
            node_abbr = record['NodeAbbr']
            site_name = unicode(record['SiteName'], encoding='latin-1')
            raw_lat = str(record['Lat'])
            lat = raw_lat[:-6] + '.' + raw_lat[-6:]
            raw_lon = str(record['Lon'])
            lon = raw_lon[:-6] + '.' + raw_lon[-6:]
            cls.objects.create(
                signup=signup, stop_id=stop_id, stop_abbr=stop_abbr,
                stop_name=stop_name, node_abbr=node_abbr, site_name=site_name,
                lat=lat, lon=lon)
            stop_cnt += 1
        logger.info('Parsed %d Stops.' % stop_cnt)


class Node(models.Model):
    '''A node inferred from StopsByLine or StopsByPattern
    
    We don't have a direct database of nodes, but some stops are identified as
    nodes in the StopsBy* data.
    '''
    stop = models.ForeignKey(Stop, related_name='nodes')
    node_id = models.IntegerField(db_index=True)
    abbr = models.CharField(max_length=8)
    name = models.CharField(max_length=20)

    class Meta:
        unique_together = ('stop', 'node_id')
    

class StopByLine(models.Model):
    stop = models.ForeignKey(Stop)
    linedir = models.ForeignKey(LineDirection)
    seq = models.IntegerField()

    class Meta:
        unique_together = ('stop', 'linedir', 'seq')

    @classmethod
    def import_dbf(cls, signup, path):
        logger.info('Parsing Stops->Line from %s...' % path)
        db_f = dbfpy.dbf.Dbf(path, readOnly=True)
        sxl_cnt, node_cnt, new_node_cnt, stop_cnt = 0, 0, 0, 0
        for record in db_f:
            stop_id = record['StopID']
            stop_abbr = record['StopAbbr']
            stop_name = unicode(record['StopName'], encoding='latin-1')
            site_name = unicode(record['SiteName'], encoding='latin-1')
            raw_lat = str(record['Lat'])
            lat = raw_lat[:-6] + '.' + raw_lat[-6:]
            raw_lon = str(record['Lon'])
            lon = raw_lon[:-6] + '.' + raw_lon[-6:]
            stop = Stop.objects.get(signup=signup, stop_id=stop_id)
            assert stop.stop_abbr == stop_abbr
            assert stop.stop_name == stop_name
            assert stop.site_name == site_name
            assert lat.startswith(str(stop.lat))
            assert lon.startswith(str(stop.lon))

            linedirid = record['LineDirID']
            linedir = LineDirection.objects.get(
                line__signup=signup, linedir_id=linedirid)

            seq = record['Sequence']
            stop_type = record['StopType']
            if stop_type == 'N':
                node_cnt += 1
                node_abbr = record['NodeAbbr']
                node_name = unicode(record['NodeName'], encoding='latin-1')
                node_id = record['NodeID']
                node, created = Node.objects.get_or_create(
                    stop=stop, node_id=node_id, abbr=node_abbr,
                    name=node_name)
                if created:
                    new_node_cnt += 1
            else:
                stop_cnt += 1
            

            cls.objects.create(stop=stop, linedir=linedir, seq=seq)
            sxl_cnt += 1
        logger.info(
            'Parsed %d Stops->Line: %d nodes (%d new), %d stops.' % (
                sxl_cnt, node_cnt, new_node_cnt, stop_cnt))


class StopByPattern(models.Model):
    stop = models.ForeignKey(Stop)
    linedir = models.ForeignKey(LineDirection)
    pattern = models.ForeignKey(Pattern)
    seq = models.IntegerField()
    
    class Meta:
        unique_together = ('stop', 'linedir', 'pattern', 'seq')

    @classmethod
    def import_dbf(cls, signup, path):
        logger.info('Parsing Stops->Pattern from %s...' % path)
        db_f = dbfpy.dbf.Dbf(path, readOnly=True)
        sxl_cnt, node_cnt, new_node_cnt, stop_cnt = 0, 0, 0, 0
        for record in db_f:
            stop_id = record['StopID']
            stop_abbr = record['StopAbbr']
            stop_name = unicode(record['StopName'], encoding='latin-1')
            site_name = unicode(record['SiteName'], encoding='latin-1')
            raw_lat = str(record['Lat'])
            lat = raw_lat[:-6] + '.' + raw_lat[-6:]
            raw_lon = str(record['Lon'])
            lon = raw_lon[:-6] + '.' + raw_lon[-6:]
            stop = Stop.objects.get(signup=signup, stop_id=stop_id)
            assert stop.stop_abbr == stop_abbr
            assert stop.stop_name == stop_name
            assert stop.site_name == site_name
            assert lat.startswith(str(stop.lat))
            assert lon.startswith(str(stop.lon))

            linedirid = record['LineDirID']
            linedir = LineDirection.objects.get(
                line__signup=signup, linedir_id=linedirid)
                
            pattern_id = record['PatternID']
            pattern_name = record['Pattern']
            pattern = Pattern.objects.get(
                linedir=linedir, pattern_id=pattern_id)
            assert pattern.name == pattern_name

            seq = record['Sequence']
            stop_type = record['StopType']
            if stop_type == 'N':
                node_cnt += 1
                node_abbr = record['NodeAbbr']
                node_name = unicode(record['NodeName'], encoding='latin-1')
                node_id = record['NodeID']
                node, created = Node.objects.get_or_create(
                    stop=stop, node_id=node_id, abbr=node_abbr,
                    name=node_name)
                if created:
                    new_node_cnt += 1
            else:
                stop_cnt += 1

            cls.objects.create(
                stop=stop, linedir=linedir, pattern=pattern, seq=seq)
            sxl_cnt += 1
            if stop_type == 'N':
                node_cnt += 1
            else:
                stop_cnt += 1
        logger.info(
        'Parsed %d Stops->Line: %d nodes (%d new), %d stops.' % (
            sxl_cnt, node_cnt, new_node_cnt, stop_cnt))


class Service(models.Model):
    signup = models.ForeignKey(SignUp)
    service_id = models.IntegerField()


class Trip(models.Model):
    linedir = models.ForeignKey(LineDirection)
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
