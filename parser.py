#!/usr/bin/env python
# encoding: utf-8
import csv
import dbfpy.dbf
import getopt
import os
import sys


def latlon_transformer(value):
    '''Transforms latitude and longitude values to valid degree decimals'''
    return float(value) / 1000000


def convert_color(value):
    '''Convert integer value into a hex color value'''
    return '%06x' % value


MAPPING = {'stops': {'file': 'STOPS/stops.dbf',
                     'fields': (('StopId', 'stop_id'),
                                ('StopName', 'stop_name'),
                                ('lat', 'stop_lat', latlon_transformer),
                                ('lon', 'stop_lon', latlon_transformer),
                                ('SiteName', 'stop_desc'),
                                ('StopAbbr', 'stop_code'))},
           'routes': {'file': 'lines/line.dbf',
                      'fields': (('LineID', 'route_id'),
                                 ('LineAbbr', 'route_short_name'),
                                 ('LineName', 'route_long_name'),
                                 ('', 'route_type', lambda x: 3),
                                 ('LineColor', 'route_color', convert_color))},
           #'calendar': {},
           #'trips': {},
          }


def parse(dbf_folder='./', destination_folder='./', mapping=MAPPING):
    '''Parse MTTA dbf files into Google Transit csv files'''
    for f in mapping:
        feed = mapping[f]
        dbf_file = '%s%s' % (dbf_folder, feed['file'])
        print 'parsing %s' % dbf_file
        db_f = dbfpy.dbf.Dbf(dbf_file, readOnly=True)
        output_name = os.path.splitext(os.path.basename(f))[0]
        rows = []
        header = []
        for fh in feed['fields']:
            header.append(fh[1])
        rows.append(header)
        for record in db_f:
            row = []
            for field in feed['fields']:
                if field[0]:
                    field_value = record[field[0]]
                if len(field) >= 3 and callable(field[2]):
                    field_value = field[2](field_value)
                row.append(field_value)
            rows.append(row)
        if rows:
            with open('%s%s.txt' % (destination_folder,
                                    output_name), 'w') as f:
                writer = csv.writer(f)
                writer.writerows(rows)


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


help_message = '''
Convert a folder of DBF files to a sqlite database.  Options:

 -h, --help   - This help
 -d, --dbf    - The path to the DBF files (default ./)
 -o, --out - The output directory (default ./)
'''


def main(argv=None):
    if argv is None:
        argv = sys.argv
    base_path = os.path.abspath(os.path.dirname(__file__))
    dbf_folder = os.path.join(base_path, './')
    destination = os.path.join(base_path, './')
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hd:o:v",
                ["help", "dbf=", "out="])
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        for option, value in opts:
            if option == "-v":
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-d", "--dbf"):
                dbf_folder = value
            if option in ("-o", "--out"):
                destination = value

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 1

    parse(dbf_folder, destination)
    return 0

if __name__ == "__main__":
    sys.exit(main())
