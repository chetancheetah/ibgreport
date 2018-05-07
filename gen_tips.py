import sys
import csv
from datetime import datetime

if len(sys.argv) != 5:
    print "usage python location gen_tips.py shift_report.csv cashoutreport.csv transactions.csv"
    exit(1)

report = {'House':{'type':'House', 'hours':0.0, 'ot-hours':0.0, 'pay':0.0, 'tips':0.0, 'extra-tips':0.0, 'cash':0.0}}

shift = {'House' : [
    {'Name' : 'House',
     'Staff Type' : 'House',
     'Clock-In'  : 'January 01 2000 12:00 AM',
     'Clock-Out' : 'January 01 2100 12:00 AM',
     'Duration' : '0.0',
 } ]}
#read the shift details
with open(sys.argv[2]) as f:
    rows = f.readlines()
for r in rows:
    if not "End of Report" in r: continue
    cols = r.split(',')
    if cols[1] == '': continue
    if cols[2][1:-1] == '1001 - Kitchen':
        name = cols[1][1:-1]
    else:
        name = cols[1][1:-1].split(' ')[-1]
    if name not in shift.keys(): shift[name] = []
    shift[name].append({'Staff Type': cols[2][1:-1],
                            'Clock-In' : cols[4][1:] + cols[5][:-1],
                            'Clock-Out': cols[10][1:] + cols[11][:-1],
                            'Duration' : cols[6]})


trans = {}

with open(sys.argv[3]) as f:
    rows = f.readlines()
for r in rows:
    if not "End of Report" in r: continue
    cols = r.split(',')
    #if cols[20][0] == '"': cols[20] = cols[20][1:]
    trans[cols[15]] = {'Tip' : float(cols[17]),
                       'type' : cols[14][1:-1],
                       'Amount' : float(cols[18])}

with open(sys.argv[4]) as f:
    rows = f.readlines()
for r in rows:
    if not "End of Report" in r: continue
    cols = r.split(',')
    if cols[12] not in trans.keys():
       # print cols
       # print "Not found in end of report"
        continue
    trans[cols[12]]['Staff'] = cols[17][1:-1]
    trans[cols[12]]['Bill Date'] = cols[15]

#init the report
report = {'House':{'type':'House', 'hours':0.0, 'ot-hours':0.0, 'pay':0.0, 'tips':0.0, 'extra-tips':0.0, 'cash':0.0}}
for u in shift.keys(): report[u] = {'type':shift[u][0]['Staff Type'],'hours':0.0, 'ot-hours':0.0, 'pay': 0.0, 'tips':0.0, 'extra-tips':0.0, 'cash':0.0}

#calculate the OT hours
for name, shifts in shift.iteritems():
    report[name]['shifts'] = shifts
    dat = '0'
    old = {'hours':0.0}
    hours = 0.0
    for s in shifts:
        s['hours'] = 0.0
        ndate = s['Clock-In'].split(' ')[1]
        if dat != ndate:
            old['hours'] = hours
            hours = 0.0
            dat  = ndate
        hours += float(s['Duration'])
        old = s
    old['hours'] = hours
    for s in shifts:
        hours = s['hours'] if s['hours'] <= 8.0 else 8.0
        ot_hours = 0.0 if s['hours'] <= 8.0 else (s['hours'] - 8.0)
        report[name]['hours'] += hours
        report[name]['ot-hours'] += ot_hours
#        rate = float(s['Hourly Rate'][1:])
#        report[name]['pay'] += hours * rate + ot_hours*1.5*rate


#how to share
chino_shared_tips= {
    'House' : 0.02, # 2%
    '1001 - Kitchen'  : 0.08,   #  8%
    '2008 - Host(ess)' : 0.05,    #  5%
    '2008 - Runner' : 0.10,    #  10%
    '2009 - Host' : 0.05,    #  5%
}

shared_tips= {
    'House'  : 0.08,   #  8%
    'Busser' : 0.10,     # 10%
    'Food Runner' : 0.05,#  5%
    '2008 - Host(ess)' : 0.02,    #  2%
    '2009 - Host' : 0.02,    #  2%
    '2007 - Lead Bartender': 0.05,   #  5%
}

if sys.argv[1] == 'chino':
    shared_tips = chino_shared_tips

#calculate the tips
for tid, t in trans.iteritems():
    # 70% belong to the server
    if t['Staff'] not in report.keys() :
        report['House']['tips'] += t['Tip']
    else:
        report[t['Staff']]['tips'] += t['Tip']
        pass
    if t['type'] == 'CASH':
        if t['Staff'] not in report.keys() :
            report['House']['cash'] += t['Amount']
        else:
            report[t['Staff']]['cash'] += t['Amount']
    #now lets split it
    #distribute the tips amongst the helpers
    for staff in shared_tips.keys():
        worked = 0
        for name, shifts in shift.iteritems():
            #iterate over the shifts
            for s in shifts:
                if s['Staff Type'] != staff: continue
                tran = datetime.strptime(t['Bill Date'], '%m/%d/%Y %H:%M:%S%p')
                fr = datetime.strptime(s['Clock-In'], '%B %d %Y %H:%M %p')
                if s['Clock-Out'] == "\"\"":
                    to = datetime.now()
                else:
                    to = datetime.strptime(s['Clock-Out'], '%B %d %Y %H:%M %p')
                if  fr <= tran and tran <= to:
                    worked += 1
        if worked == 0:
            # if there was no busser  or food runner then assumption the server would have bussed
            if staff == 'Busser' or staff == 'Food Runner':
                report[t['Staff'] if t['Staff'] in report.keys() else 'House']['extra-tips'] += t['Tip']*shared_tips[staff]
            else:
                report['House']['tips'] += t['Tip']*shared_tips[staff]
            continue
#            print "No one worked as " + staff + " for bill " + t['Bill Number'] + " at " + t['Bill Date']
        for name, val in shift.iteritems():
            #iterate over the shifts
            for s in val:
                if s['Staff Type'] != staff: continue
                tran = datetime.strptime(t['Bill Date'], '%m/%d/%Y %H:%M:%S%p')
                fr = datetime.strptime(s['Clock-In'], '%B %d %Y %H:%M %p')
                if s['Clock-Out'] == "\"\"":
                    to =  datetime.now()
                else:
                    to = datetime.strptime(s['Clock-Out'], '%B %d %Y %H:%M %p')
                if  fr <= tran and tran <= to:
                    report[name]['tips'] += (t['Tip']*shared_tips[staff])

print "{:>20} {:>22} {:>12} {:>12} {:>12} {:>12}  {:>12} {:>12}  {:>12} ".format('Name','Type', 'Hours', 'OT-hours', 'Pay', 'tips', 'extra-tips', 'cash-advance', 'Total')
hours, ot_hours, pay, tips, extra_tips, cash = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
for k, v in sorted(report.items(), key=lambda x:x[1]['type']):
    print "{:>20} {:>22} {:>12} {:>12} {:>12} {:>12}  {:>12} {:>12}  {:>12} ".format(k, v['type'], v['hours'], v['ot-hours'], v['pay'], v['tips'], v['extra-tips'], v['cash'], v['pay'] + v['tips'] + v['extra-tips'] - v['cash'])
    hours += v['hours']
    ot_hours += v['ot-hours']
    pay += v['pay']
    tips += v['tips']
    extra_tips += v['extra-tips']
    cash += v['cash']    
print "{:>20} {:>22} {:>12} {:>12} {:>12} {:>12}  {:>12} {:>12}  {:>12} ".format("Total", "", hours, ot_hours, pay, tips, extra_tips, cash, pay+tips+extra_tips-cash)
    
