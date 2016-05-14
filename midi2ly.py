#!/usr/bin/env python3.4
import sys
sys.path.append('python_midi')
import argparse
import re
import python_midi   as midi
import lib.lilypond  as lilypond
import lib.key_guess as key_guess
from   lib.miditrack import *

def get_title_composer_from(args):
    global title
    global composer
    title    = 'Unknown Title'
    composer = 'Unknown Composer'
    finfo = re.sub('\.[mM][iI][dD][iI]?','',args.midifile)
    if finfo != args.midifile:
        finfo = re.split(' *- *',finfo)
        if len(finfo) == 2:
            title    = finfo[1] if args.comp_first else finfo[0]
            composer = finfo[0] if args.comp_first else finfo[1]
    if args.title is not None:
        title    = args.title[0]
    if args.composer is not None:
        composer = args.composer[0]

parser = argparse.ArgumentParser(description= \
        'Tool to convert a midi-file (e.g. from Logic Pro/X) to lilypond format\n'+
        'The midi-filename should be "<Title> - <Composer>.mid" or ".midi".\n'+
        'If title and composer are reversed, then use the -r switch.\n'+
        'Otherwise provide title and composer via commandline switch (-t/-c).\n'
        'Output is defined by the -D/-P/-V/-L switches.')
parser.add_argument('-o', nargs=1, dest='file',     help='Output processing result to file')
parser.add_argument('-t', nargs=1, dest='title',    help='Title of the song')
parser.add_argument('-c', nargs=1, dest='composer', help='Composer of the song')
parser.add_argument('-r', action='store_true', dest='comp_first', help='Composer and Title reversed in filename')
parser.add_argument('-l', action='store_true', dest='list', help='List all tracks in midi-file')
parser.add_argument('-v', action='store_true', dest='verbose', help='Include verbose information in output')
parser.add_argument('-V', nargs=1, dest='voice_list', default=[],help='Select tracks as voice  for output e.g. -V 1,2,3 ')
parser.add_argument('-D', nargs=1, dest='drum_list',  default=[],help='Select tracks as drums  for output e.g. -D 1,2,3 ')
parser.add_argument('-P', nargs=1, dest='piano_list', default=[],help='Select tracks as piano  for output e.g. -P 1,2,3 ')
parser.add_argument('-L', nargs=1, dest='lyrics_list',default=[],help='Select tracks as lyrics for output e.g. -L 1,2,3 ')
parser.add_argument('midifile', help='Midifile to be processed')
args = parser.parse_args()

get_title_composer_from(args)
if args.file is not None:
    sys.stdout = open(args.file[0], 'w')

for ax in [args.voice_list,args.drum_list,args.piano_list,args.lyrics_list]:
    if ax is not None:
        oldlist = ax.copy()
        ax.clear()
        while len(oldlist) > 0:
            ol = oldlist.pop()
            ax += ol.split(',')

midifile = args.midifile
try:
    pattern = midi.read_midifile(midifile)
except TypeError as e:
    print('Cannot read "%s" as midifile' % args.midifile)
    print('Exception says: %s' % e)
    sys.exit(2)

MidiTrack.resolution = pattern.resolution
for p in pattern:
    mt = MidiTrack(p,args.verbose)

if args.list:
    for mt in MidiTrack.tracklist:
        print(mt.index,':',mt)
    sys.exit(0)

for mt in MidiTrack.tracklist:
    n = '%d' % mt.index
    if n in args.drum_list:
        mt.output        = True
        mt.output_drums  = True
    if n in args.voice_list:
        mt.output        = True
        mt.output_voice  = True
    if n in args.piano_list:
        mt.output        = True
        mt.output_piano  = True
    if n in args.lyrics_list:
        mt.output        = True
        mt.output_lyrics = True
    mt.trim_notes()
    mt.split_same_time_notes_to_same_length()

MidiTrack.fill_bars()
print('%% ',MidiTrack.bars)
print('%% ',len(MidiTrack.bars))
for mt in MidiTrack.tracklist:
    mt.split_notes_at_bar()

for mt in MidiTrack.tracklist:
    mt.convert_notes_to_bars_as_lilypond()


