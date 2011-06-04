#!/usr/bin/env python
# encoding: utf-8
"""
convert.py
Convert a folder of DBF files to a sqlite database

Created by John Whitlock on 2011-05-07.
"""

import getopt
import glob
import os
import sqlite3
import sys

import dbfpy.dbf

help_message = '''
Convert a folder of DBF files to a sqlite database.  Options:

 -h, --help   - This help
 -d, --dbf    - The path to the DBF files (default ./originals)
 -o, --output - The output database (default output.db)
'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    base_path = os.path.abspath(os.path.dirname(__file__))
    dbf_folder = os.path.join(base_path, 'originals')
    output_db = os.path.join(base_path, 'output.db')
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
                output_db = value
    
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 1

    convert_folder(dbf_folder, output_db)
    return 0

def to_unicode(str):
    '''Converts input string to unicode'''
    return str.decode('iso_8859_1')

def convert_folder(dbf_folder, output_db):
    '''Convert a folder of .dbf files to a sqlite database'''
    pattern = os.path.join(dbf_folder, '*.dbf')
    dbf_files = glob.glob(pattern)
    if not dbf_files:
        raise Exception('No .dbf files found in %s' % dbf_folder)

    out = sqlite3.connect(output_db)
    if not out:
        raise Exception('Unable to open sqlite3 database at %s' % output_db)
    out.text_factory = to_unicode
    
    for dbf_file in dbf_files:
        db_f = dbfpy.dbf.Dbf(dbf_file, readOnly=True)
        r_table_name = os.path.splitext(os.path.basename(dbf_file))[0]
        table_name = 'o_' + r_table_name.lower().replace('by', '_by_')
        print 'Reading', dbf_file, 'into', table_name
        
        # Convert DBF column types to sqlite
        columns = []
        names = []
        for f in db_f.fieldDefs:
            assert f.typeCode in 'NCL'
            if f.typeCode == 'N':
                if f.decimalCount == 0:
                    s_type = 'INTEGER'
                else:
                    s_type = 'REAL'
            elif f.typeCode == 'C':
                s_type = 'TEXT'
            elif f.typeCode == 'L':
                s_type = 'BOOLEAN'
            name = f.name.lower()
            count = 1
            while name in names:
                name = f.name + str(count)
                count += 1
            columns.append((name, s_type))
            names.append(name)
        sql_cols = ', '.join(['%s %s'%pair for pair in columns])
        sql_drop = 'DROP TABLE IF EXISTS %s ' % table_name
        sql_create = 'CREATE TABLE %s (%s)' % (table_name, sql_cols)
        sql_pos = ','.join(['?' for pair in columns])
        sql_insert = 'INSERT INTO %s VALUES (%s)' % (table_name, sql_pos)

        cur = out.cursor()
        cur.execute(sql_drop)
        cur.execute(sql_create)
        # Fast method
        #cur.executemany(sql_insert, [row.asList() for row in db_f])
        # Slow method, better for debugging
        for row in db_f:
            row_l = row.asList()
            cur.execute(sql_insert, row_l)
        cur.close()

if __name__ == "__main__":
    sys.exit(main())
