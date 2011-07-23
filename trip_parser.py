#!/usr/bin/env python
'''Parse a trapeze text file'''

import csv
import re

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
    d = dict(meta=dict(),dir=list())
    for linenum, line in enumerate(text.split('\n')):
        if in_header:
            if ':' in line:
                name, raw_val = line.split(':',1)
                val = raw_val.strip()
                d['meta'][name] = val
            elif line == '':
                in_header = False
            else:
                raise ValueError('Header failure at line ' + linenum + '\n' + line)
        elif in_dir:
            if line == '':
                if dir_headers is None: dir_headers = []
                elif dir_trips is None: dir_trips = []
                else:
                    d['dir'][-1]['trips'] = dir_trips
                    in_dir = False
                    dir_num += 1
            elif dir_trips is None:
                if line.startswith('~'):
                    pattern = '^(' + line.replace('~','.').\
                        replace(' .',' (.').replace('. ','.) ')
                    
                    if pattern[-1] == '.': pattern += ')'
                    # Fails on 100 groups
                    try:
                        dir_re = re.compile(pattern)
                    except AssertionError:
                        raise ValueError('Need to use something other than re')
                    headers = list()
                    for h in dir_headers:
                        headers.append(
                            [x.strip() for x in dir_re.match(h).groups()])
                    minimized_headers = list()
                    for h in zip(*headers):
                        minimized_headers.append(
                            [x for x in h if x])
                    assert(minimized_headers[0] == ['Pattern'])
                    assert(minimized_headers[1] == ['INT'])
                    assert(minimized_headers[2] == ['VAL'])
                    final_headers = minimized_headers[3:]
                    d['dir'][-1]['headers'] = final_headers
                else:
                    dir_headers.append(line)
            else:
                dir_trips.append(
                    [x.strip() for x in dir_re.match(line).groups()[3:]])
            
        else:
            if linenum == 0: assert(line == 'Stop Trips')
            elif linenum == 1: assert(line == '~~~~~~~~~~')
            elif linenum == 2: 
                assert(line == '')
                in_header = True
            elif line.startswith('Direction:'):
                name, raw_val = line.split(':',1)
                val = raw_val.strip()
                # Also Northbound, etc.
                #assert(val in ('To Downtown', 'From Downtown'))
                d['dir'].append(dict(headers=list()))
                d['dir'][-1]['name'] = val
                in_dir = True
                dir_headers = None
                dir_trips = None
            elif line == '': continue
            else:
                raise ValueError('I have no idea where I am at line ' + linenum + '\n' + line)
            
    return d


def stop_id_lookup(stop_abbr, line_id, line_dir):
    '''Find a stop ID, or return None'''
    return stop_abbr

def combine_tables(stop_data, routes_data):
    
    routes = dict([(b,a) for a,b,_,_,_ in routes_data])
    route_id = routes[stop_data['meta']['Line']]
    stop_data['meta']['route_id'] = route_id
    service_id = stop_data['meta']['Service']

    for dir_num, d in enumerate(stop_data['dir']):
        d['headers'].insert(0, 'trip_id')
        d['stop_ids'] = ['trip_id']
        for t_num, t in enumerate(d['trips']):
            trip_id = "%s_%s_%d_%02d" % (route_id, service_id, dir_num, t_num)
            t.insert(0, trip_id)
        for stop_abbrs in d['headers'][1:]:
            stop_id = None
            for stop_abbr in stop_abbrs:
                stop_id = stop_id_lookup(stop_abbr, route_id, service_id)
                if stop_id: break
            d['stop_ids'].append(stop_id)


def trip_columns():
    return [
        'route_id',         # from routes.txt
        'service_id',       # from calendar.txt
        'trip_id',          # primary key
        'trip_headsign',    # "to Downtown", "Northbound"
        'direction_id',     # 0 (outbound?) or 1 (inbound?)
    ]

def trips_from_data(stop_data):

    route_id = stop_data['meta']['route_id']
    service_id = stop_data['meta']['Service']
    trips = list()
    for dir_num, d in enumerate(data['dir']):
        headsign = d['name']
        for t_num, t in enumerate(d['trips']):
            trip_id = t[0]
            trips.append((route_id, service_id, trip_id, headsign, dir_num))
    return trips

def stop_columns():
    return [
        'trip_id',          # from trips.txt 
        'arrival_time',     # - HH:MM:SS - 24hr
        'departure_time',   # - HH:MM:SS - 24hr
        'stop_id',          # from stops.txt
        'stop_sequence',    # order of the stops for a trip - starts with 1
    ]

def stop_times_from_data(stop_data):

    route_id = stop_data['meta']['route_id']
    service_id = stop_data['meta']['Service']
    stop_times = list()
    for dir_num, d in enumerate(stop_data['dir']):
        for t_num, t in enumerate(d['trips']):
            trip_id = t[0]
            for s_num, raw_time in enumerate(t[1:]):
                # Some are empty
                if not raw_time: continue
                
                # Trapeze uses '+' for approximate times (we think)
                raw_time = raw_time.replace('+','')
                hour, minute = [int(x) for x in raw_time.split(':')]
                gtime = "%02d:%02d:00" % (hour, minute)
                
                stop_id = d['stop_ids'][s_num+1]
                stop_times.append((trip_id, gtime, gtime, stop_id, s_num + 1))
    return stop_times

if __name__ == '__main__':
    import glob
    
    destination_folder = "./"
    text_dir = "data/Stoptrips/*.txt"
    
    routes_data = []
    with open('%s%s.txt' % (destination_folder,
                            'routes'), 'r') as f:
        reader = csv.reader(f)
        reader.next()
        routes_data.extend(reader)
    
    text_dir = "data/Stoptrips/*.txt"
    trips = [trip_columns()]
    stops = [stop_columns()]
    for filename in glob.glob(text_dir):
        d = open(filename, 'rU').read()
        try:
            data = parse_trapeze_text(d)
        except(ValueError):
            continue
        data2 = combine_tables(data, routes_data)
        trips.extend(trips_from_data(data))
        stops.extend(stop_times_from_data(data))
    
    destination_folder = "./"
    output_name = 'trips'
    with open('%s%s.txt' % (destination_folder,
                            output_name), 'w') as f:
        writer = csv.writer(f)
        writer.writerows(trips)
        
    output_name = 'stop_times'
    with open('%s%s.txt' % (destination_folder,
                            output_name), 'w') as f:
        writer = csv.writer(f)
        writer.writerows(stops)
    print "Done"
