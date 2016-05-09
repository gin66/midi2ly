#!/usr/bin/env python3.4
import sys
sys.path.append('python_midi')
import python_midi as midi
import key_guess

if len(sys.argv) != 2:
    print("Usage: {0} <midifile>".format(sys.argv[0]))
    print('     midifile: Title - Composer.mid')
    sys.exit(2)

midifile = sys.argv[1]
pattern = midi.read_midifile(midifile)

# Logic Pro X
# - uses first track for metadata
# - each region is coded as a separate track
# - seldom uses NoteOff but NoteOn with velocity zero
# - First two events are TrackNameEvent and InstrumentNameEvent

def get_track_instrument(p):
    if type(p[0]) is not midi.events.TrackNameEvent:
        return None,None
    if type(p[1]) is not midi.events.InstrumentNameEvent:
        return None,None
    return p[0].text,p[1].text

def parse_meta_track(p):
    for ev in p:
        print('% meta:',ev)

LILY_NOTE = []
for x in [",,,,",",,,",",,",",","","'","''","'''"]:
    for c in ['c','cis','d','dis','e','f','fis','g','gis','a','ais','b']:
        LILY_NOTE.append(c+x)

LILY_PERC = {
        36:'bd',
        42:'hh',
        40:'sn',
        28:'cymra',
        49:'cymca'
        }

print('%',LILY_NOTE)
durations = [
        None,
        ['32'],
        ['16'],
        ['16.'],
        ['8'],
        ['8','32'],
        ['8.'],
        ['8','16.'],
        ['4'],
        ['4','32'],
        ['4','16'],
        ['4','16.'],
        ['4.'],
        ['4','8','32'],
        ['4','8','16'],
        ['4','8','16.'],
        ['2'],
        ['2','32'],
        ['2','16'],
        ['2','16.'],
        ['2','8'],
        ['2','8','32'],
        ['2','8','16'],
        ['2','8','16.'],
        ['2','4'],
        ['2','4','32'],
        ['2','4','16'],
        ['2','4','16.'],
        ['2','4','8'],
        ['2','4','8','32'],
        ['2','4','8','16'],
        ['2','4','8','16.'],
        ['1']
    ]
def select_duration(tick,nextbar,dt):
    if dt < 0:
        print('negative dt',dt)
        raise
    v32 = int(round(16.0*dt/FULLTICK))*2
    if v32 == 0:
        v32 = 2
    res = durations[v32],FULLTICK//32 * v32
    print('%% select_duration(',tick,',',nextbar,',',dt,')=',res)
    return res

for p in pattern:
    p.make_ticks_abs()

# Get all ticks
ticks=set()
for p in pattern:
    for e in p:
        if type(e) is midi.events.NoteOnEvent and e.data[1] > 0:
            ticks.add(e.tick)
ticks=sorted(list(ticks))

# Get deltas => BASED ON THIS SET THE CLOCKTICK VALUE !!!!
dticks = {}
for i in range(len(ticks)-1):
    dt = ticks[i+1]-ticks[i]
    if dt in dticks:
        dticks[dt] += 1
    else:
        dticks[dt]  = 1
for dt in sorted([d for d in dticks]):
    print('% ',dt,dticks[dt])

FULLTICK = 16*120.0
FULLBAR  = FULLTICK
print(('%% Full tick aka 4 fourth is set to %d' % FULLTICK))

all_lily   = {}
track_type = {}
stats = [0]*12
keys = {}
for p in pattern:
    track,instrument = get_track_instrument(p)
    if track is None:
        parse_meta_track(p)
        continue

    k = track + '_' + instrument
    k = k.replace('-','_').replace(' ','_')
    if k not in all_lily:
        all_lily[k] = {}

    keys[k] = key_guess.calculate(p)
    print('%%',k,":",keys[k])

    if 'Bluebird' in k:
        CONV = LILY_PERC
        track_type[k] = 'drums'
    else:
        CONV = LILY_NOTE
        if 'L' in k:
            track_type[k] = 'piano left'
        elif 'R' in k:
            track_type[k] = 'piano right'
        else:
            track_type[k] = 'song'

    lily = all_lily[k]
    transient = {}
    for e in p:
        print('%% ', repr(e))
        if type(e) is midi.events.NoteOnEvent and e.data[1] > 0:
            if e.data[0] in transient:
                transient[e.data[0]].append(e)
            else:
                transient[e.data[0]] = [e]

            if track_type[k] != 'drums':
                stats[e.data[0] % 12] += 1

        if type(e) is midi.events.NoteOnEvent and e.data[1] == 0 \
                or type(e) is midi.events.NoteOffEvent:
            if e.data[0] not in transient:
                print('%% NoteOff without NoteOn: ',e)
                raise
            se = transient[e.data[0]].pop(0)
            if len(transient[e.data[0]]) == 0:
                del transient[e.data[0]]

            note = CONV[se.data[0]]
            dt   = e.tick - se.tick
            if se.tick not in lily:
                lily[se.tick] = []
            lily[se.tick].append( [note,dt,False] )
            print('%% => ',se.tick,str( [note,dt] ))
    if len(transient) > 0:
        raise

