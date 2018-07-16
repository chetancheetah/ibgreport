import sys
import csv
from datetime import datetime

if len(sys.argv) != 6:
    print "usage python gen_tips.py location format shift_report.csv cashoutreport.csv transactions.csv"
    exit(1)

report = {'Kitchen':{'type':'Kitchen', 'hours':0.0, 'ot-hours':0.0, 'pay':0.0, 'tips':0.0, 'extra-tips':0.0, 'cash':0.0}}

shift = {'Kitchen' : [
    {'Name' : 'Kitchen',
     'Staff Type' : 'Kitchen',
     'Clock-In'  : 'January 01 2000 12:00 AM',
     'Clock-Out' : 'January 01 2100 12:00 AM',
     'Duration' : '0.0',
 } ]}
#read the shift details
with open(sys.argv[3]) as f:
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


trans = []
tips = 0.0
cash = 0.0
with open(sys.argv[4]) as f:
    rows = f.readlines()
for r in rows:
    if not "End of Report" in r: continue
    cols = r.split(',')
    tips += float(cols[17])
    trans.append({ 'id': cols[15],
                   'Tip' : float(cols[17]),
                   'type' : cols[14][1:-1],
                   'Amount' : float(cols[16])})
    if cols[14][1:-1] == "CASH":
        cash += float(cols[16])
with open(sys.argv[5]) as f:
    rows = f.readlines()
for r in rows:
    if not "End of Report" in r: continue
    cols = r.split(',')
    for t in trans:
        if t['id'] == cols[12]:
            t['Staff'] = cols[17][1:-1]
            t['Bill Date'] = cols[15]

#init the report
report = {'Kitchen':{'type':'Kitchen', 'hours':0.0, 'ot-hours':0.0, 'pay':0.0, 'tips':0.0, 'extra-tips':0.0, 'cash':0.0}}
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
    week_hours = {}
    for s in shifts:
        hours = s['hours'] if s['hours'] <= 8.0 else 8.0
        ot_hours = 0.0 if s['hours'] <= 8.0 else (s['hours'] - 8.0)
        fr = datetime.strptime(s['Clock-In'], '%B %d %Y %H:%M %p')
        fr = fr.isocalendar()[1]
        if fr not in week_hours.keys():
            week_hours[fr] = {'hours':0.0, 'ot-hours':0.0}
        week_hours[fr]['hours'] += hours
        week_hours[fr]['ot-hours'] += ot_hours
    for h in week_hours:
        if week_hours[h]['hours'] > 40.0:
            week_hours[h]['ot-hours'] += week_hours[h]['hours'] - 40.0
            week_hours[h]['hours'] = 40.0
        report[name]['hours'] += week_hours[h]['hours']
        report[name]['ot-hours'] += week_hours[h]['ot-hours']

staff_types = {
    'Kitchen' : 'kitchen',
    '1001 - Kitchen' : 'BOH',
    '1002 - Servers' : 'server',
    '1007 - Owners' : 'owner',
    '1005 - Wait Staff Managers' : 'manager',
    '1006 - Managers' : 'manager',
    '2008 - Runner' : 'runner',
    '2011 - Food Runner' : 'runner',
    '2012 - Busser' : 'nusser',
    '2008 - Host(ess)' : 'host',
    '2009 - Host' : 'host',
    '2007 - Lead Bartender' : 'bartender',
    '2009 - Bartender' : 'bartender',
    '1008 - System Administrators' : 'manager',
}

#how to share
chino_shared_tips= {
    'kitchen' : 0.10, # 10%
    'runner' : 0.15,    #  5%
    'host' : 0.05,    #  5%
}

bellevue_shared_tips = {
    'kitchen' : 0.08, # 8%
    'runner' : 0.05,    #  15%
    'host' : 0.02,    #  2%
    'bartender' : 0.05,    #  2%
    'busser' : 0.10, # 10%
}

shared_tips= {
    'kitchen' : 0.08, # 8%
    'runner' : 0.05,    #  15%
    'host' : 0.02,    #  2%
    'bartender' : 0.05,    #  2%
    'busser' : 0.10, # 10%
}

if sys.argv[1] == 'chino':
    print "Chino Hills Report total_tips %f cash_advance %f" % (tips, cash)
    shared_tips = chino_shared_tips

if sys.argv[1] == 'bellevue':
    print "Bellevue Report total_tips %f cash_advance %f" % (tips, cash)
    shared_tips = bellevue_shared_tips

