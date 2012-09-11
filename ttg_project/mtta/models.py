import logging
import os

from django.db import models
from django_extensions.db.fields.json import JSONField
import dbfpy.dbf
import shapefile

logger = logging.getLogger(__name__)


def mockable_open(path):
    return open(path)


class SignUp(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    _unset_name = '<unset>'

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
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s - %s - %s" % (self.stop, self.node_id, self.abbr)

    class Meta:
        unique_together = ('stop', 'node_id')


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
        return '%s - %s - %s' % (self.linedir, self.seq, self.stop)

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
        return '%s -  %s - %s' % (self.pattern, self.seq, self.stop)

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

    class Meta:
        unique_together = ordering = ('signup', 'service_id')

    def __unicode__(self):
        return '%s - %s' % (self.signup.id, self.get_service_id_display())


class TripDay(models.Model):
    '''A set of trips for a line direction by service day'''
    linedir = models.ForeignKey(LineDirection)
    service = models.ForeignKey(Service)

    class Meta:
        unique_together = ordering = ('linedir', 'service')

    def __unicode__(self):
        return '%s - %s' % (self.linedir, self.service)

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
        return "%s - %s" % (self.tripday, self.seq)

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
        #  Panic on a node mismatch, but OK if no exact stop match
        logger.info('Trying nodes-by-line strategy...')

        # Test the abbreviations against the candidates
        nodes_by_line_matches = True
        node_seq = 1
        tripstop_params = []
        for seq, abbrs in enumerate(columns[data_col:]):
            node_abbr, stop_abbr = abbrs
            if node_abbr:
                # Look for the node in StopByLine
                sbl = linedir.stopbyline_set.get(seq=node_seq)
                node = sbl.node
                stop = sbl.stop
                if ((not node or node_abbr != node.abbr) and
                        (not stop or node_abbr != stop.node_abbr)):
                    nodes_by_line_matches = False
                    logger.info(
                        'At seq %s, abbrs %s, node %s did not match' %
                        (seq, abbrs, sbl.node))
                    break
                if stop_abbr:
                    if not stop or stop_abbr != stop.stop_abbr:
                        nodes_by_line_matches = False
                        logger.info(
                            'At seq %s, abbrs %s, stop %s did not match' %
                            (seq, abbrs, sbl.stop))
                        break
                tripstop_params.append(dict(stop=sbl.stop, node=sbl.node))
                node_seq += 1
            else:
                # Look for stops in the SignUp with the same ID
                stops = signup.stop_set.filter(
                    stop_abbr=stop_abbr).order_by('stop_id')
                if len(stops) == 1:
                    stop = stops[0]
                else:
                    stop = None
                    logger.warning(
                        'At stop %s, %d stops found for abbreviation "%s"'
                        ' - Leaving stop unassigned' %
                        (seq, len(stops), stop_abbr))
                tripstop_params.append(dict(stop=stop, stop_abbr=stop_abbr))
        if nodes_by_line_matches:
            tripstops = []
            for seq, params in enumerate(tripstop_params):
                params['tripday'] = tripday
                params['seq'] = seq
                tripstops.append(TripStop.objects.create(**params))
            return pattern_bounds, data_bounds, tripstops
        logger.warning("Can't find stops for TripDay %s!" % tripday)
        return

class Trip(models.Model):
    '''A bus trip on a TripDay'''
    tripday = models.ForeignKey(TripDay)
    pattern = models.ForeignKey(Pattern)
    seq = models.IntegerField()

    class Meta:
        unique_together = ordering = ('tripday', 'seq', 'pattern')

    def __unicode__(self):
        return "%s - %s" % (self.tripday, self.seq)

class TripTime(models.Model):
    '''A stop time for a Trip'''
    trip = models.ForeignKey(Trip)
    tripstop = models.ForeignKey(TripStop)
    time = models.CharField(max_length=5)

    def __unicode__(self):
        return "%s - %s" % (self.tripstop, self.time)

    class Meta:
        unique_together = ordering = ('trip', 'tripstop')
