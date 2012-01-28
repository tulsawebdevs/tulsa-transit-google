#!/usr/bin/env python
'''Parse a trapeze trips text file'''


def is_useful(full_path):
    '''Return True if a file is a Trips file'''
    if not full_path.lower().endswith('.txt'):
        return False
    key_string = 'Trips'
    first_bits = open(full_path, 'r').read(len(key_string))
    return first_bits == key_string


def read(full_path, database, verbose=False):
    '''Read a Trips file'''
    text = open(full_path, 'rU').read()
    data = parse_trapeze_stop_trips(text)
    store_stop_trips(data, database, verbose)


def parse_trapeze_text(text):
    '''Parse a trapeze file'''
    if text.startswith('Trips'):
        return parse_trapeze_stop_trips(text)
    else:
        raise ValueError('Unknown Trapeze text dump')


def parse_trapeze_stop_trips(text):
    '''Parse a trapeze Trips file'''
    in_header = False
    header_done = False
    in_dir = False
    dir_num = 0
    dir_headers = None
    dir_trips = None
    dir_fields = None
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
                    dir_fields.append((start, column))
                    headers = list()
                    for h in dir_headers:
                        headers.append([h[s:e].strip() for s, e in dir_fields])
                    minimized_headers = list()
                    for h in zip(*headers):
                        minimized_headers.append(
                            [x for x in h if x])
                    assert(minimized_headers[0] == ['Frz'])
                    assert(minimized_headers[1] == ['Trip'])
                    assert(minimized_headers[2] == ['Pattern'])
                    assert(minimized_headers[3] == ['VehType'])
                    assert(minimized_headers[4] == ['Block'])
                    assert(minimized_headers[5] == ['INT'])
                    assert(minimized_headers[6] == ['Tot RT'])
                    final_headers = minimized_headers[7:]
                    d['dir'][-1]['headers'] = final_headers
                else:
                    dir_headers.append(line)
            else:
                dir_trips.append(
                    [line[s:e].strip() for s, e in dir_fields][7:])
        else:
            if linenum == 0:
                assert(line == 'Trips')
            elif linenum == 1:
                assert(line == '~~~~~')
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


def store_stop_trips(stop_data, database, verbose=False):
    '''Store stop trips data to the database'''

    cursor = database.cursor()

    # Gather line_no to route_ids
    # Not ideal, but simplifies things down the line
    route_sql = 'SELECT route_short_name, route_id FROM routes;'
    res = cursor.execute(route_sql).fetchall()
    assert(len(res) > 0)
    route_ids = dict([(str(k), v) for k, v in res])

    line_id = stop_data['meta']['Line']
    route_id = route_ids[line_id]
    service_id = stop_data['meta']['Service']
    stop_times = list()
    complaints = set()
    for dir_num, d in enumerate(stop_data['dir']):
        for t_num, t in enumerate(d['trips']):
            trip_id = "%s_%s_%d_%02d" % (route_id, service_id, dir_num, t_num)
            last_time = None
            last_abbr = None
            
            node_times = dict()
            skipped_stop = False
            for s_num, raw_time in enumerate(t):

                # Trapeze uses '+' for approximate times (we think)
                if '+' in raw_time:
                    # Omit approximate time
                    gtime = ""
                elif not raw_time:
                    skipped_stop = True
                    gtime = None
                else:
                    skipped_stop = False
                    hour, minute = [int(x) for x in raw_time.split(':')]
                    gtime = "%02d:%02d:00" % (hour, minute)

                node_abbrs = d['headers'][s_num]
                raw_node_abbr = ';'.join(node_abbrs)

                # Sometimes, a stop is duplicated in the schedule
                #if gtime == last_time and raw_node_abbr == last_abbr:
                #    continue

                assert len(node_abbrs) == 1
                if gtime:
                    node_times[node_abbrs[0].strip()] = gtime

                last_time = gtime
                last_abbr = raw_node_abbr
            
            sql = ('SELECT stop_abbr, node_abbr, ' +
                   ' stop_id, sequence FROM line_stops WHERE' +
                   " line_no='%s' AND line_dir='%s';")
            sql = sql % (route_id, dir_num)
            stops = dict()
            for stop_abbr, node_abbr, stop_id, sequence in cursor.execute(sql):
                stops[int(sequence)] = (stop_abbr, node_abbr, stop_id)
            s = 1
            skipped_stops = False
            for k in sorted(stops.keys()):
                stop_abbr, node_abbr, stop_id = stops[k]
                if node_abbr:
                    if node_abbr in node_times:
                        gtime = node_times[node_abbr]
                        skipped_stops = (gtime is None)
                    else:
                        complaints.add('No time for node "%s" stop "%s" seq %s' % ( node_abbr, stop_abbr, sequence))
                else:
                    gtime = ""
                if skipped_stops:
                    stop_times.append((trip_id, gtime, gtime, stop_abbr, stop_id, str(s)))
                    s+=1

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


def pick_stop_id(stop_ids, stop_abbrs, node_ids, node_abbrs, route_id, dir_num, seq_num):
    '''Find a stop ID, or die trying'''
    stop_id = None
    candidates = set()
    complaint = None
    for stop_abbr in stop_abbrs:
        key = (str(stop_abbr), str(route_id), str(dir_num), str(seq_num))
        candidates.update(stop_ids.get(key, []))
    for node_abbr in node_abbrs:
        key = (str(node_abbr), str(route_id), str(dir_num))
        candidates.update(node_ids.get(key, []))
    if len(candidates) == 0:
        raise Exception('No stop ID candidates for stop_abbrs ' +
            ','.join(stop_abbrs))
    if len(candidates) > 1:
        complaint = 'For stop_abbr %s, multiple stop candidates %s' % (
            ','.join(stop_abbrs), ','.join([str(c) for c in candidates]))
    return candidates.pop(), complaint