# Guess the key
print('% Statistik:',stats)
ref = {
        'c \\major': [1,0,1,0,1,1,0,1,0,1,0,1],
        'g \\major': [1,0,1,0,1,0,1,1,0,1,0,1],
        'd \\major': [0,1,1,0,1,0,1,1,0,1,0,1],
        'a \\major': [0,1,1,0,1,0,1,0,1,1,0,1],
        'e \\major': [0,1,0,1,1,0,1,0,1,1,0,1],
        'h \\major': [0,1,0,1,1,0,1,0,1,0,1,1],

        'f \\major': [1,0,1,0,1,1,0,1,0,1,1,0],
        'b \\major': [1,0,1,1,0,1,0,1,0,1,1,0],
        'c \\minor': [1,0,1,1,0,1,0,1,1,0,1,0],
        'f \\minor': [1,1,0,1,0,1,0,1,1,0,1,0],
        'b \\minor': [1,1,0,1,0,1,1,0,1,0,1,0]
    }
rmax = [None,None]
for r in ref:
    s = sum(h*(f-0.5) for h,f in zip(stats,ref[r]))
    print('%% %s %.2f' % (r,s))
    if rmax[0] is None or rmax[0] < s:
        rmax = [s,r]
key = rmax[1]
print('%% -> Selected:',key)

# Identify overlapping notes
for k in all_lily:
    lily = all_lily[k]
    ticks = sorted([t for t in lily])
    i = 0
    while i < len(ticks)-1:
        tick  = ticks[i]
        ntick = ticks[i+1]
        dt    = ntick-tick
        ns    = lily[tick]
        cns   = lily[ntick]
        for n in ns:
            if n[1] > dt:
                cns.append( [n[0],n[1]-dt,False] )
                n[1] = dt
                n[2] = True
        i += 1

# Determine max ticks
max_tick = 0
for k in all_lily:
    lily = all_lily[k]
    ticks = sorted([t for t in lily])
    tick  = ticks[-1]
    for n in lily[tick]:
        if n[1]+tick > max_tick:
            max_tick = tick + n[1]

# Shorten notes to same length
for k in all_lily:
    lily = all_lily[k]
    ticks = sorted([t for t in lily])
    i = 0
    while i < len(ticks):
        tick  = ticks[i]
        dt  = min(n[1] for n in ns)
        dtm = max(n[1] for n in ns)
        if dt != dtm:
            for n in ns:
                ntick = tick + dt
                if n[1] > dt:
                    if ntick not in lily:
                        lily[ntick] = []
                        ticks = sorted([t for t in lily])
                    cns = lily[ntick]
                    cns.append( [n[0],n[1]-dt,False] )
                    n[1] = dt
                    n[2] = True
        i += 1

# Split notes at bar
for k in all_lily:
    lily = all_lily[k]
    ticks = sorted([t for t in lily])
    next_bar = 0
    i = 0
    while i < len(ticks):
        tick  = ticks[i]
        while tick >= next_bar:
            next_bar += FULLBAR
        dt = next_bar - tick

        ns = lily[tick]
        for n in ns:
            if n[1] > dt:
                if next_bar not in lily:
                    lily[next_bar] = []
                    ticks = sorted([t for t in lily])
                cns = lily[next_bar]
                cns.append( [n[0],n[1]-dt,False] )
                n[1] = dt
                n[2] = True
        i += 1

