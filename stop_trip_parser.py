#!/usr/bin/env python
'''Parse a trapeze stop trips text file'''


def is_useful(full_path):
    '''Return True if a file is a Stop Trips file'''
    if not full_path.lower().endswith('.txt'):
        return False
    key_string = 'Stop Trips'
    first_bits = open(full_path, 'r').read(len(key_string))
    return first_bits == key_string


def read(full_path, database, verbose=False, fixups=None):
    '''Read a Stop Trips file'''
    text = open(full_path, 'rU').read()
    data = parse_trapeze_stop_trips(text)
    store_stop_trips(data, database, verbose, fixups)


def parse_trapeze_text(text):
    '''Parse a trapeze file'''
    if text.startswith('Stop Trips'):
        return parse_trapeze_stop_trips(text)
    else:
        raise ValueError('Unknown Trapeze text dump')


def parse_trapeze_stop_trips(text):
    '''Parse a trapeze Stop Trips file'''
    in_header = False
    header_done = False
    in_dir = False
    dir_num = 0
    dir_headers = None
    dir_trips = None
    dir_fields = None
    start_col = 0
    d = dict(meta=dict(), dir=list())
    for linenum, line in enumerate(text.split('\n')):
        if in_header:
            if ':' in line:
                name, raw_val = line.split(':', 1)
                val = raw_val.strip()
                d['meta'][name] = val
            elif line == '':
                in_header = False
            else:
                raise ValueError(
                    'Header failure at line ' + linenum + '\n' + line
                )
        elif in_dir:
            if line == '':
                if dir_headers is None:
                    dir_headers = []
                elif dir_trips is None:
                    dir_trips = []
                else:
                    d['dir'][-1]['trips'] = dir_trips
                    in_dir = False
                    dir_num += 1
            elif dir_trips is None:
                if line.startswith('~'):
                    dir_fields = list()
                    start = 0
                    last_char = '~'
                    for column, char in enumerate(line):
                        if char != last_char:
                            if char == ' ':
                                dir_fields.append((start, column))
                            elif char == '~':
                                start = column
                            last_char = char
                    last_start, last_column = dir_fields[-1]
                    if last_start != start:
                        dir_fields.append((start, column))
                    headers = list()
                    for h in dir_headers:
                        headers.append([h[s:e].strip() for s, e in
                            dir_fields])
                    minimized_headers = list()
                    for h in zip(*headers):
                        minimized_headers.append(
                            [x for x in h if x])
                    start_col = 0
                    assert(minimized_headers[0] == ['Pattern'])
                    start_col += 1
                    if minimized_headers[1] == ['INT']:
                        start_col += 1
                    if minimized_headers[2] == ['VAL']:
                        start_col += 1
                    final_headers = minimized_headers[start_col:]
                    d['dir'][-1]['headers'] = final_headers
                else:
                    dir_headers.append(line)
            else:
                assert(start_col != 0)
                dir_trips.append(
                    [line[s:e].strip() for s, e in dir_fields][start_col:])
        else:
            if linenum == 0:
                assert(line == 'Stop Trips')
            elif linenum == 1:
                assert(line == '~~~~~~~~~~')
            elif linenum == 2:
                assert(line == '')
                in_header = True
            elif line.startswith('Direction:'):
                name, raw_val = line.split(':', 1)
                val = raw_val.strip()
                # Also Northbound, etc.
                #assert(val in ('To Downtown', 'From Downtown'))
                d['dir'].append(dict(headers=list()))
                d['dir'][-1]['name'] = val
                in_dir = True
                dir_headers = None
                dir_trips = None
            elif line == '':
                continue
            else:
                raise ValueError(
                    'I have no idea where I am at line '
                    + linenum + '\n' + line
                )
    return d


