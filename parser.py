#!/usr/bin/env python
# encoding: utf-8
'''
Convert a folder of DBF files to Google Transit Feed files.  Options:

 -h, --help     - This help
 -v, --verbose  - Print progress messages
 -d, --database - An optional persistant SQLite3 database
 -i, --in       - The input directory (default ./input)
 -o, --out      - The output directory (default ./output)
 --validate     - Run Google's validator, exit non-zero if invalid
'''

import csv
import getopt
import glob
import os
import shutil
import sqlite3
import sys
import zipfile

import dbf_parser
import stop_trip_parser

DATABASE_SCHEMA = {
    'stops': (
        ('stop_id', 'int', True),
        ('stop_name', 'text', True),
        ('stop_lat', 'int', True),
        ('stop_lon', 'int', True),
        ('stop_desc', 'text', True),
        ('stop_code', 'text', True),
        ('active', 'int', False),
    ),
    'routes': (
        ('route_id', 'int', True),
        ('route_short_name', 'text', True),
        ('route_long_name', 'text', True),
        ('route_type', 'int', True),
        ('route_color', 'text', True),
        ('route_text_color', 'text', True),
        ('active', 'int', False),
    ),
    'line_stops': (
        ('stop_id', 'int', False),
        ('stop_abbr', 'text', False),
        ('node_abbr', 'text', False),
        ('line_no', 'text', False),
        ('line_dir', 'text', False),
        ('sequence', 'text', False),
        ('active', 'int', False),
    ),
    'line_nodes': (
        ('stop_id', 'int', False),
        ('stop_abbr', 'text', False),
        ('node_abbr', 'text', False),
        ('line_no', 'text', False),
        ('line_dir', 'text', False),
        ('sequence', 'text', False),
        ('active', 'int', False),
    ),
    'trips': (
        ('route_id', 'int', True),
        ('service_id', 'int', True),
        ('trip_id', 'text', True),
        ('trip_headsign', 'int', True),
        ('direction_id', 'int', True),
        ('active', 'int', False),
    ),
    'stop_times': (
        ('trip_id', 'text', True),
        ('arrival_time', 'text', True),
        ('departure_time', 'text', True),
        ('stop_id', 'int', True),
        ('stop_sequence', 'int', True),
        ('x_stop_abbr', 'text', False),
        ('active', 'int', False),
    ),
}


def create_db(database, schema, drop_first=True):
    '''Create the database schema'''
    sql = create_db_sql(schema, drop_first)
    database.executescript(sql)
    database.commit()


def create_db_sql(schema, drop_first):
    '''Return SQL for creating the database schema'''

    sql = []
    if drop_first:
        for table_name in schema.keys():
            sql.append('DROP TABLE IF EXISTS %s;' % table_name)

    for table_name, column_data in schema.items():
        sql.append('CREATE TABLE %s' % table_name + ' (' +
            ', '.join(['%s %s' % (cname, ctype) for
                cname, ctype, _ in column_data]) + ');')

    return '\n'.join(sql)


def write_gtf_text(database, destination_folder, schema):

    cur = database.cursor()
    out_files = []
    for table_name, column_data in schema.items():
        out_name = os.path.join(destination_folder, table_name + '.txt')
        columns = [name for name, _, include in column_data if include]
        if len(columns) == 0:
            continue
        out_files.append(out_name)
        sql = ('SELECT active, ' + ', '.join(columns) +
            ' FROM ' + table_name + ';')

        def to_csv_field(val):
            if isinstance(val, unicode):
                return val.encode('utf-8')
            else:
                return val

        with open(out_name, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in cur.execute(sql):
                if row[0] == 1:
                    csv_row = [to_csv_field(c) for c in row[1:]]
                    writer.writerow(csv_row)
    cur.close()
    return out_files


def load_same_stops(same_stops_path, verbose=True):
    same_stops = dict()
    try:
        with open(same_stops_path, 'r') as f:
            reader = csv.reader(f)
            reader.next()  # Throw away headers
            for row in reader:
                stop_id, stop_name, replacement_id, replacement_name = row
                same_stops[int(stop_id)] = int(replacement_id)
    except IOError:
        # File doesn't exist
        if verbose:
            print 'Error reading "%s" - continuing without same stop checking' % same_stops_path
        
    return same_stops

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    verbose = False
    validate = False
    base_path = os.path.abspath(os.path.dirname(__file__))
    input_folder = os.path.join(base_path, 'input')
    destination = os.path.join(base_path, 'output', 'feed')
    fixups_folder = os.path.join(base_path, 'fixups')
    database_path = ':memory:'
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hi:d:o:v",
                ["help", "in=", "database=", "out=", "verbose", "validate"])
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        for option, value in opts:
            if option in ("-v", "--verbose"):
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(__doc__)
            if option in ("-i", "--input"):
                input_folder = value
            if option in ("-d", "--database"):
                database_path = value
            if option in ("-o", "--out"):
                destination = value
            if option in ("--validate", ):
                validate = True

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 1

    # Create the database
    schema = DATABASE_SCHEMA
    database = sqlite3.connect(database_path)
    create_db(database, schema, True)

    # Read Same Stops file
    same_stops_path = os.path.join(fixups_folder, 'same_stops.csv')
    same_stops = load_same_stops(same_stops_path)

    # Read DBF files
    for path, dirs, files in os.walk(input_folder):
        for f in files:
            full_path = os.path.abspath(os.path.join(path, f))
            if dbf_parser.is_useful(full_path):
                if verbose:
                    print "Parsing DBF file '%s'" % full_path
                dbf_parser.read(full_path, database, verbose)

    # Read trip files
    for path, dirs, files in os.walk(input_folder):
        files.sort()
        for f in files:
            full_path = os.path.abspath(os.path.join(path, f))
            if stop_trip_parser.is_useful(full_path):
                if verbose:
                    print "Parsing trip file '%s'" % full_path
                stop_trip_parser.read(full_path, database, verbose,
                                      same_stops)

    # Activate stops if they are in a schedule
    database.execute('UPDATE stops SET active=1 WHERE stops.stop_id IN' +
        ' (SELECT DISTINCT stop_times.stop_id FROM stop_times);')
    database.commit()

    # Write from database to Google Transit Feed files
    out_files = write_gtf_text(database, destination, schema)

    # Copy files from static folder
    static_folder = os.path.join(base_path, "static")
    for f in glob.glob(os.path.join(base_path, "static", "*.txt")):
        filename = os.path.split(f)[1]
        dest_path = os.path.join(destination, filename)
        shutil.copy(f, dest_path)
        out_files.append(dest_path)

    # Write feed.zip
    zip_path = os.path.join(destination, 'feed.zip')
    feed_zip = zipfile.ZipFile(zip_path, 'w')
    for f in out_files:
        filename = os.path.split(f)[1]
        feed_zip.write(f, filename)
    feed_zip.close()

    # Optionally validate
    if validate:
        if verbose:
            print "Validating"
        sys.path.append('./transitfeed')
        import feedvalidator

        output = os.path.join(destination, 'validation-results.html')
        old_argv = sys.argv
        sys.argv = [sys.argv[0], zip_path, '--output=%s' % output]
        return feedvalidator.main()
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())