# Cluster the tracks in lilypond format into bars
bars = {}
for k in all_lily:
    bars[k] = []

    lily = all_lily[k]

    cur_tick = 0
    next_bar = 0
    ticks = sorted([t for t in lily])
    i = 0
    last_i = -1
    while i < len(ticks):
        if cur_tick >= next_bar:
            cbar = []
            bars[k].append(cbar)
            next_bar += FULLBAR

        tick = ticks[i]

        if cur_tick < tick:
            #print('Rest',tick,cur_tick,next_bar)
            if next_bar <= tick:
                v,dt = select_duration(cur_tick,next_bar,next_bar-cur_tick)
            else:
                v,dt = select_duration(cur_tick,next_bar,tick - cur_tick)

            cur_tick += dt
            for vx in v:
                cbar.append('r' + vx)
        else:
            i += 1
            ns = lily[tick]

            n = ns[0]
            dt = min(n[1],n[1]+tick-cur_tick)
            if dt < 0:
                continue
            v,dt = select_duration(cur_tick,next_bar,dt)

            s = []
            for n in ns:
                if n[1] + tick > cur_tick:
                    s.append(n[0])
            if len(s) == 0:
                print('%% STRANGE: NO NOTE to set:',ns,tick,cur_tick)
                continue
            if len(s) > 1:
                s = ['<'] + s + ['>']
            s = ' '.join(s)

            sx = []
            for vx in v:
                sx.append(s+vx)

            cbar.append(' ~ '.join(sx) )

            if ns[0][-1]:
                cbar.append('~')

            print('%% COLLECT',ns,'to bar ',len(bars[k]),':',cbar)

            cur_tick += dt

    if cur_tick < next_bar:
        dt = next_bar - cur_tick
        v,dt = select_duration(cur_tick,next_bar,dt)
        for vx in v:
            cbar.append('r' + vx)
        cur_tick += dt

    while cur_tick < max_tick:
        if cur_tick >= next_bar:
            cbar = []
            bars[k].append(cbar)
            next_bar += FULLBAR
        cur_tick += FULLBAR
        cbar.append('r1')
    bars[k] = [' '.join(b) for b in bars[k]]

del_silence = True
while del_silence:
    for k in all_lily:
        if bars[k][0] != 'r1':
            del_silence = False
            break
    if del_silence:
        for k in all_lily:
            bars[k].pop(0)

# Find repeats
voices = [v for v in all_lily if track_type[v][:5] == 'piano']
max_bar = max(len(bars[k]) for k in voices)
bar_dict = {}
for i in range(max_bar):
    bdata = ''
    for k in voices:
        try:
            bdata += bars[k][i]
        except KeyError:
            pass
    if bdata in bar_dict:
        bar_dict[bdata].append(i)
    else:
        bar_dict[bdata] = [i]
dups = [bar_dict[b] for b in bar_dict if len(bar_dict[b]) > 1]

dup_dict = {}
for d in dups:
    for v in d[:-1]:
        dup_dict[v] = d

