# encoding: utf-8
import dbfpy.dbf
import sqlite3


def to_unicode(str):
    '''Converts input string to unicode'''
    return str.decode('iso_8859_1')


def generate_line_stops(dbf_file):
    out = sqlite3.connect('line_stops.db')
    if not out:
        raise Exception('Unable to open sqlite3 database at %s' % output_db)
    out.text_factory = to_unicode
    db_f = dbfpy.dbf.Dbf(dbf_file)

    sql_drop = 'DROP TABLE IF EXISTS line_stops;'
    sql_create = 'CREATE TABLE line_stops (stop_id int, stop_abbr text, line_no text, line_dir text);'
    sql_insert = 'INSERT INTO line_stops (stop_id, stop_abbr, line_no, line_dir) VALUES ( ?,?,?,? );'

    cur = out.cursor()
    cur.execute(sql_drop)
    cur.execute(sql_create)

    for row in db_f:
        linedir_str = str(row['LineDirId'])
        line_no = linedir_str[:-1]
        line_dir = linedir_str[-1]
        stop_id = row['StopId']
        stop_abbr = row['StopAbbr']
        cur.execute(sql_insert, (stop_id, stop_abbr, line_no, line_dir))

    cur.close()
    out.commit()
