#!/usr/bin/env python
# encoding: utf-8
'''
Convert a folder of DBF files to Google Transit Feed files.  Options:

 -h, --help     - This help
 -d, --database - An optional persistant SQLite3 database
 -i, --in       - The input directory (default ./input)
 -o, --out      - The output directory (default ./output)
'''

import csv
import getopt
import os
import sqlite3
import sys

import dbf_parser
import trip_parser

DATABASE_SCHEMA = {
    'stops': (
        ('stop_id', 'int', True),
        ('stop_name', 'str', True),
        ('stop_lat', 'int', True),
        ('stop_lon', 'int', True),
        ('stop_desc', 'str', True),
        ('stop_code', 'str', True),
    ),
    'routes': (
        ('route_id', 'int', True),
        ('route_short_name', 'str', True),
        ('route_long_name', 'str', True),
        ('route_type', 'int', True),
        ('route_color', 'str', True),
    ),
    'line_stops': (
        ('stop_id', 'int', False),
        ('stop_abbr', 'text', False),
        ('line_no', 'text', False),
        ('line_dir', 'text', False),
    ),
    'trips' : (
        ('route_id', 'int', True),
        ('service_id', 'int', True),
        ('trip_id', 'str', True),
        ('trip_headsign', 'int', True),
        ('direction_id', 'int', True),
    ),
    'stop_times' : (
        ('trip_id', 'str', True),
        ('arrival_time', 'str', True),
        ('departure_time', 'str', True),
        ('stop_id', 'int', True),
        ('stop_sequence', 'int', True),
        ('x_stop_abbr','str', False),
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
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table_name + ';'

        def to_csv_field(val):
            if isinstance(val, unicode):
                out = val.encode('utf-8')
                if out.startswith('sqlite_val('):
                    out = out[11:-1]
                return out
            else:
                return val

        with open(out_name, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in cur.execute(sql):
                csv_row = [to_csv_field(c) for c in row]
                writer.writerow(csv_row)
    cur.close()

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    verbose = False
    base_path = os.path.abspath(os.path.dirname(__file__))
    input_folder = os.path.join(base_path, 'input')
    destination = os.path.join(base_path, 'output', 'feed')
    database_path = ':memory:'
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hi:d:o:v",
                ["help", "in=", "database=", "out=", "verbose"])
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

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 1

    # Create the database
    schema = DATABASE_SCHEMA
    database = sqlite3.connect(database_path)
    create_db(database, schema, True)
    
    # Read DBF files
    for path, dirs, files in os.walk(input_folder):
        for f in files:
            full_path = os.path.abspath(os.path.join(path, f))
            if dbf_parser.is_useful(full_path):
                if verbose:
                    print "Parsing DBF file '%s'" % full_path
                dbf_parser.read(full_path, database)
    
    # Read trip files
    for path, dirs, files in os.walk(input_folder):
        for f in files:
            full_path = os.path.abspath(os.path.join(path, f))
            if trip_parser.is_useful(full_path):
                if verbose:
                    print "Parsing trip file '%s'" % full_path
                trip_parser.read(full_path, database)
        
    # Write from database to Google Transit Feed files
    out_files = write_gtf_text(database, destination, schema)
    
    # TODO: Write zip file
    return 0

if __name__ == "__main__":
    sys.exit(main())