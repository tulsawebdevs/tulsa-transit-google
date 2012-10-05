from collections import defaultdict
import datetime
import logging
import re
import os

from django.db import models
from django_extensions.db.fields.json import JSONField
import dbfpy.dbf
import shapefile

from mtta.utils import haversine
from multigtfs.models import Feed

logger = logging.getLogger(__name__)


def _mockable_open(path, mode=None):
    return open(path, mode)


def _force_to_file(obj):
    '''Force to a file-like object

    Strings are treated like file paths
    None are returned
    Other objects should already have a 'read' attribute.
    '''
    if isinstance(obj, basestring):
        name = obj
    elif hasattr(obj, 'name'):
        name = obj.name
    elif obj is None:
        return None
    else:
        name = '<stream>'
    if hasattr(obj, 'read'):
        filelike = obj
    else:
        filelike = _mockable_open(obj, 'rb')
    if not hasattr(filelike, 'name'):
        filelike.name = name
    return filelike


class SignUp(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    feeds = models.ManyToManyField(Feed, through='SignupExports')
    _unset_name = '<unset>'
    _data_file_names = (
        ('lines', 'line'),
        ('patterns', 'pattern'),
        ('stops', 'stop'),
        ('stopsbyline',),
        ('stopsbypattern',),
    )
    _names_file = 'NewFieldNames.txt'

    def import_folder(self, folder):
        data_files = defaultdict(dict)
        stop_trips = []
        stop_trips_start = 'Stop Trips'
        for path, dirs, files in os.walk(folder):
            data_name = None
            for f in files:
                full_path = os.path.abspath(os.path.join(path, f))
                full_name = f.lower()
                name, ext = os.path.splitext(full_name)
                ext = ext.replace('.', '')
                for nameset in self._data_file_names:
                    if name in nameset:
                        data_name = nameset[0]
                        data_files[data_name][ext] = full_path

                if ext == 'txt':
                    with open(full_path, 'r') as candidate:
                        first_bits = candidate.read(len(stop_trips_start))
                    if (first_bits == stop_trips_start):
                        stop_trips.append(full_path)
            if data_name and self._names_file in files:
                full_path = os.path.abspath(
                    os.path.join(path, self._names_file))
                data_files[data_name][self._names_file] = full_path

        for nameset in self._data_file_names:
            key = nameset[0]
            if key not in data_files.keys():
                raise Exception('No %s found in path %s' % (key, folder))
        if not stop_trips:
            raise Exception('No schedules found in path %s' % folder)
        self._import(data_files, stop_trips)

    def _import(self, data_files, stop_trips):
        '''Import a set of ESRI Shapfiles and Stop Trip schedules'''

        # Get the important parts, so we'll raise a KeyError early
        lines_dbf = data_files['lines']['dbf']
        lines_names = data_files['lines'].get(self._names_file)
        patterns_dbf = data_files['patterns']['dbf']
        patterns_shp = data_files['patterns']['shp']
        patterns_shx = data_files['patterns'].get('shx')
        stops_dbf = data_files['stops']['dbf']
        stops_names = data_files['stops'].get(self._names_file)
        stopsbyline_dbf = data_files['stopsbyline']['dbf']
        stopsbyline_names = data_files['stopsbyline'].get(self._names_file)
        stopsbypattern_dbf = data_files['stopsbypattern']['dbf']
        stopsbypattern_names = data_files['stopsbypattern'].get(
            self._names_file)

        # Run the model-specific imports
        if not self.service_set.exists():
            Service.create_from_defaults(self)
        Line.import_dbf(self, lines_dbf, lines_names)
        Pattern.import_shp(
            self, dbf=patterns_dbf, shp=patterns_shp, shx=patterns_shx)
        Stop.import_dbf(self, stops_dbf, stops_names)
        StopByLine.import_dbf(self, stopsbyline_dbf, stopsbyline_names)
        StopByPattern.import_dbf(
            self, stopsbypattern_dbf, stopsbypattern_names)
        for schedule in stop_trips:
            TripDay.import_schedule(self, schedule)

    def copy_to_feed(self):
        feed = Feed.objects.create(name=self.name)
        signup_export = SignupExports.objects.create(
            signup=self, feed=feed, started=feed.created)
        agency = AgencyInfo.objects.get(pk=1)
        agency.copy_to_feed(feed)
        feedinfo = FeedInfo.objects.get(pk=1)
        feedinfo.copy_to_feed(feed)
        for line in self.line_set.all():
            logger.info('Exporting data for line %s...' % line)
            line.copy_to_feed(feed)
        signup_export.finished = datetime.datetime.now()
        return feed

    def __unicode__(self):
        return "%s-%s" % (self.id, self.name or '(No Name)')


class SignupExports(models.Model):
    signup = models.ForeignKey(SignUp)
    feed = models.ForeignKey(Feed)
    started = models.DateTimeField()
    finished = models.DateTimeField(null=True, blank=True)


class ShapeAttributes(models.Model):
    signup = models.ForeignKey(SignUp)
    name = models.CharField(max_length=20)
    attributes = JSONField(default=[])


class AgencyInfo(models.Model):
    '''MTTA information used by GTFS feed'''
    name = models.CharField(max_length=20)
    url = models.URLField()
    timezone = models.CharField(max_length=20)
    lang = models.CharField(max_length=2)
    phone = models.CharField(max_length=20)
    fare_url = models.URLField()

    def copy_to_feed(self, feed):
        feed.agency_set.get_or_create(
            name=self.name, url=self.url, timezone=self.timezone,
            lang=self.lang, phone=self.phone, fare_url=self.fare_url)


class FeedInfo(models.Model):
    '''Tulsa Web Devs information used by GTFS feed'''
    name = models.CharField(max_length=20)
    url = models.URLField()
    lang = models.CharField(max_length=2)
    version = models.CharField(max_length=20, null=True, blank=True)

    def copy_to_feed(self, feed):
        feed.feedinfo_set.get_or_create(
            publisher_name=self.name, publisher_url=self.url, lang=self.lang)

class DbfBase(models.Model):
    '''Base class for models from .DBF data'''
    attributes = JSONField(default=[])

    class Meta:
        abstract = True

    @classmethod
    def read_dbf(cls, signup, dbf_file, names_file):
        '''Read and summarize data from a DBF file


        Kwargs:
            signup: The sign-up to associate this item with
            dbf_file: The DBF file
            names_file: The 'NewFieldNames.txt' file

        Returns: tuple of:
            fields - List of dictionaries describing the DBF fields, stored in
                ShapeAttributes as well
            rows - List of dictionaries for each DBF row, with only the
                important values (either used in the model fields, or value is
                different from 50% of the other values for that field)
                Uses the class variable _dbf_mapping to decide if a
                low-information variable should be included.
        '''

        # Get the field names we're looking to store in the database
        assert hasattr(cls, '_dbf_mapping')
        used_names = dict([(a, 0) for a, b in cls._dbf_mapping])

        # Parse the names file for long names
        if hasattr(names_file, 'seek'):
            names_file.seek(0)
        names_content = names_file.read()
        long_name_pairs = re.findall('(\w+) for (\w+)', names_content)
        long_names = dict(
            [(k.upper(), v.upper()) for (k, v) in long_name_pairs])

        # Read all the rows
        db_f = dbfpy.dbf.Dbf(dbf_file, readOnly=True)
        rows = [row.asList() for row in db_f]

        # Read the field info, count value frequencies
        fields = []
        for index, field in enumerate(db_f.fieldDefs):
            name, type_code, length, field_default_value = field.fieldInfo()

            # Long names come from the names file
            long_name = long_names.get(name.upper())
            if not long_name and name.upper().startswith('TPFIELD'):
                # Line has both line directions in same table
                long_name = long_names.get(name.upper()[:-1])
                if long_name:
                    long_name += name[-1]

            # Find the value variance
            value_counts = defaultdict(int)
            for row in rows:
                val = row[index]
                value_counts[val] += 1

            # Find the top values
            values_by_count = [(c, v) for v, c in value_counts.items()]
            values_by_count.sort(reverse=True)
            top_count, top_value = values_by_count[0]

            # Decide if a default value should be used for the field
            if name in used_names:
                used_names[name] += 1
                default_value = None
            elif long_name in used_names:
                used_names[long_name] += 1
                default_value = None
            elif top_count > (0.5 * len(rows)):
                if isinstance(top_value, basestring):
                    default_value = unicode(top_value, encoding='latin-1')
                else:
                    default_value = top_value
            else:
                default_value = None

            # Store the field definition
            field_params = dict(
                name=name, type_code=type_code, length=length,
                default_value=default_value, index=index,
                top_values=values_by_count[:5])
            if long_name:
                field_params['long_name'] = long_name
            fields.append(field_params)

        # Check used fields:
        for name, count in used_names.items():
            if count != 1:
                msg = '%s appears %d times in DBF fields,' % (name, count)
                msg += ' only first will be used:'
                for field in fields:
                    if field['name'] == name or field.get('long_name') == name:
                        msg += '\n  ' + str(field)
                logger.warning(msg)

        # Store the field definitions in the database
        ShapeAttributes.objects.create(
            signup=signup, attributes=fields, name=cls.__name__)

        # Convert the rows to minimized dicts
        row_summaries = []
        for row in rows:
            summary = list()
            assert len(row) == len(fields)
            for val, field in zip(row, fields):
                default = field['default_value']
                if isinstance(val, basestring):
                    val = unicode(val, encoding='latin-1')
                if (default is None) or (val != default):
                    summary.append(dict(
                        name=field['name'], index=field['index'], value=val))
                    if 'long_name' in field:
                        summary[-1]['long_name'] = field['long_name']
            row_summaries.append(summary)
        return fields, row_summaries

    @classmethod
    def import_dbf(cls, signup, dbf, names):
        '''Import a DBF as several objects for an instance

        Kwargs:
            signup: The sign-up to associate this item with
            dbf: The DBF file or the path to the file
            names: The 'NewFieldNames.txt' file or the path to the file

        This function uses class items to customize behaviour:
        - _dbf_mapping (required) maps DBF column names to model field names
        - funtions named like 'convert_DBFNAME' convert the DBF value to the
          field value
        - create_from_dbf is used instead of create when associated models
          need to be created
        '''
        assert hasattr(cls, '_dbf_mapping')
        dbf_file = _force_to_file(dbf)
        names_file = _force_to_file(names)
        my_name = cls.__name__
        logger.info(
            'Reading %s data from %s...' % (my_name, dbf_file.name))

        dbf_fields, dbf_rows = cls.read_dbf(signup, dbf_file, names_file)
        model_params = []
        for row in dbf_rows:
            # Collect DBF values from row
            values = dict()
            for item in row:
                name = item['name']
                long_name = item.get('long_name')
                value = item['value']
                if name not in values:
                    values[name] = value
                if long_name and long_name not in values:
                    values[long_name] = value

            # Map to model fields
            params = dict(attributes=row)
            for dbf_name, field_name in cls._dbf_mapping:
                value = values[dbf_name]
                converter = getattr(cls, 'convert_' + dbf_name.upper(), None)
                if converter:
                    value = converter(value)
                params[field_name] = value
            model_params.append(params)

        # Create the database entries
        creator = getattr(cls, 'create_from_dbf', cls.objects.create)
        created_counts = defaultdict(int)
        for params in model_params:
            obj = creator(signup=signup, **params)
            if isinstance(obj, DbfBase):
                created_counts[obj.__class__.__name__] += 1
            else:
                for o in obj:
                    created_counts[o.__class__.__name__] += 1

        # Report on what was done
        counts = [(created_counts.pop(my_name), my_name)]
        for name in sorted(created_counts.keys()):
            counts.append((created_counts[name], name))
        msg = 'Read '
        fmt = lambda c, n: '%d %s%s' % (c, n, 's' if c > 1 else '')
        if len(counts) > 2:
            msg += ', '.join(fmt(*c) for c in counts[:-1])
            msg += ', and %s' % fmt(*counts[-1])
        else:
            msg += fmt(*counts[0])
            if len(counts) == 2:
                msg += ' and %s' % fmt(*counts[1])
        msg += ' from %s' % dbf_file.name
        logger.info(msg)

    @classmethod
    def convert_latlon(cls, value):
        '''Convert a DBF lat/lon to a string'''
        raw = str(value)
        return raw[:-6] + '.' + raw[-6:]


class Line(DbfBase):
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

    # Map DBF source columns to model fields
    _dbf_mapping = (
        ('LINEID', 'line_id'),
        ('LINEABBR', 'line_abbr'),
        ('LINENAME', 'line_name'),
        ('LINECOLOR', 'line_color'),
        ('LINETYPE', 'line_type'),
        ('LINEDIRID0', 'linedirid0'),
        ('DIRECTIONNAME0', 'directionname0'),
        ('LINEDIRID1', 'linedirid1'),
        ('DIRECTIONNAME1', 'directionname1'))

    @classmethod
    def create_from_dbf(cls, **params):
        '''Create Line and associated LineDirections from DBF data'''
        ld0_params = dict(
            linedir_id=params.pop('linedirid0'),
            name=params.pop('directionname0'))
        ld1_params = dict(
            linedir_id=params.pop('linedirid1'),
            name=params.pop('directionname1'))
        line = cls.objects.create(**params)
        linedirs = []
        if ld0_params['linedir_id']:
            linedir0 = LineDirection.objects.create(line=line, **ld0_params)
            linedirs.append(linedir0)
        if ld1_params['linedir_id']:
            linedir1 = LineDirection.objects.create(line=line, **ld1_params)
            linedirs.append(linedir1)
        return [line] + linedirs

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
        return self.line_abbr.replace('FLEX', 'FL').replace('SFLX', 'SF')

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
    def import_shp(cls, signup, dbf, shp, shx=None):
        dbf_file = _force_to_file(dbf)
        shp_file = _force_to_file(shp)
        shx_file = _force_to_file(shx)
        logger.info(
            'Parsing Pattern Shapes (dbf=%s, shp=%s, %s)' %
            (dbf_file.name, shp_file.name,
            ('shx=%s' % shx_file.name) if shx_file else 'no shx'))
        sf = shapefile.Reader(
            dbf=dbf_file, shp=shp_file, shx=shx_file)
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
            # For debugging adding and discarding segments
            def log_action(msg, n1, n2):
                logger.info(
                    ' Pattern %s for linedir %s of line %s: %s'
                    ' (%0.5f, %0.5f)->(%0.5f, %0.5f) (%0.1f meters)' % (
                        self, self.linedir, self.linedir.line, msg,
                        n2[0], n2[1], n3[0], n3[1],
                        1000.0 * node_dist(n2, n3)))

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
                        line.extend((n1, n2, n3, n4))
                    else:
                        log_action('Discarding first segment', n2, n3)
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
                    if n1 == n2 or n2 == n3:
                        line.append(n3)
                    elif node_dist(n1, n2) < min_add_dist:
                        log_action('Adding segment', n1, n2)
                        line.extend((n2, n3))
                    else:
                        log_action('Discarding segment', n2, n2)
                else:
                    # Collect the first segment for later
                    first_nodes = (node1, node2)
            self.fixed_pattern = line
            self.save()
        return self.fixed_pattern


class Stop(DbfBase):
    '''A stop from stops.dbf'''
    signup = models.ForeignKey(SignUp)
    stop_id = models.IntegerField(db_index=True)
    stop_abbr = models.CharField(max_length=8, db_index=True)
    stop_name = models.CharField(max_length=50)
    node_abbr = models.CharField(max_length=8, blank=True)
    site_name = models.CharField(max_length=80, blank=True)
    lat = models.DecimalField(
        'Latitude', max_digits=13, decimal_places=8,
        help_text='WGS 84 latitude of stop or station')
    lon = models.DecimalField(
        'Longitude', max_digits=13, decimal_places=8,
        help_text='WGS 84 longtitude of stop or station')
    in_service = models.BooleanField()

    class Meta:
        unique_together = ('signup', 'stop_id')
        ordering = ('signup', 'stop_id')

    def __unicode__(self):
        return "%s-%s" % (self.stop_id, self.stop_abbr)

    # Map DBF source columns to model fields
    _dbf_mapping = (
        ('STOPID', 'stop_id'),
        ('STOPABBR', 'stop_abbr'),
        ('STOPNAME', 'stop_name'),
        ('NODEABBR', 'node_abbr'),
        ('SITENAME', 'site_name'),
        ('LAT', 'lat'),
        ('LON', 'lon'),
        ('INSERVICE', 'in_service'))

    convert_LAT = DbfBase.convert_latlon
    convert_LON = DbfBase.convert_latlon

    def copy_to_feed(self, feed):
        gtfs_stop, created = feed.stop_set.get_or_create(
            stop_id=self.stop_id, defaults=dict(
                name=self.stop_name, lat=self.lat, lon=self.lon,
                desc=self.site_name, location_type=0))
        return gtfs_stop


class Node(models.Model):
    '''A node inferred from StopsByLine or StopsByPattern

    We don't have a direct database of nodes, but some stops are identified as
    nodes in the StopsBy* data.
    '''
    signup = models.ForeignKey(SignUp)
    stops = models.ManyToManyField(Stop, related_name='nodes')
    node_id = models.IntegerField(db_index=True)
    node_abbr = models.CharField(max_length=8)
    node_name = models.CharField(max_length=50)

    def __unicode__(self):
        return "%s-%s" % (self.node_id, self.node_abbr)

    class Meta:
        ordering = ('node_id',)


class StopByLine(DbfBase):
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

    # Map DBF source columns to model fields
    _dbf_mapping = (
        ('STOPID', 'stop_id'),
        ('LINEDIRID', 'linedir_id'),
        ('SEQUENCE', 'seq'),
        ('STOPTYPE', 'stop_type'),
        ('NODEID', 'node_id'),
        ('NODEABBR', 'node_abbr'),
        ('NODENAME', 'node_name'))

    @classmethod
    def create_from_dbf(cls, **params):
        signup = params.pop('signup')
        stop_id = params.pop('stop_id')
        stop = Stop.objects.get(signup=signup, stop_id=stop_id)

        linedir_id = params.pop('linedir_id')
        linedir = LineDirection.objects.get(
            line__signup=signup, linedir_id=linedir_id)

        seq = params.pop('seq')
        stop_type = params.pop('stop_type')
        attributes = params.pop('attributes')
        node = None
        node_created = False
        if stop_type == 'N':
            node, node_created = signup.node_set.get_or_create(**params)
            node.stops.add(stop)
        sbl = cls.objects.create(
            stop=stop, linedir=linedir, seq=seq, node=node,
            attributes=attributes)
        if node_created:
            return [sbl, node]
        else:
            return sbl


class StopByPattern(DbfBase):
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

    # Map DBF source columns to model fields
    _dbf_mapping = (
        ('STOPID', 'stop_id'),
        ('LINEDIRID', 'linedir_id'),
        ('PATTERNID', 'pattern_id'),
        ('SEQUENCE', 'seq'),
        ('STOPTYPE', 'stop_type'),
        ('NODEID', 'node_id'),
        ('NODEABBR', 'node_abbr'),
        ('NODENAME', 'node_name'))

    @classmethod
    def create_from_dbf(cls, **params):
        signup = params.pop('signup')
        stop_id = params.pop('stop_id')
        stop = Stop.objects.get(signup=signup, stop_id=stop_id)

        linedir_id = params.pop('linedir_id')
        linedir = LineDirection.objects.get(
            line__signup=signup, linedir_id=linedir_id)

        pattern_id = params.pop('pattern_id')
        pattern = Pattern.objects.get(
            linedir=linedir, pattern_id=pattern_id)

        seq = params.pop('seq')
        stop_type = params.pop('stop_type')
        attributes = params.pop('attributes')
        node = None
        node_created = False
        if stop_type == 'N':
            node, node_created = signup.node_set.get_or_create(**params)
            node.stops.add(stop)
        sbp = cls.objects.create(
            stop=stop, linedir=linedir, pattern=pattern, seq=seq, node=node,
            attributes=attributes)
        if node_created:
            return [sbp, node]
        else:
            return sbp


class Service(models.Model):
    signup = models.ForeignKey(SignUp, null=True, blank=True)
    service_id = models.IntegerField(
        choices=((1, 'Weekday'), (2, 'Saturday')))
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()
    saturday = models.BooleanField()
    sunday = models.BooleanField()
    start_date = models.DateField()
    end_date = models.DateField()

    @classmethod
    def create_from_defaults(cls, signup):
        for default in cls.objects.filter(signup=None):
            service = cls.objects.create(
                signup=signup, service_id=default.service_id,
                monday=default.monday, tuesday=default.tuesday,
                wednesday=default.wednesday, thursday=default.thursday,
                friday=default.friday, saturday=default.saturday,
                sunday=default.sunday, start_date=default.start_date,
                end_date=default.end_date)
            for def_exception in default.serviceexception_set.filter(
                    date__gte=default.start_date, date__lte=default.end_date):
                service.serviceexception_set.create(
                    date=def_exception.date,
                    exception_type=def_exception.exception_type)

    class Meta:
        unique_together = ordering = ('signup', 'service_id')

    def __unicode__(self):
        return '%s-%s' % (self.service_id, self.get_service_id_display())

    def copy_to_feed(self, feed):
        gtfs_service, created = feed.service_set.get_or_create(
            service_id=str(self.service_id), defaults=dict(
                monday=self.monday, tuesday=self.tuesday,
                wednesday=self.wednesday, thursday=self.thursday,
                friday=self.friday, saturday=self.saturday,
                sunday=self.sunday, start_date=self.start_date,
                end_date=self.end_date))
        for exception in self.serviceexception_set.filter(
                date__gte=self.start_date, date__lte=self.end_date):
            exception.copy_to_feed(feed, gtfs_service)
        return gtfs_service


class ServiceException(models.Model):
    service = models.ForeignKey(Service)
    date = models.DateField()
    exception_type = models.IntegerField(
        choices=((1, 'Add Service'), (2, 'Remove Service')))

    def copy_to_feed(self, feed, gtfs_service):
        servicedate_set = gtfs_service.servicedate_set
        gtfs_service_exception, created = servicedate_set.get_or_create(
            service=gtfs_service, date=self.date,
            exception_type=self.exception_type)


class TripDay(models.Model):
    '''A set of trips for a line direction by service day'''
    linedir = models.ForeignKey(LineDirection)
    service = models.ForeignKey(Service)

    class Meta:
        unique_together = ordering = ('linedir', 'service')

    def __unicode__(self):
        return '%s-%s' % (self.linedir.linedir_id, self.service.service_id)

    @classmethod
    def import_schedule(cls, signup, path_or_file):
        schedule = _force_to_file(path_or_file)
        logger.info('Parsing Trips from %s...' % schedule.name)

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
        for linenum, linein in enumerate(schedule.readlines()):
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
                    service = signup.service_set.get(service_id=service_id)
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
                    pattern_name = raw_pat.strip()
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
    stop_abbr = models.CharField(max_length=8)
    node = models.ForeignKey(Node, null=True, blank=True)
    node_abbr = models.CharField(max_length=8, blank=True)
    seq = models.IntegerField()
    scheduled = models.BooleanField(help_text='Stop is a scheduled stop.')
    arrival = models.OneToOneField(
        'TripStop', related_name='departure', null=True, blank=True)

    class Meta:
        unique_together = ordering = ('tripday', 'seq')

    def __unicode__(self):
        return "%s-%02d" % (self.tripday, self.seq)

    @classmethod
    def parse_schedule_for_tripstops(cls, tripday, col_lines):
        assert len(col_lines) == 2 or len(col_lines) == 3
        assert set(col_lines[-1]) == set(' ~'),\
            'Last col_line must be schedule column designator'

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
            field_bounds.append((start, column + 1))
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
        data_cols = columns[data_col:]
        line_type = tripday.linedir.line.line_type
        if line_type == 'FX':
            tripstop_params = cls._parse_normal_columns(tripday, data_cols)
        else:
            assert line_type == 'FL'
            tripstop_params = cls._parse_flex_columns(tripday, data_cols)

        tripstops = []
        last_params = dict()
        for seq, params in enumerate(tripstop_params):
            params['tripday'] = tripday
            params['seq'] = seq
            if 'stop' in params and last_params.get('stop') == params['stop']:
                params['arrival'] = tripstops[-1]
            tripstops.append(TripStop.objects.create(**params))
            last_params = params
        return pattern_bounds, data_bounds, tripstops

    @classmethod
    def _parse_normal_columns(cls, tripday, col_lines):
        '''Parse the node/stop columns on a normal line'''
        linedir = tripday.linedir
        tripstop_params = []
        stops_by_line_matches = True
        for seq, abbrs in enumerate(col_lines):
            node_abbr, stop_abbr = abbrs
            sbl = linedir.stopbyline_set.get(seq=(seq + 1))
            node = sbl.node
            stop = sbl.stop
            if node_abbr:
                if ((not node or node_abbr != node.node_abbr) and
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
                     node_abbr=node_abbr, scheduled=(node is not None)))
        if not stops_by_line_matches:
            raise Exception('Parsing a normal line failed!')
        return tripstop_params

    @classmethod
    def _parse_flex_columns(cls, tripday, col_lines):
        '''Parse the node/stop columns on a flex line'''
        linedir = tripday.linedir
        signup = linedir.line.signup
        # Find the timing nodes first
        sbls = list(linedir.stopbyline_set.order_by('seq'))
        tripstop_params = []
        for seq, abbrs in enumerate(col_lines):
            node_abbr, stop_abbr = abbrs
            params = dict(
                stop_abbr=stop_abbr, node_abbr=node_abbr, scheduled=False)
            # Look for the node in StopByLine
            if node_abbr:
                for sbl in sbls:
                    node = sbl.node
                    stop = sbl.stop
                    if node and node_abbr == node.node_abbr:
                        params.update(dict(
                            stop=stop, node=node, scheduled=True))
                    elif stop and node_abbr.lower() == stop.node_abbr.lower():
                        params.update(dict(
                            stop=stop, node=None, scheduled=True))
                    elif stop and stop_abbr == stop.stop_abbr:
                        params.update(dict(stop=stop, scheduled=True))
                        if stop.nodes.count() == 1:
                            node = stop.nodes.get()
                            logger.warning(
                                "On tripday %s, no node match for '%s', but"
                                " stop '%s' matches. Using its node '%s'." %
                                (tripday, node_abbr, stop, node))
                            params['node'] = node
                        elif stop.nodes.exists():
                            logger.warning(
                                "On tripday %s, no node match for '%s', but"
                                " stop '%s' matches.  It has multiple nodes"
                                " (%s), so leaving node empty." %
                                (tripday, node_abbr, stop, stop.nodes.all()))
                        else:
                            logger.warning(
                                "On tripday %s, no node match for '%s', but"
                                " stop '%s' matches.  It has no nodes, so"
                                " leaving node empty." %
                                (tripday, node_abbr, stop))
                    else:
                        continue
                    sbls.remove(sbl)
                    break
            tripstop_params.append(params)
        if sbls:
            # We have unmatched scheduled points.  See if the number of
            # StopsByLine left matches the number of unscheduled nodes
            unscheduled_nodes = []
            for param in tripstop_params:
                if param['node_abbr'] and not param['scheduled']:
                    unscheduled_nodes.append(param)
            if len(unscheduled_nodes) == len(sbls):
                for un, sbl in zip(unscheduled_nodes, sbls):
                    logger.warning(
                        "On tripday %s, no match for timing node %s (stop %s)"
                        " in schedule.  Assiging to unscheduled node %s"
                        " (stop %s)." % (
                            tripday, sbl.node, sbl.stop, un['node_abbr'],
                            un['stop_abbr']))
                    un['node'] = sbl.node
                    un['stop'] = sbl.stop
                    un['scheduled'] = True
                    sbls.remove(sbl)
            else:
                for sbl in sbls:
                    logger.error(
                        "On tripday %s, couldn't find timing node %s (stop"
                        " %s) in schedule." % (tripday, sbl.node, sbl.stop))
        # Now for the non-timing stops and nodes
        for seq, params in enumerate(tripstop_params):
            if 'stop' not in params:
                stop_abbr = params['stop_abbr']
                stop = None
                stops = signup.stop_set.filter(
                    stop_abbr=stop_abbr, in_service=True).order_by('stop_id')
                if len(stops) == 1:
                    stop = stops[0]
                elif len(stops) > 1:
                    candidates = []
                    node_abbr = params['node_abbr']
                    for s in stops:
                        if s.node_abbr.lower() == node_abbr.lower():
                            candidates.append(s)
                        elif s.nodes.filter(node_abbr=node_abbr).count() == 1:
                            candidates.append(s.nodes.get(node_abbr=node_abbr))
                    if len(candidates) == 1:
                        stop = candidates[0]
                if stop:
                    params['stop'] = stop
                    if stop.nodes.count() == 1:
                        params['node'] = stop.nodes.get()
                else:
                    logger.warning(
                        "On tripday %s, at trip stop %s, %d stops found for"
                        " stop abbreviation '%s'. Leaving stop unassigned" %
                        (tripday, seq, len(stops), stop_abbr))
        return tripstop_params


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
        if self.time and (self.tripstop.scheduled or force_time):
            time = self.time
        else:
            time = None
        if force_time and not time:
            logger.warning('Skipping TripTime "%s" - needs time' % self)
            return None
        if hasattr(self.tripstop, 'departure'):
            d = self.trip.triptime_set.filter(tripstop=self.tripstop.departure)
            if d.exists():
                departure_time = d[0].time
            else:
                # The departure stop is not part of this trip
                departure_time = time
        elif self.tripstop.arrival:
            a = self.trip.triptime_set.filter(tripstop=self.tripstop.arrival)
            if a.exists():
                # Already included in the departure
                return None
            else:
                # Arrival stop not part of this trip - treat as normal stop
                departure_time = time
        else:
            departure_time = time
        gtfs_stop = self.tripstop.stop.copy_to_feed(feed)
        gtfs_stoptime, created = gtfs_trip.stoptime_set.get_or_create(
            stop=gtfs_stop, stop_sequence=self.tripstop.seq, defaults=dict(
                arrival_time=time, departure_time=departure_time))
        if force_time and not created:
            gtfs_stoptime.arrival_time = time
            gtfs_stoptime.departure_time = departure_time
            gtfs_stoptime.save()
        return gtfs_stoptime
