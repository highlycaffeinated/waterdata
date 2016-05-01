#!/usr/bin/env python

import json
import requests
import sys

r = requests.get('http://waterservices.usgs.gov/nwis/iv/?format=json&sites=08178700,08168500,08169500&parameterCd=00060,00065')
if r.status_code != 200:
    sys.exit()

data = r.json()

current_vals = { }
result = 0

try:
    with open('/tmp/waterdata.last', 'r') as f:
        previous_vals = json.load(f)
except:
    previous_vals = {}

try:
    with open('/etc/waterdata.thresholds', 'r') as f:
        thresholds = json.load(f)
except:
    thresholds = {}


for ts in data['value']['timeSeries']:
    sitecode = ts['sourceInfo']['siteCode'][0]['value']
    sitename = ts['sourceInfo']['siteName']
    varcode = ts['variable']['variableCode'][0]['value']
    varname = ts['variable']['variableName']
    value = float(ts['values'][0]['value'][0]['value'])

    if sitecode not in current_vals:
        current_vals[sitecode] = { 'name': sitename, 'values': {} }

    last = float(previous_vals.get(sitecode, {}).get('values', {}).get(varcode, {}).get('value', 0))
    trend = value - last

    current_vals[sitecode]['values'][varcode] = { 'name': varname, 'value': value, 'trend': trend }

    key = "{}-{}".format(sitecode, varcode)
    if key in thresholds:
        threshold = float(thresholds[key])
        if value >= threshold and last < threshold:
            print "Alert: {} {} = {} (threshold {})".format(sitename, varname, value, threshold)
            result = 1
        if value < threshold and last >= threshold:
            print "Normal: {} {} = {} (threshold {})".format(sitename, varname, value, threshold)
            result = 1


#write new 'last' file
with open('/tmp/waterdata.last', 'w') as f:
    json.dump(current_vals, f, indent=4)

sys.exit(result)