def store_stop_trips(stop_data, database, verbose=False, fixups=None):
    '''Store stop trips data to the database'''
    
    same_stops = dict()
    for ss in fixups.get('same_stops', []):
        same_stops[ss["original_id"]] = ss["replacement_id"]

    cursor = database.cursor()

    # Gather line_no to route_ids
    # Not ideal, but simplifies things down the line
    route_sql = 'SELECT route_short_name, route_id FROM routes;'
    res = cursor.execute(route_sql).fetchall()
    assert(len(res) > 0)
    route_ids = dict([(str(k), v) for k, v in res])

    line_id = stop_data['meta']['Line']
    try:
        route_id = route_ids[line_id]
    except KeyError:
        candidates = [k for k in route_ids.keys() if k.startswith(line_id)]
        if len(candidates) == 1:
            route_id = route_ids[candidates[0]]
            if verbose:
                print ('No exact match for %s - using %s (line ID %s)' %
                        (line_id, candidates[0], route_id))
        else:
            if verbose:
                print ('No exact match for %s - found %s' %
                        (line_id, candidates))
            raise
    service_id = stop_data['meta']['Service']
    stop_times = list()
    complaints = set()
    for dir_num, d in enumerate(stop_data['dir']):
        # Read all stop_ids
        # Again, not ideal, but easier to do this on first insert
        line_stops_sql = (
            "SELECT stop_abbr, node_abbr, stop_id, sequence"
            " FROM line_stops"
            " WHERE line_no='%s' AND line_dir='%s';" % 
            (route_id, dir_num))
        stop_ids = dict()
        for stop_abbr, node_abbr, stop_id, seq in (
                cursor.execute(line_stops_sql)):
            if node_abbr:
                key = (node_abbr, seq)
                stop_ids.setdefault(key, []).append(stop_id)
            key = (stop_abbr, seq)
            stop_ids.setdefault(key, []).append(stop_id)
            key = ('', seq)
            stop_ids.setdefault(key, []).append(stop_id)
        assert stop_ids
        
        for t_num, t in enumerate(d['trips']):
            trip_id = "%s_%s_%d_%02d" % (route_id, service_id, dir_num, t_num)
            last_time = None
            last_abbr = None
            for s_num, raw_time in enumerate(t):
                # Some are empty - stop is skipped this trip
                if not raw_time:
                    continue

                stop_abbrs = d['headers'][s_num]
                raw_stop_abbr = ';'.join(stop_abbrs)

                # Our best guess:
                # If stop abbr is included, trapeze uses '+' for approximate
                # If stop_abbr is empty, then is is approximate
                # Omit approximate times (Google will estimate) unless it's
                #  the first or last stop in a trip
                first_stop = (s_num == 0)
                last_stop = (s_num + 1 == len(t))
                approximate = '+' in raw_time or raw_stop_abbr == ''
                if (approximate and (not first_stop and not last_stop)):
                    gtime = ""
                else:
                    hour, minute = [int(x) for x in raw_time.split(':')]
                    gtime = "%02d:%02d:00" % (hour, minute)

                stop_id, complaint = pick_stop_id(stop_ids, stop_abbrs,
                    route_id, dir_num, s_num + 1)
                if stop_id in same_stops:
                    stop_id = same_stops[stop_id]
                if complaint:
                    complaints.add(complaint)
                stop_times.append((trip_id, gtime, gtime, raw_stop_abbr,
                    stop_id, s_num + 1))
                last_time = gtime
                last_abbr = raw_stop_abbr

    if complaints and verbose:
        print "\n".join(sorted(list(complaints)))

    trips = list()
    for dir_num, d in enumerate(stop_data['dir']):
        headsign = d['name']
        for t_num, t in enumerate(d['trips']):
            trip_id = "%s_%s_%d_%02d" % (route_id, service_id, dir_num, t_num)
            trips.append((route_id, service_id, trip_id, headsign, dir_num))

    stop_times_sql = ('INSERT INTO stop_times (trip_id, arrival_time,' +
        'departure_time, x_stop_abbr, stop_id, stop_sequence, active) ' +
        'VALUES (?, ?, ?, ?, ?, ?, 1);')
    cursor.executemany(stop_times_sql, stop_times)
    trips_sql = ('INSERT INTO trips (route_id, service_id, trip_id, ' +
        'trip_headsign, direction_id, active) VALUES (?, ?, ?, ?, ?, 1)')
    cursor.executemany(trips_sql, trips)
    cursor.close()
    database.commit()


def pick_stop_id(stop_ids, stop_abbrs, route_id, dir_num, seq_num):
    '''Find a stop ID, or die trying'''
    stop_id = None
    candidates = set()
    complaint = None

    # 0 and 1 - stop_abbrs are node_abbr or omitted
    # 1 and 2 - stop_abbrs are node_abbr and stop_abbr
    assert(len(stop_abbrs) in [0,1,2])

    for abbr in stop_abbrs:
        key = (str(abbr), str(seq_num))
        candidates.update(stop_ids.get(key, []))
    else:
        key = ('', str(seq_num))
        candidates.update(stop_ids.get(key, []))

    if len(candidates) == 0:
        raise Exception('No stop ID candidates for stop_abbrs ' +
            ','.join(stop_abbrs))
    if len(candidates) > 1:
        complaint = 'For stop_abbr %s, multiple stop candidates %s' % (
            ','.join(stop_abbrs), ','.join([str(c) for c in candidates]))
    return candidates.pop(), complaint
