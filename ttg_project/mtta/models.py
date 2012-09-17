import logging
import os

from django.db import models
from django_extensions.db.fields.json import JSONField
import dbfpy.dbf
import shapefile

from mtta.utils import haversine

logger = logging.getLogger(__name__)


def mockable_open(path):
    return open(path)


class SignUp(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    _unset_name = '<unset>'
    # TODO: Don't hardcode agency details
    _agency_defaults = dict(
        name='Tulsa Transit', url='http://www.tulsatransit.org',
        timezone='America/Chicago', phone='(918) 582-2100', lang='en',
        fare_url='http://tulsatransit.org/fares-passes/')
    _calendar_dates = (
        (1, '2012-11-22', 2),
        (1, '2012-11-23', 2),
        (2, '2012-11-23', 1),
        (1, '2012-12-24', 2),
        (2, '2012-12-24', 1),
        (1, '2012-12-25', 2),
        (1, '2013-01-01', 2),
    )
    
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
            TripDay.import_schedule(self, path)

    def copy_to_feed(self):
        from multigtfs.models import Feed
        feed = Feed.objects.create(name=self.name)
        feed.agency_set.get_or_create(defaults=self._agency_defaults)
        for line in self.line_set.all():
            logger.info('Exporting data for line %s...' % line)
            line.copy_to_feed(feed)
        for service_id, date, etype in self._calendar_dates:
            service = feed.service_set.get(service_id=service_id)
            service.servicedate_set.create(date=date, exception_type=etype)
        return feed

    def __unicode__(self):
        return "%s-%s" % (self.id, self.name or '(No Name)')


class Line(models.Model):
    '''A transit line from lines.dbf'''
    signup = models.ForeignKey(SignUp)
    line_id = models.IntegerField(db_index=True)
    line_abbr = models.CharField(max_length=8, db_index=True)
    line_name = models.CharField(max_length=30)
    line_color = models.IntegerField()
    line_type = models.CharField(max_length=2)

    class Meta:
        unique_together = ('signup', 'line_id')
        ordering = ('line_id',)

    def __unicode__(self):
        return "%s-%s" % (self.line_id, self.line_abbr)

    @classmethod
    def import_dbf(cls, signup, path):
        logger.info('Parsing Lines from %s...' % path)
        db_f = dbfpy.dbf.Dbf(path, readOnly=True)
        line_cnt, linedir_cnt = 0, 0
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
                linedir_cnt += 1
        logger.info(
            'Parsed %d Lines, %s LineDirections.' % (line_cnt, linedir_cnt))


    def color_as_hex(self):
        '''Convert integer value into a hex color value

        Because SQLite strips leading 0's from numbers, we store strangely.
        '''
        try:
            return '%06x' % self.line_color
        except:
            return self.color

    def text_color_as_hex(self):
        '''Convert integer value into a contrasting hex color value
        '''
        back_color = self.color_as_hex()
        # http://www.webmasterworld.com/forum88/9769.htm
        r = int(back_color[:2], 16)
        g = int(back_color[2:4], 16)
        b = int(back_color[4:6], 16)

        color_value = ((r * 299) + (g * 587) + (b * 114)) / 1000

        if color_value > 130:
            text_color = '000000'
        else:
            text_color = 'ffffff'
        return text_color
    
    def short_name(self):
        return self.line_abbr.replace('FLEX', 'FX').replace('SFLX', 'SF')

    def copy_to_feed(self, feed):
        gtfs_route, created = feed.route_set.get_or_create(
            route_id=self.line_id, defaults=dict(
                short_name=self.short_name(),
                long_name=self.line_name.replace(self.line_abbr, ''),
                rtype=3, color=self.color_as_hex(),
                text_color=self.text_color_as_hex()))
        for linedir in self.linedirection_set.all():
            linedir.copy_to_feed(feed, gtfs_route)


class LineDirection(models.Model):
    '''The two line directions for a Line from lines.dbf'''
    linedir_id = models.IntegerField(db_index=True)
    line = models.ForeignKey(Line)
    name = models.CharField(max_length=20)

    class Meta:
        unique_together = ('linedir_id', 'line')
        ordering = ('linedir_id',)

    def __unicode__(self):
        return "%s-%s" % (self.linedir_id, self.name)

    def copy_to_feed(self, feed, gtfs_route):
        for tripday in self.tripday_set.all():
            tripday.copy_to_feed(feed, gtfs_route)


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
        return "%s-%s" % (self.pattern_id, self.name)

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
            point_cnt += 2 * len(parts)
            cls.objects.create(
                pattern_id=pattern_id, name=pattern, linedir=linedir,
                raw_pattern=parts)
            pattern_cnt += 1
        logger.info(
            'Parsed %d Shapes with a total of %d points.' % (
                pattern_cnt, point_cnt))

    def copy_to_feed(self, feed):
        shape_id = "%s_%s" % (self.pattern_id, self.name)
        gtfs_shape, created = feed.shape_set.get_or_create(shape_id=shape_id)
        if created:
            for seq, (lat, lon) in enumerate(self.get_points()):
                gtfs_shape.points.create(sequence=seq, lat=lat, lon=lon)
        return gtfs_shape
    
    def get_points(self):        
        def node_dist(node1, node2):
            return haversine(node1[0], node1[1], node2[0], node2[1])
        
        if not self.fixed_pattern:
            # Create line
            line = []
            parts = self.raw_pattern
            first_nodes = None
            min_add_dist = 0.140
            for seq, (node1, node2) in enumerate(parts):
                if first_nodes:
                    first_node1, first_node2 = first_nodes
                    # Sort node orders by shortest distance between segments
                    node_orders = sorted([
                        (node_dist(first_node1, node1),
                         (first_node2, first_node1, node1, node2)),
                        (node_dist(first_node1, node2),
                         (first_node2, first_node1, node2, node1)),
                        (node_dist(first_node2, node1),
                         (first_node1, first_node2, node1, node2)),
                        (node_dist(first_node2, node2),
                         (first_node1, first_node2, node2, node1))])
                    dist, (n1, n2, n3, n4) = node_orders[0]
                    # Optimize for shared point in the two segements
                    if n2 == n3:
                        line.extend((n1, n2, n4))
                    elif node_dist(n2, n3) < min_add_dist:
                        # print "Pattern %s:%s for line %s: Adding first segment (%0.5f, %0.5f) -> (%0.5f, %0.5f) (%0.1f meters)" % (pattern_id, pattern, linedir_id, n2[0], n2[1], n3[0], n3[1], 1000.0 * node_dist(n2, n3))
                        line.extend((n1, n2, n3, n4))
                    else:
                        pass
                        #if verbose:
                        #    print "Pattern %s:%s for line %s: Discarding first segment (%0.5f, %0.5f) -> (%0.5f, %0.5f) (%0.1f meters)" % (pattern_id, pattern, linedir_id, n2[0], n2[1], n3[0], n3[1], 1000.0 * node_dist(n2, n3))
                    first_nodes = None
                elif line:
                    last_node = line[-1]
                    # Sort node orders by shortest distance to tail point
                    node_orders = sorted([
                        (node_dist(last_node, node1),
                            (last_node, node1, node2)),
                        (node_dist(last_node, node2),
                            (last_node, node2, node1))])
                    n1, n2, n3 = node_orders[0][1]
                    # Optimize for tail point in the new segment
                    if n1 == n2:
                        line.append(n3)
                    elif node_dist(n1, n2) < min_add_dist:
                        #if verbose:
                        #    print "Pattern %s:%s for line %s: Adding segment (%0.5f, %0.5f) -> (%0.5f, %0.5f) (%0.1f meters)" % (pattern_id, pattern, linedir_id, n1[0], n1[1], n2[0], n2[1], 1000.0 * node_dist(n1, n2))
                        line.extend((n2, n3))
                    else:
                        pass
                        #if verbose:
                        #    print "Pattern %s:%s for line %s: Discarding segment (%0.5f, %0.5f) -> (%0.5f, %0.5f) (%0.1f meters)" % (pattern_id, pattern, linedir_id, n1[0], n1[1], n2[0], n2[1], 1000.0 * node_dist(n1, n2))
                else:
                    # Collect the first segment for later
                    first_nodes = (node1, node2)
            self.fixed_pattern = line
            self.save()
        return self.fixed_pattern        


class Stop(models.Model):
    '''A stop from stops.dbf'''
    signup = models.ForeignKey(SignUp)
    stop_id = models.IntegerField(db_index=True)
    stop_abbr = models.CharField(max_length=7, db_index=True)
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
        ordering = ('signup', 'stop_id')

    def __unicode__(self):
        return "%s-%s" % (self.stop_id, self.stop_abbr)

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

    def copy_to_feed(self, feed):
        gtfs_stop, created = feed.stop_set.get_or_create(
            stop_id=self.stop_id, defaults=dict(
                name=self.stop_name, lat=self.lat, lon=self.lon,
                desc=self.site_name, code=self.stop_abbr, location_type=0))
        return gtfs_stop


class Node(models.Model):
    '''A node inferred from StopsByLine or StopsByPattern

    We don't have a direct database of nodes, but some stops are identified as
    nodes in the StopsBy* data.
    '''
    stop = models.ForeignKey(Stop, related_name='nodes')
    node_id = models.IntegerField(db_index=True)
    abbr = models.CharField(max_length=8)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s-%s" % (self.node_id, self.abbr)

    class Meta:
        unique_together = ('stop', 'node_id')
        ordering = ('node_id', 'stop__stop_id')


class StopByLine(models.Model):
    stop = models.ForeignKey(Stop)
    linedir = models.ForeignKey(LineDirection)
    seq = models.IntegerField()
    node = models.ForeignKey(Node, null=True, blank=True)

    class Meta:
        unique_together = ('stop', 'linedir', 'seq')
        ordering = ('linedir', 'seq')
        verbose_name_plural = "stops by line"

    def __unicode__(self):
        return '%s-%02d' % (self.linedir.linedir_id, self.seq)

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
                node = None

            cls.objects.create(stop=stop, linedir=linedir, seq=seq, node=node)
            sxl_cnt += 1
        logger.info(
            'Parsed %d Stops->Line: %d nodes (%d unique), %d stops.' % (
                sxl_cnt, node_cnt, new_node_cnt, stop_cnt))


class StopByPattern(models.Model):
    stop = models.ForeignKey(Stop)
    linedir = models.ForeignKey(LineDirection)
    pattern = models.ForeignKey(Pattern)
    seq = models.IntegerField()
    node = models.ForeignKey(Node, null=True, blank=True)

    class Meta:
        unique_together = ('stop', 'linedir', 'pattern', 'seq')
        ordering = ('pattern', 'seq',)
        verbose_name_plural = "stops by pattern"

    def __unicode__(self):
        return '%s-%02d' % (self.pattern.pattern_id, self.seq)

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
                node = None

            cls.objects.create(
                stop=stop, linedir=linedir, pattern=pattern, seq=seq,
                node=node)
            sxl_cnt += 1
        logger.info(
            'Parsed %d Stops->Pattern: %d nodes (%d new), %d stops.' % (
                sxl_cnt, node_cnt, new_node_cnt, stop_cnt))


class Service(models.Model):
    signup = models.ForeignKey(SignUp)
    service_id = models.IntegerField(
        choices=((1, 'Weekday'), (2, 'Saturday')))
    _service_defaults = {
        1: dict(monday=True, tuesday=True, wednesday=True, thursday=True,
                friday=True, saturday=False, sunday=False,
                start_date='2012-08-01', end_date='2013-08-01'),
        2: dict(monday=False, tuesday=False, wednesday=False, thursday=False,
                friday=False, saturday=True, sunday=False,
                start_date='2012-08-01', end_date='2013-08-01')
    }

    class Meta:
        unique_together = ordering = ('signup', 'service_id')

    def __unicode__(self):
        return '%s-%s' % (self.service_id, self.get_service_id_display())

    def copy_to_feed(self, feed):
        # TODO: Don't hardcode these
        gtfs_service, created = feed.service_set.get_or_create(
            service_id=str(self.service_id),
            defaults=self._service_defaults[self.service_id])
        return gtfs_service


class TripDay(models.Model):
    '''A set of trips for a line direction by service day'''
    linedir = models.ForeignKey(LineDirection)
    service = models.ForeignKey(Service)

    class Meta:
        unique_together = ordering = ('linedir', 'service')

    def __unicode__(self):
        return '%s-%s' % (self.linedir.linedir_id, self.service.service_id)

    @classmethod
    def import_schedule(cls, signup, path):
        logger.info('Parsing Trips from %s...' % path)

        in_intro = 0  # Make sure we're in a Stop Trips file
        in_meta = 1   # Get Line and Service, fix SignUp name
        in_dir = 2    # Get / switch the LineDirection
        in_cols = 3   # Get the TripStops
        in_data = 4   # Get the Trip and TripTimes
        in_error = 5  # Some error, cease processing
        phase = in_intro

        linedir = None
        meta = dict()

        tripday_cnt, tripstop_cnt, trip_cnt, triptimes_cnt = 0, 0, 0, 0
        for linenum, linein in enumerate(mockable_open(path).readlines()):
            linein = linein.rstrip()
            if phase == in_intro:
                # Make sure we're in a Stop Trips file
                if linenum == 0:
                    assert(linein == 'Stop Trips')
                elif linenum == 1:
                    assert(linein == '~~~~~~~~~~')
                elif linenum == 2:
                    assert(linein == '')
                    phase = in_meta
                else:
                    raise ValueError(
                        'Got lost in intro phase at line %d:\n.%s' %
                        (linenum, linein))
            elif phase == in_meta:
                # Get Line and Service, fix SignUp name
                if ':' in linein:
                    name, val = linein.split(':', 1)
                    meta[name] = val.strip()
                elif linein == '':
                    signup_name = meta['SignUp']
                    service_id = meta['Service']
                    line_name = meta['Line']
                    if signup.name == SignUp._unset_name:
                        signup.name = signup_name
                        signup.save()
                    service, created = Service.objects.get_or_create(
                        signup=signup, service_id=service_id)
                    possible_names = (
                        line_name, line_name + 'FLEX', line_name + 'FLX')
                    line = signup.line_set.get(line_abbr__in=possible_names)
                    phase = in_dir
            elif phase == in_dir:
                # Get / switch the LineDirection
                if linein.startswith('Direction:'):
                    name, raw_val = linein.split(':', 1)
                    val = raw_val.strip()
                    linedir = line.linedirection_set.get(name=val)
                    tripday = cls.objects.create(
                        linedir=linedir, service=service)
                    tripday_cnt += 1
                    phase = in_cols
                    col_lines = []
                elif linein == '':
                    continue
                else:
                    raise ValueError(
                        'Got lost in dir phase at line %d:\n%s' %
                        (linenum, linein))
            elif phase == in_cols:
                # Accumulate the header, then parse TripStops
                # Format is something like:
                #   Pattern  Node
                #            Stop
                #   ~~~~~~~ ~~~~~
                if linein == '':
                    continue
                elif not linein.startswith('~'):
                    col_lines.append(linein)
                else:
                    assert len(col_lines) in (1, 2)
                    col_lines.append(linein)
                    parsed = TripStop.parse_schedule_for_tripstops(
                        tripday, col_lines)
                    if not parsed:
                        # Parse errors, abandon
                        phase = in_error
                        break
                    else:
                        pattern_bounds, data_bounds, tripstops = parsed
                    tripstop_cnt += len(tripstops)
                    phase = in_data
                    found_trip = False
                    trip_seq = 0
            elif phase == in_data:
                if linein == '':
                    if trip_seq > 0:
                        # Get ready for next set of data
                        phase = in_dir
                    else:
                        continue
                elif linein.startswith('Direction:'):
                    raise ValueError(
                        'Got lost in data phase at line %d:\n%s' %
                        (linenum, linein))
                else:
                    # Parse Trip
                    raw_pat = linein[pattern_bounds[0]:pattern_bounds[1]]
                    pattern_name= raw_pat.strip()
                    pattern = linedir.pattern_set.get(name=pattern_name)
                    trip = Trip.objects.create(
                        tripday=tripday, pattern=pattern, seq=trip_seq)
                    trip_seq += 1
                    trip_cnt += 1
                    # Parse TripTime
                    for time_seq, (start, end) in enumerate(data_bounds):
                        time = linein[start:end].strip()
                        if time:
                            tripstop = tripstops[time_seq]
                            TripTime.objects.create(
                                trip=trip, tripstop=tripstop, time=time)
                            triptimes_cnt += 1
        if phase == in_error:
            logger.warning(
                'Errors detected during parsing, may be partially imported.')
        logger.info(
            'Parsed %d times for %d trips, %d stops, and %d line directions.'
                % (triptimes_cnt, trip_cnt, tripstop_cnt, tripday_cnt))

    def copy_to_feed(self, feed, gtfs_route):
        gtfs_service = self.service.copy_to_feed(feed)
        for trip in self.trip_set.all():
            trip.copy_to_feed(feed, gtfs_route, gtfs_service)



class TripStop(models.Model):
    '''A stop on a TripDay'''
    tripday = models.ForeignKey(TripDay)
    stop = models.ForeignKey(Stop, null=True, blank=True)
    stop_abbr = models.CharField(max_length=7)
    node = models.ForeignKey(Node, null=True, blank=True)
    node_abbr = models.CharField(max_length=8, blank=True)
    seq = models.IntegerField()

    class Meta:
        unique_together = ordering = ('tripday', 'seq')

    def __unicode__(self):
        return "%s-%02d" % (self.tripday, self.seq)

    @classmethod
    def parse_schedule_for_tripstops(cls, tripday, col_lines):
        assert len(col_lines) == 2 or len(col_lines) == 3
        assert set(col_lines[-1]) == set(' ~'),\
            'Last col_line must be schedule column designator'
        linedir = tripday.linedir
        signup = linedir.line.signup

        # Determine the columns
        field_bounds = list()
        start = 0
        last_char = '~'
        for column, char in enumerate(col_lines[-1]):
            if char != last_char:
                if char == ' ':
                    field_bounds.append((start, column))
                elif char == '~':
                    start = column
                last_char = char
        last_start, last_column = field_bounds[-1]
        if last_start != start:
            field_bounds.append((start, column+1))
        # Get the column titles
        columns = list()
        for start, end in field_bounds:
            col1 = col_lines[0][start:end].strip()
            if len(col_lines) == 3:
                col2 = col_lines[1][start:end].strip()
            else:
                col2 = None
            columns.append((col1, col2))
        # First column should be 'Pattern'
        assert columns[0][0] == 'Pattern'
        pattern_bounds = field_bounds[0]
        # There may be two unused columns 'INT' and 'VAL'
        data_col = 1
        while True:
            if (columns[data_col][0] in ('INT', 'VAL') or
                    columns[data_col][1] in ('INT', 'VAL')):
                data_col += 1
            else:
                break
        assert data_col == 1 or data_col == 3
        data_bounds = field_bounds[data_col:]
        # The rest are node/stop columns, but we need to match
        #  them to data.  First, let's test if StopsByLine is
        #  accurate
        stops_by_line_matches = True
        tripstop_params = []
        for seq, abbrs in enumerate(columns[data_col:]):
            node_abbr, stop_abbr = abbrs
            sbl = linedir.stopbyline_set.get(seq=seq+1)
            node = sbl.node
            stop = sbl.stop
            if node_abbr:
                if ((not node or node_abbr != node.abbr) and
                        (not stop or node_abbr != stop.node_abbr)):
                    stops_by_line_matches = False
                    logger.info(
                        'At seq %s, abbrs %s, node %s did not match' %
                        (seq, abbrs, sbl.node))
                    break
            if stop_abbr:
                if not stop or stop_abbr != stop.stop_abbr:
                    stops_by_line_matches = False
                    logger.info(
                        'At seq %s, abbrs %s, stop %s did not match' %
                        (seq, abbrs, sbl.stop))
                    break
            tripstop_params.append(
                dict(stop=stop, node=node, stop_abbr=stop_abbr,
                     node_abbr=node_abbr))
        if stops_by_line_matches:
            # This is the best way to match times to stops
            tripstops = []
            for seq, params in enumerate(tripstop_params):
                params['tripday'] = tripday
                params['seq'] = seq
                tripstops.append(TripStop.objects.create(**params))
            return pattern_bounds, data_bounds, tripstops

        # Another possibility is that StopsByLine is just the nodes.
        #  If this is the case, then guess at stops
        #  Try for a node match, then for a stop match
        logger.info('Trying nodes-by-line strategy...')

        # Test the abbreviations against the candidates
        node_seq = 1
        tripstop_params = []
        for seq, abbrs in enumerate(columns[data_col:]):
            node_abbr, stop_abbr = abbrs
            # Look for the node in StopByLine
            if node_abbr:
                sbl = linedir.stopbyline_set.get(seq=node_seq)
                node = sbl.node
                stop = sbl.stop
                node_match = (node and node_abbr == node.abbr)
                stop_node_match = (
                    stop and node_abbr.lower() == stop.node_abbr.lower())
                any_node_match = node_match or stop_node_match
                stop_match = (stop and stop_abbr == stop.stop_abbr)
                if stop_node_match and not node_match:
                    logger.info(
                        'On linedir %s seq %s, node %s did not match "%s" but'
                        ' stop %s did' %
                        (linedir, seq, node, node_abbr, sbl.stop))
                if not any_node_match:
                    logger.info(
                        'On linedir %s seq %s, node %s did not match "%s" and'
                        ' stop %s did not either' %
                        (linedir, seq, node, node_abbr, sbl.stop))
                if not stop_match:
                    logger.info(
                        'On linedir %s seq %s, stop %s did not match "%s"' %
                        (linedir, seq, stop, stop_abbr))
                if any_node_match and stop_match:
                    if not node_match:
                        node = None
                    tripstop_params.append(dict(stop=sbl.stop, node=node))
                    node_seq += 1
                    continue

            # Look for stops in the SignUp with the same ID
            stops = signup.stop_set.filter(
                stop_abbr=stop_abbr).order_by('stop_id')
            if len(stops) == 1:
                stop = stops[0]
            else:
                stop = None
                logger.warning(
                    'At stop %s, %d stops found for stop "%s"'
                    ' - Leaving stop unassigned' %
                    (seq, len(stops), stop_abbr))
            tripstop_params.append(dict(stop=stop, stop_abbr=stop_abbr))
        tripstops = []
        for seq, params in enumerate(tripstop_params):
            params['tripday'] = tripday
            params['seq'] = seq
            tripstops.append(TripStop.objects.create(**params))
        return pattern_bounds, data_bounds, tripstops


class Trip(models.Model):
    '''A bus trip on a TripDay'''
    tripday = models.ForeignKey(TripDay)
    pattern = models.ForeignKey(Pattern)
    seq = models.IntegerField()

    class Meta:
        unique_together = ordering = ('tripday', 'seq', 'pattern')

    def __unicode__(self):
        return "%s-%s-%s" % (self.tripday, self.pattern, self.seq)

    def copy_to_feed(self, feed, gtfs_route, gtfs_service):
        route_id = gtfs_route.short_name
        service_id = gtfs_service.service_id
        linedir = self.tripday.linedir
        direction = str(linedir.linedir_id)[-1]
        trip_id = "%s_%s_%s_%02d" % (route_id, service_id, direction, self.seq)
        gtfs_shape = self.pattern.copy_to_feed(feed)
        gtfs_trip, created = gtfs_route.trip_set.get_or_create(
            trip_id=trip_id, defaults=dict(
                headsign=linedir.name, direction=direction, shape=gtfs_shape))
        gtfs_trip.services.add(gtfs_service)
        
        no_time = self.triptime_set.filter(time='')
        if no_time.exists():
            logger.info('On Trip %s, skipping %d stops with no time.' %
                        (self, no_time.count()))
        no_stop = self.triptime_set.filter(tripstop__stop=None)
        if no_stop.exists():
            logger.info('On Trip %s, skipping %d stops with ambiguous stop'
                        ' abbreviations.' % (self, no_stop.count()))
        
        # Gather the valid trip times
        times = []
        for triptime in self.triptime_set.exclude(
                time='').exclude(tripstop__stop=None):
            times.append([triptime, False])
        times[0][1] = True
        times[-1][1] = True
        
        for triptime, force_time in times:
            triptime.copy_to_feed(feed, gtfs_trip, force_time)


class TripTime(models.Model):
    '''A stop time for a Trip'''
    trip = models.ForeignKey(Trip)
    tripstop = models.ForeignKey(TripStop)
    time = models.CharField(max_length=5)

    def __unicode__(self):
        return "%s-%s" % (self.tripstop, self.time)

    class Meta:
        unique_together = ordering = ('trip', 'tripstop')
        ordering = ('trip', 'tripstop', 'time')

    def copy_to_feed(self, feed, gtfs_trip, force_time):
        if not self.tripstop.stop:
            logger.info('Skipping TripTime "%s" - no stop' % self)
            return
        if self.time and (self.tripstop.node_abbr or force_time):
            time = self.time
        else:
            time = None
        if force_time and not time:
            logger.warning('Skipping TripTime "%s" - needs time' % self)
            return None
        gtfs_stop = self.tripstop.stop.copy_to_feed(feed)
        gtfs_stoptime, created = gtfs_trip.stoptime_set.get_or_create(
            stop=gtfs_stop, stop_sequence=self.tripstop.seq, defaults=dict(
                arrival_time=time, departure_time=time))
        if force_time and not created:
            gtfs_stoptime.arrival_time=time
            gtfs_stoptime.departure_time=time
            gtfs_stoptime.save()
        return gtfs_stoptime
