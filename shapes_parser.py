#!/usr/bin/env python
# encoding: utf-8

import collections
from math import radians, cos, sin, asin, sqrt 
import os.path

import networkx
import shapefile


BREAK_STUFF = 1


def is_useful(full_path):
    name = os.path.split(full_path)[-1].lower()
    useful = (name.startswith('line') or name.startswith('pattern')) and name.endswith('.shp')
    if useful and not BREAK_STUFF:
        print "I'd parse '%s', but shape parsing isn't working yet" % full_path
        return False
    return useful


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    
    From http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    return km


def nearest_node(graph, lat, lon):
    """
    Find the nearest node to the point
    """
    node_candidates = []
    for lat1, lon1 in graph.nodes():
        distance = haversine(lat, lon, lat1, lon1) 
        node_candidates.append((distance, (lat1, lon1)))
    node_candidates.sort()
    return node_candidates[0][1]


def read(full_path, database, verbose=False):
    '''Read a shapefile into the database'''
    name = os.path.split(full_path)[-1].lower()
    if name.startswith('pattern'):
        pass
        #read_patterns(full_path, database, verbose)
    elif name.startswith('lines'):
        read_lines(full_path, database, verbose)


def read_patterns(patterns_path, database, verbose=False):
    '''
    Read a patterns shapefile into the database
    
    This might be the one we want
    '''
    sf = shapefile.Reader(patterns_path)
    assert sf.shapeType == 3  # PolyLine
    shapes = sf.shapes()
    PATTERN_ID_FIELD = 1
    PATTERN_FIELD = 2
    LINEDIR_ID_FIELD = 3
    assert sf.fields[PATTERN_ID_FIELD][0] == 'PatternId'
    assert sf.fields[PATTERN_FIELD][0] == 'Pattern'
    assert sf.fields[LINEDIR_ID_FIELD][0] == 'LineDirId'

    for record, shape in zip(sf.records(), shapes):
        assert shape.shapeType == 3
        pattern_id = record[PATTERN_ID_FIELD - 1]
        pattern = record[PATTERN_FIELD - 1]
        linedir_id = record[LINEDIR_ID_FIELD - 1]
        
        # Assemble parts
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
        
        # Create line
        line = []
        first_nodes = None
        for seq, (node1, node2) in enumerate(parts):
            print "%s %s %s %d: (%0.5f %0.5f) -> (%0.5f %0.5f)" % (
                pattern_id, pattern, linedir_id, seq, node1[0], node1[1], node2[0], node2[1])
            if first_nodes:
                first_node1, first_node2 = first_nodes
                if first_node1 == node1:
                    line.extend([first_node2, first_node1, node2])
                elif first_node1 == node2:
                    line.extend([first_node2, first_node1, node1])
                elif first_node2 == node1:
                    line.extend([first_node1, first_node2, node2])
                elif first_node2 == node2:
                    line.extend([first_node1, first_node2, node1])
                else:
                    raise Exception('Discontinuity')
                first_nodes = None
            elif line:
                last_node = line[-1]
                pen_node = line[-2]
                if last_node == node1:
                    found = True
                    line.append(node2)
                elif last_node == node2:
                    found = True
                    line.append(node1)
                elif pen_node == node1 or pen_node == node2:
                    print "*** Tossing out last node (%0.5f %0.5f)" % last_node
                    line.pop()
                    if pen_node == node1:
                        line.append(node2)
                    else:
                        line.append(node1)
                else:
                    print "*** Discontinuity - trying to recover"
                    first_nodes = (node1, node2)
            else:
                first_nodes = (node1, node2)

def read_lines(lines_path, database, verbose=False):
    '''Read an lines shapefile into the database'''
    sf = shapefile.Reader(lines_path)
    assert sf.shapeType == 3  # PolyLine
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
    trips_sql = 'SELECT trip_id from trips where route_id=? and active=1;'
    stops_sql = (
        'SELECT stop_times.stop_id, stop_times.stop_sequence, stops.stop_lat,'
        '       stops.stop_lon'
        ' FROM stop_times JOIN stops on stop_times.stop_id=stops.stop_id'
        ' WHERE stop_times.active=1 AND stop_times.trip_id=?'
        ' ORDER BY stop_times.stop_sequence;') 
    update_trip_sql = 'UPDATE trips SET shape_id=? WHERE trip_id=?;'
    
    trip_shape_cache = dict()
    stop_node_cache = dict()
    for record, shape in zip(sf.records(), shapes):
        assert shape.shapeType == 3
        line_id = record[LINE_ID_FIELD - 1]
        trip1_id = record[TRIP1_ID_FIELD - 1]
        trip2_id = record[TRIP2_ID_FIELD - 1]
        assert(line_id)
        assert(trip1_id)
        assert(trip2_id)
        shape_id = 'shp_%s' % line_id
        shape_seq = 0
        num_points = len(shape.points)
        
        # Iterate through the trips
        res = database.execute(trips_sql, (str(line_id),))
        trips = [x[0] for x in res.fetchall()]
        if not trips:
            continue
        
        if verbose:
            print "Adding shape %s (%d points) for line %s with trip ids %s and %s" % (shape_id, num_points, line_id, trip1_id, trip2_id)

        # Assemble parts
        parts = set()
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
                        parts.add((part[0], part[1]))
                part = []
            part.append((lat, lon))
        if part:
            parts.add((part[0], part[1]))

        # Create graph
        graph = networkx.Graph()
        for (lat1, lon1), (lat2, lon2) in parts:
            distance = haversine(lat1, lon1, lat2, lon2)
            graph.add_edge((lat1, lon1), (lat2, lon2), distance=distance)
        
        # Iterate through the trips
        for trip in trips:
            # Get the stops
            stops = database.execute(stops_sql, (trip,)).fetchall()
            assert stops
            
            # Create the trip identifier
            trip_shape_key = '-'.join([str(s[0]) for s in stops])
            if trip_shape_key not in trip_shape_cache:
                trip_shape = []
                for stop, seq, lat, lon in stops:
                    stop_node_key = "%s-%s" % (stop, shape_id)
                    if stop_node_key not in stop_node_cache:
                        node = nearest_node(graph, lat, lon)
                        stop_node_cache[stop_node_key] = node
                    node = stop_node_cache[stop_node_key]
                    if trip_shape:
                        path = networkx.shortest_path(
                            graph, trip_shape[-1], node)
                        trip_shape.extend(path[1:])
                    else:
                        trip_shape.append(node)
                trip_shape_id = "%s_%d" % (shape_id, shape_seq)
                shape_seq += 1
                trip_shape_cache[trip_shape_key] = trip_shape_id
                for s, (lat, lon) in enumerate(trip_shape):
                    database.execute(
                        shape_sql, (trip_shape_id, lat, lon, s, 1))
            trip_shape_id = trip_shape_cache[trip_shape_key]
            database.execute(update_trip_sql, (trip_shape_id, trip))
