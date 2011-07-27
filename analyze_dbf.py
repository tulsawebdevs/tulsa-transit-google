#!/usr/bin/env python
# encoding: utf-8
'''Analyze the data in a DBF file, looking for useful fields.  Usage:

./analyze_dbf <path_to_dbf>
'''



import os
import sys

import dbfpy.dbf

def analyze_dbf(dbf_file):
    print 'parsing %s' % dbf_file
    db_f = dbfpy.dbf.Dbf(dbf_file, readOnly=True)
    
    # Gather columns
    columns = [x.name for x in db_f.fieldDefs]
    total_rows = db_f.recordCount
    
    # Gather values and counts
    fields = dict()
    for rownum, record in enumerate(db_f):
        if rownum == 0: continue
        for column, value in record.asDict().items():
            if column not in fields: fields[column] = dict()
            if value not in fields[column]: fields[column][value] = 0
            fields[column][value] += 1
    
    # Invert and analyze
    useless_columns = []
    for c in columns:
        if len(fields[c]) == 1:
            useless_columns.append(c)
            continue
        counts = [(count, value) for (value,count) in fields[c].items()]
        counts.sort()
        counts.reverse()
        vals = ", ".join(["'%s':%d"%(value,count) for count,value in counts[:4]])
        if len(counts) > 4:
            headline_count = sum([count for count,_ in counts[:4]])
            vals += ", (Other):%d" % (total_rows - headline_count)
        print "%s - %s"%(c, vals)
    
    print "\nUseless columns:", " ".join(useless_columns)
    
if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(1)
    else:
        analyze_dbf(os.path.abspath(sys.argv[1]))
    