if False:
    time_sig =''
    def parse_meta_track(p):
        for ev in p:
            print('% meta:',ev)
            if type(ev) is midi.events.TimeSignatureEvent:
                time_sig = '\\numericTimeSignature\\time %d/%d' % (ev.numerator,ev.denominator)

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
        print('%% KEYS',k,":",keys[k])

        if 'Bluebird' in k:
            CONV = lilypond.PERC
            track_type[k] = 'drums'
        else:
            CONV = lilypond.NOTE
            if 'L' in instrument:
                track_type[k] = 'piano left'
            elif 'R' in instrument:
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
                    v,dt = lilypond.select_duration(cur_tick,next_bar,next_bar-cur_tick,FULLBAR)
                else:
                    v,dt = lilypond.select_duration(cur_tick,next_bar,tick - cur_tick,FULLBAR)

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
                v,dt = lilypond.select_duration(cur_tick,next_bar,dt,FULLBAR)

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
            v,dt = lilypond.select_duration(cur_tick,next_bar,dt,FULLBAR)
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
            feasible.append( (c,1,0,len(c)) )

bar_deco = []
for i in range(len(MidiTrack.bars)):
    bar_deco.append( { 'info'     :'orig',
                       'pre'      : '',
                       'fmt'      : '%(pre)s %(bar)s %(post)s  %% %(info)s',
                       'post'     : ' |',
                       'repeated' : False} )

if False:
# SORT feasible
    feasible = sorted(feasible,key=lambda x:(x[1]-x[2])*x[3],reverse=True)

    for f in feasible:
        print('%% OK',f)

    for f in feasible:
        c,delta,skip,repeat = f
        if skip <= delta//2 and delta >= 2:
            last_bar = min(c[0]+(1+repeat)*delta,max_bar)-1

            ok = True
            for deco in bar_deco[c[0]:last_bar+1]:
                if deco['repeated']:
                    ok = False
            if ok:
                for deco in bar_deco[c[0]:last_bar+1]:
                    deco['repeated'] = True

                s = '%% %s -> %d repeats of %d bars' % (str(c),repeat+1,delta)
                if skip > 0:
                    s += ' with alternate end(s) of %d bars' % (delta-skip)
                print(s)
                #   delta=4,skip = 0,repeat = 2:
                #                 x  x  x  A  B  C  D  A  B  C  D  A  B  C  D  x  x  x
                #       alt_rep:  +  +  +  A  +  +  B  -  -  -  -  -  -  -  -  +  +  +
                #                        R{          }
                #
                #   delta=4,skip = 2,repeat = 1:
                #                 x  x  x  A  B     C  D  A  B  E  F  x  x  x
                #       alt_rep:  +  +  +  A  B     C  E  -  -  D  F  +  +  +
                #                        R{    } A {    }      {    }}
                #
                #   delta=4,skip = 2,repeat = 2:
                #                 x  x  x  A  B     C  D  A  B  E  F  A  B  G  H  x  x  x
                #       alt_rep:  +  +  +  A  B     C  E  -  -  D  E  -  -  D  F  +  +  +
                #                        R{    } A{{    }      {    }      {    }}
                #
                #   delta=4,skip = 1,repeat = 2:
                #                 x  x  x  A  B  C     D  A  B  C  E  A  B  C  F  x  x  x
                #       alt_rep:  +  +  +  A  +  B     C  -  -  -  G  -  -  -  H  +  +  +
                #                        R{       } A{{ }         { }         { }}
                s = '' if repeat <= 1 else '\\mark "%dx" ' % (repeat+1)
                deco = bar_deco[c[0]]
                deco['info'] = 'alt_rep A %d repeat=%d' % (c[0],repeat)
                deco['pre' ] = '\\repeat volta %d {%s' % (repeat+1,s)
                deco = bar_deco[c[0]+delta-skip-1]
                deco['post'] = '| }' if skip == 0 else '| }\\alternative{'

                if skip > 0:
                    for r in range(1,repeat+2):
                        bar_deco[    c[0]+r*delta-skip          ]['pre' ] = '{'
                        bar_deco[min(c[0]+r*delta-1   ,last_bar)]['post'] = '| }'
                # Blank all repeated bars
                for r in range(2,repeat+2):
                    for deco in bar_deco[c[0]+(r-1)*delta : min(c[0]+r*delta-skip-1,last_bar)+1]:
                        deco['fmt'] = '%% SKIP ' + deco['fmt']
                if skip > 0:
                    bar_deco[min(c[0]+(repeat+1)*delta-1,last_bar)]['post'] = '}} |'

    for f in feasible:
        c,delta,skip,repeat = f
        if skip == 0 and delta == 1 and repeat >= 1:
            ok = True
            for deco in bar_deco[c[0]:c[0]+repeat]:
                if deco['repeated']:
                    ok = False
            if ok:
                deco = bar_deco[c[0]]
                print('%%',c,"-> simple repeat")
                deco['info']     = 'simple'
                deco['pre' ]     = '\\repeat percent %d {' % (repeat)
                deco['post']     = '}|'
                deco['repeated'] = True
                for deco in bar_deco[c[0]+1:c[0]+repeat+1]:
                    deco['fmt'] = '%% SKIP: ' + deco['fmt']
                    deco['repeated'] = True

