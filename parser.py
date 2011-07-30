#!/usr/bin/env python
# encoding: utf-8

import csv
import getopt
import os
import sqlite3
import sys

import dbfpy.dbf

def latlon_transformer(value):
    '''Transforms latitude and longitude values to valid degree decimals'''
    try:
        return float(value) / 1000000
    except:
        return value


def convert_color(value):
    '''Convert integer value into a hex color value'''
    try:
        return '%06x' % value
    except:
        return value


def str_exists_validator(value):
    '''validates thats that a string is not empty'''
    try:
        return isinstance(value, str) and len(value) > 0
    except:
        return False


def latlon_validator(value):
    from numbers import Number
    try:
        return isinstance(value, Number) and value != 0
    except:
        return False


'''
Mapping for DBF input files to database.  Fields are:
- DBF Field Name
- Database column name
- DBF data transformer (optional)
- DBF data validator (optional)
'''
DBF_MAPPING = {
    'stops': {
        'table': 'stops',
        'fields': (
            ('StopId', 'stop_id'),
            ('StopName', 'stop_name', None, str_exists_validator),
            ('lat', 'stop_lat', latlon_transformer, latlon_validator),
            ('lon', 'stop_lon', latlon_transformer, latlon_validator),
            ('SiteName', 'stop_desc'),
            ('StopAbbr', 'stop_code'),
        )},
    'lines': {
        'table': 'routes',
        'fields': (
            ('LineID', 'route_id'),
            ('LineAbbr', 'route_short_name'),
            ('LineName', 'route_long_name'),
            ('', 'route_type', lambda x: 3),
            ('LineColor', 'route_color', convert_color),
        )},
}

'''
Database schema and Google Transit Feed mapping

Keys are table names and output file names (with a .txt)
Values are:
- The column name
- The column type
- If the column is included in the Google Transit Feed
'''

DATABASE_MAPPING = {
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
}

def create_db(database, mapping=DATABASE_MAPPING, drop_first=True):
    '''Create the database schema'''
    sql = create_db_sql(mapping, drop_first)
    database.executescript(sql)
    database.commit()


def create_db_sql(mapping=DATABASE_MAPPING, drop_first=True):
    '''Return SQL for creating the database schema'''
    
    sql = []
    if drop_first:
        for table_name in mapping.keys():
            sql.append('DROP TABLE IF EXISTS %s;' % table_name)
    
    for table_name, column_data in mapping.items():
        sql.append('CREATE TABLE %s' % table_name + ' (' + 
            ', '.join(['%s %s' % (cname, ctype) for
                cname, ctype, _ in column_data]) + ');')
    
    return '\n'.join(sql)


def read_dbf(dbf_path, database, mapping=DBF_MAPPING, verbose=True):
    '''Read a MTTA dbf files into the database'''
    
    # Find DBF file in mapping
    dbf_name = os.path.split(dbf_path)[-1].lower()
    dbf_name = dbf_name.replace('.dbf','')
    if dbf_name not in mapping: dbf_name += 's'
    if dbf_name not in mapping:
        if verbose: print "Skipping unknown DBF file '%s'" % dbf_path
        return
    if verbose: print "Reading DBF file '%s'" % dbf_path
    
    feed = mapping[dbf_name]
    table_name = feed['table']
    db_f = dbfpy.dbf.Dbf(dbf_path, readOnly=True)
    rows = []
    header = []
    for fh in feed['fields']:
        header.append(fh[1])
    #rows.append(header)
    for record in db_f:
        row = []
        invalid_fields = False
        for field in feed['fields']:
            if field[0]:
                field_value = record[field[0]]
            if len(field) >= 3 and callable(field[2]):
                field_value = field[2](field_value)
            if len(field) >= 4 and callable(field[3]):
                if not field[3](field_value):
                    invalid_fields = True
            if isinstance(field_value, str):
                
                row.append(unicode(field_value, encoding='latin-1'))
            else:
                row.append(field_value)
        if not invalid_fields:
            rows.append(row)
    if rows:
        sql = 'INSERT INTO %s (' % table_name
        sql += ', '.join([h for h in header])
        sql += ') VALUES (' + ', '.join(['?' for _ in header]) + ');'
        # Faster but harder to debug
        # database.executemany(sql, rows)
        
        for row in rows:
            database.execute(sql, row)


def write_gtf_text(database, destination_folder='.', 
        mapping=DATABASE_MAPPING):
    
    cur = database.cursor()
    out_files = []
    for table_name, column_data in mapping.items():
        out_name = os.path.join(destination_folder, table_name + '.txt')
        out_files.append(out_name)
        columns = [name for name, _, include in column_data if include]
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table_name + ';'
        
        def to_utf8(val):
            if isinstance(val, unicode):
                return val.encode('utf-8')
            else:
                return val
        
        with open(out_name, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in cur.execute(sql):
                utf8_row = [to_utf8(c) for c in row]
                writer.writerow(utf8_row)
    cur.close()
    
    # Create the zip file
    


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


help_message = '''
Convert a folder of DBF files to a sqlite database.  Options:

 -h, --help   - This help
 -d, --dbf    - The path to the DBF files (default ./)
 -o, --out    - The output directory (default ./)
 -s, --sqlite - Write the intermediate database to disk
'''


def main(argv=None):
    if argv is None:
        argv = sys.argv
    base_path = os.path.abspath(os.path.dirname(__file__))
    dbf_folder = os.path.join(base_path, './')
    destination = os.path.join(base_path, './')
    database_path = ':memory:'
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
            if option in ("-s", "--sqlite"):
                database_path = value
            if option in ("-o", "--out"):
                destination = value

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 1

    # Create the database
    database = sqlite3.connect(database_path)
    create_db(database)
    
    # Read DBF files
    for path, dirs, files in os.walk(dbf_folder):
        for f in files:
            if f.lower().endswith('.dbf'):
                full_path = os.path.abspath(os.path.join(path, f))
                read_dbf(full_path, database)
    
    # TODO: Read trapeeze trip files
    
    # TODO: Combine / massage data
    
    # Write from database to Google Transit Feed files
    out_files = write_gtf_text(database, destination)
    
    # TODO: Write zip file
    return 0

if __name__ == "__main__":
    sys.exit(main())
