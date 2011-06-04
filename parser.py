import csv
import dbfpy.dbf
import os


def latlon_transformer(value):
    return float(value) / 1000000

MAPPING = {'stops': {'file': 'STOPS.dbf',
                     'fields': (('StopId', 'stop_id'),
                                ('StopName', 'stop_name'),
                                ('lat', 'stop_lat', latlon_transformer),
                                ('lon', 'stop_lon', latlon_transformer),
                                ('SiteName', 'stop_desc'),
                                ('StopAbbr', 'stop_code'))},
           'routes': {'file': 'LINES.dbf',
                      'fields': (('LineID', 'route_id'),
                                 ('LineAbbr', 'route_short_name'),
                                 ('LineName', 'route_long_name'),
                                 ('', 'route_type', lambda x: 3))},
           #'calendar': {},
           #'trips': {},
          }


def parse(dbf_folder):

    for f in MAPPING:
        feed = MAPPING[f]
        db_f = dbfpy.dbf.Dbf('%s%s' % (dbf_folder, feed['file']),
                             readOnly=True)
        output_name = os.path.splitext(os.path.basename(f))[0]
        rows = []
        header = []
        for fh in feed['fields']:
            header.append(fh[1])
        rows.append(header)
        for record in db_f:
            print('record')
            row = []
            for field in feed['fields']:
                if field[0]:
                    field_value = record[field[0]]
                if len(field) >= 3 and callable(field[2]):
                    field_value = field[2](field_value)
                print('field - %s' % field_value)
                row.append(field_value)
            rows.append(row)
        if rows:
            with open('%s.txt' % (output_name), 'w') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