# collect here all possible candidates
candid=[]
for l in range(1,max_bar//2):
    for start in range(max_bar-l):
        ok = True
        for i in range(l):
            if start+i not in dup_dict:
                ok = False
                break
        if ok:
            candid.append([i+start for i in range(l)])

# Now evaluate all candidates
feasible = []
for c in candid:
    # The first value in the list determines the skip values
    for alt in dup_dict[c[0]]:
        delta = alt-c[0]
        if delta < len(c):
            continue

        for repeat in range(4,0,-1):
            ok = True
            for v in c:
                for r in range(1,repeat+1):
                    if v+r*delta not in dup_dict[v]:
                        ok = False

            if ok:
                for r in range(repeat,0,-1):
                    feasible.append( (c,delta,delta-len(c),r) )
                break

for c in feasible:
    print('%% feasible:',c)

# Check for sequences > 2
for v in dup_dict:
    d = dup_dict[v]
    c = sorted([x for x in d if x >= v])
    if len(c) > 2 and c[-1]-v == len(c)-1:
        feasible.append( (c,0,0,len(c)) )

bar_func = [('orig',1,None,lambda x,pars:x+' |') for i in range(max_bar)]

# SORT feasible
feasible = sorted(feasible,key=lambda x:len(x[0])*(x[1]-x[2]*0.5)*x[3],reverse=True)

for f in feasible:
    print('%% OK',f)

repeated = set()
for f in feasible:
    c,delta,skip,repeat = f
    if skip <= 1 and delta >= 2:
        ok = True
        for i in range(c[0],c[0]+(1+repeat)*delta):
            if i in repeated:
                ok = False
        if ok:
            for i in range(c[0],c[0]+(1+repeat)*delta):
                repeated.add(i)
            print('%%',c,"-> repeat",delta,'bars with',repeat,'alternate end(s)')
            s = '' if repeat <= 1 else '\\mark "%dx" ' % (repeat+1)
            bar_func[c[0]]           = ('alt_rep A %d repeat=%d' % (c[0],repeat),1,[repeat+1,s], \
                        lambda x,pars: '\\repeat volta %d {%s %s |' % (pars[0],pars[1],x))
            if skip == 0:
                bar_func[c[0]+  delta-1] = ('alt_rep E %d repeat=%d' % (c[0],repeat),repeat*delta+1,None, \
                            lambda x,pars: '%s |}' % x)
            else:
                bar_func[c[0]+  delta-1] = ('alt_rep B %d repeat=%d' % (c[0],repeat),delta,None, \
                            lambda x,pars: '}\\alternative{{%s|' % x)
                for r in range(2,repeat+2):
                    if r <= repeat:
                        bar_func[c[0]+r*delta-1] = ('alt_rep C %d %d' % (c[0],r),delta,None, \
                            lambda x,pars: '}{%s |'  % x)
                    else:
                        bar_func[c[0]+r*delta-1] = ('alt_rep D %d' % c[0],    1,None, \
                            lambda x,pars: '}{%s |}}' % x)

for f in feasible:
    c,delta,skip,repeat = f
    if skip == 0 and delta == 0 and repeat > 2:
        ok = True
        for i in range(c[0],c[0]+repeat-1):
            if i in repeated:
                ok = False
        if ok:
            for i in range(c[0],c[0]+repeat-1):
                repeated.add(i)
            print('%%',c,"-> multi repeat")
            bar_func[c[0]] = ('multi %d' % repeat,repeat,repeat,\
                        lambda x,pars: '\\repeat percent %d { %s }|' % (pars,x))

for f in feasible:
    c,delta,skip,repeat = f
    if skip == 0 and delta == 1:
        if c[0] not in repeated:
            print('%%',c,"-> simple repeat")
            bar_func[c[0]] = ('simple',2,None,lambda x,pars: '\\repeat percent 2 { %s }|' % x)

# RECREATE in lilypond format
print('\\version "2.18.2"')

finfo = sys.argv[1].replace('.mid','').split(' - ')
title = finfo[0]
composer = finfo[1] if len(finfo) > 1 else ''
print('\\header {')
print('  title = "%s"' % title)
print('  composer = "%s"' % composer)
print('}')

for k in voices:
    if track_type[k] == 'drums':
        print(k,'= \\drummode {')
    else:
        print(k,'= {')
    i = 0
    while i < max_bar:
        info,delta,pars,bfunc = bar_func[i]
        s = bfunc(bars[k][i],pars)
        print(s,' %% %d' % i,info)
        i += delta
    print('}')

lpiano_voices = []
rpiano_voices = []
drum_voices   = []
song_voices   = []
while len(voices) > 0:
    k = voices.pop()
    if track_type[k] == 'piano left':
        lpiano_voices.append(k)
    elif track_type[k] == 'piano right':
        rpiano_voices.append(k)
    elif track_type[k] == 'drums':
        drum_voices.append(k)
    else:
        song_voices.append(k)

print('%% Piano links =',lpiano_voices)
print('%% Piano rechts=',rpiano_voices)
print('%% Drum=' ,drum_voices)
print('%% Song=' ,song_voices)

pianostaff = ''
drumstaff  = ''
songstaff  = ''

if len(rpiano_voices) > 0:
    pianostaff  = '\\new PianoStaff << \\context Staff = "1" << '
    pianostaff += '\\set PianoStaff.instrumentName = #"Piano"'
    for v,x in zip(rpiano_voices,['One','Two','Three','Four']):
        pianostaff += '\\context Voice = "RPiano%s" { \\voice%s \\clef "treble" \\key %s  \\numericTimeSignature\\time 4/4 \\%s}' % (x,x,key,v)
    pianostaff += '>> \\context Staff = "2" <<'
    for v,x in zip(lpiano_voices,['One','Two','Three','Four']):
        pianostaff += '\\context Voice = "LPiano%s" { \\voice%s \\clef "bass" \\key %s  \\numericTimeSignature\\time 4/4 \\%s}' % (x,x,key,v)
    pianostaff += '>> >>'

if len(drum_voices) > 0:
    drumstaff  = '\\new DrumStaff <<'
    for v,x in zip(drum_voices,['One','Two','Three','Four']):
        drumstaff += '\\new DrumVoice {\\voice%s \\clef "percussion" \\numericTimeSignature\\time 4/4 \\%s}' % (x,v)
    drumstaff += '>>'


print("""
% The score definition
\\book {
  \\score {
    <<
            \\set Score.alternativeNumberingStyle = #'numbers-with-letters
""")
for v,x in zip(song_voices,['One','Two','Three','Four']):
    print('\\new Voice = "melody%s" { \\voice%s \\clef "bass" \\key %s  \\numericTimeSignature\\time 4/4 \\%s}' % (x,x,key,v))
print(pianostaff)
print(drumstaff)
print("""
    >>
    \\layout {}
  }
    \\header {
        tagline = "%s"
    }
}
""" % title)

print("""
% The score definition
\\score {
    \\unfoldRepeats
    <<
""")
for v in song_voices:
    print('\\new Voice = melody \\%s' % v)
print(pianostaff)
print(drumstaff)
print("""
    >>
    \\midi {
            \\tempo 4 = 127
    }
}
""")