# RECREATE in lilypond format
print('\\version "2.18.2"')
print('\\header {')
print('  title = "%s"' % title)
print('  composer = "%s"' % composer)
print('}')

lpiano_voices = []
rpiano_voices = []
drum_voices   = []
song_voices   = []

for mt in MidiTrack.tracklist:
    if mt.output:
        if mt.output_drums:
            drum_voices.append(mt.key)
        if mt.output_piano:
            lpiano_voices.append(mt.key)
        if mt.output_voice:
            song_voices.append(mt.key)
        mode = '\\drummode' if mt.output_drums else ''
        print(mt.key,'= ' + mode + '{')
        for deco,bar in zip(bar_deco,mt.bar_lily_notes):
            deco['bar'] = bar
            print(deco['fmt'] % deco)
        print('}')

if False:
    for k in voices:
        if track_type[k] == 'drums':
            print(k,'= \\drummode {')
        else:
            print(k,'= {')
        for deco,bar in zip(bar_deco,bars[k]):
            deco['bar'] = bar
            print(deco['fmt'] % deco)
        print('}')

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

key = 'c \\major'
time_sig = ''
if len(lpiano_voices) > 0 or len(rpiano_voices) > 0:
    pianostaff  = '\\new PianoStaff << \\context Staff = "1" << '
    pianostaff += '\\set PianoStaff.instrumentName = #"Piano"'
    for v,x in zip(rpiano_voices,['One','Two','Three','Four']):
        pianostaff += '\\context Voice = "RPiano%s" { \\voice%s \\clef "treble" \\key %s %s \\%s}' % (x,x,key,time_sig,v)
    pianostaff += '>> \\context Staff = "2" <<'
    for v,x in zip(lpiano_voices,['One','Two','Three','Four']):
        pianostaff += '\\context Voice = "LPiano%s" { \\voice%s \\clef "bass" \\key %s %s \\%s}' % (x,x,key,time_sig,v)
    pianostaff += '>> >>'

if len(drum_voices) > 0:
    drumstaff  = '\\new DrumStaff <<'
    for v,x in zip(drum_voices,['One','Two','Three','Four']):
        drumstaff += '\\new DrumVoice {\\voice%s \\clef "percussion" %s \\%s}' % (x,time_sig,v)
    drumstaff += '>>'


print("""
% The score definition
\\book {
  \\score {
    <<
            \\set Score.alternativeNumberingStyle = #'numbers-with-letters
""")
#for v,x in zip(song_voices,['One','Two','Three','Four']):
#    print('\\new Voice = "melody%s" { \\voice%s \\clef "bass" \\key %s %s \\%s}' % (x,x,key,time_sig,v))
print(pianostaff)
print(drumstaff)
print(songstaff)
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
print(pianostaff)
print(drumstaff)
print(songstaff)
print("""
    >>
    \\midi {
            \\tempo 4 = 127
    }
}
""")

