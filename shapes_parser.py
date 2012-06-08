#!/usr/bin/env python
# encoding: utf-8

import os.path

import shapefile


BREAK_STUFF = 0

def is_useful(full_path):
    name = os.path.split(full_path)[-1].lower()
    useful = name.startswith('line') and name.endswith('.shp')
    if useful and not BREAK_STUFF:
        print "I'd parse '%s', but shape parsing isn't working yet" % full_path
        return False
    return useful


def read(lines_path, database, verbose=False):
    '''Read an lines shapefile into the database'''
    sf = shapefile.Reader(lines_path)
    shapes = sf.shapes()
    LINE_ID_FIELD = 2
    TRIP1_ID_FIELD = 54
    TRIP2_ID_FIELD = 55
    assert sf.fields[LINE_ID_FIELD][0] == 'LineId'
    assert sf.fields[TRIP1_ID_FIELD][0] == 'LineDirId0'
    assert sf.fields[TRIP2_ID_FIELD][0] == 'LineDirId1'

    shape_sql = (
    'INSERT INTO shapes'
    ' (shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence, active)'
    ' VALUES (?, ?, ?, ?, ?);')
    update_sql = (
    'UPDATE trips SET shape_id=? WHERE route_id=? and direction_id=?;')

    for record, shape in zip(sf.records(), shapes):
        line_id = record[LINE_ID_FIELD - 1]
        trip1_id = record[TRIP1_ID_FIELD - 1]
        trip2_id = record[TRIP2_ID_FIELD - 1]
        assert(line_id)
        assert(trip1_id)
        assert(trip2_id)
        shape_id = 'shp_%s' % line_id
        num_points = len(shape.points)
        if verbose:
            print "Adding shape %s (%d points) for line %s with trip ids %s and %s" % (shape_id, num_points, line_id, trip1_id, trip2_id)
        
        # Forward trip
        shape_id_0 = shape_id + '_0'
        for seq, (lon, lat) in enumerate(shape.points):
            database.execute(shape_sql, (shape_id_0, lat, lon, seq, 1))
        database.execute(update_sql, (shape_id_0, line_id, 0))
        
        # Return trip
        shape_id_1 = shape_id + '_1'
        for seq, (lon, lat) in enumerate(shape.points):
            rseq = num_points - seq
            database.execute(shape_sql, (shape_id_1, lat, lon, rseq, 1))
        database.execute(update_sql, (shape_id_1, line_id, 1))