#calculate the tips
for  t in trans:
    # 70% belong to the server
    if t['Staff'] not in report.keys() :
        report['Kitchen']['tips'] += t['Tip'] * 0.7
    else:
        report[t['Staff']]['tips'] += t['Tip'] * 0.7
        pass
    if t['type'] == 'CASH':
        if t['Staff'] not in report.keys() :
            report['Kitchen']['cash'] += t['Amount']
        else:
            report[t['Staff']]['cash'] += t['Amount']
    #now lets split it
    #distribute the tips amongst the helpers
    for staff in shared_tips.keys():
        worked = 0
        for name, shifts in shift.iteritems():
            #iterate over the shifts
            for s in shifts:
                if staff_types[s['Staff Type']] != staff: continue
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
            if staff == 'busser' or staff == 'runner':
                report[t['Staff'] if t['Staff'] in report.keys() else 'Kitchen']['extra-tips'] += t['Tip']*shared_tips[staff]
            else:
                report['Kitchen']['tips'] += t['Tip']*shared_tips[staff]
            continue
#            print "No one worked as " + staff + " for bill " + t['Bill Number'] + " at " + t['Bill Date']
        for name, val in shift.iteritems():
            #iterate over the shifts
            for s in val:
                if staff_types[s['Staff Type']] != staff: continue
                tran = datetime.strptime(t['Bill Date'], '%m/%d/%Y %H:%M:%S%p')
                fr = datetime.strptime(s['Clock-In'], '%B %d %Y %H:%M %p')
                if s['Clock-Out'] == "\"\"":
                    to =  datetime.now()
                else:
                    to = datetime.strptime(s['Clock-Out'], '%B %d %Y %H:%M %p')
                if  fr <= tran and tran <= to:
                    report[name]['tips'] += (t['Tip']*shared_tips[staff]) / worked

if sys.argv[2] == 'csv':
    print "{:>20}, {:>22}, {:>12}, {:>12}, {:>12}, {:>12},  {:>12}, {:>12},  {:>12}, ".format('Name','Type', 'Hours', 'OT-hours', 'Pay', 'tips', 'extra-tips', 'cash-advance', 'Total')
    hours, ot_hours, pay, tips, extra_tips, cash = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    for k, v in sorted(report.items(), key=lambda x:x[1]['type']):
        print "{:>20}, {:>22}, {:>12}, {:>12}, {:>12}, {:>12},  {:>12}, {:>12},  {:>12}, ".format(k, v['type'], v['hours'], v['ot-hours'], v['pay'], v['tips'], v['extra-tips'], v['cash'], v['pay'] + v['tips'] + v['extra-tips'] - v['cash'])
        hours += v['hours']
        ot_hours += v['ot-hours']
        pay += v['pay']
        tips += v['tips']
        extra_tips += v['extra-tips']
        cash += v['cash']
    print "{:>20}, {:>22}, {:>12}, {:>12}, {:>12}, {:>12},  {:>12}, {:>12},  {:>12}, ".format("Total", "", hours, ot_hours, pay, tips, extra_tips, cash, pay+tips+extra_tips-cash)
else:
    print "{:>20}\t{:>22}\t {:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}\t{:>12}".format('Name','Type', 'Hours', 'OT-hours', 'Pay', 'tips', 'extra-tips', 'cash-advance', 'Total')
    hours, ot_hours, pay, tips, extra_tips, cash = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    for k, v in sorted(report.items(), key=lambda x:x[1]['type']):
        print "{:>20}\t {:>22}\t {:>12}\t {:>12}\t {:>12}\t {:>12}\t  {:>12}\t {:>12}\t  {:>12}\t ".format(k, v['type'], v['hours'], v['ot-hours'], v['pay'], v['tips'], v['extra-tips'], v['cash'], v['pay'] + v['tips'] + v['extra-tips'] - v['cash'])
        hours += v['hours']
        ot_hours += v['ot-hours']
        pay += v['pay']
        tips += v['tips']
        extra_tips += v['extra-tips']
        cash += v['cash']
    print "{:>20}\t {:>22}\t {:>12}\t {:>12}\t {:>12}\t {:>12}\t  {:>12}\t {:>12}\t  {:>12}\t ".format("Total", "", hours, ot_hours, pay, tips, extra_tips, cash, pay+tips+extra_tips-cash)
