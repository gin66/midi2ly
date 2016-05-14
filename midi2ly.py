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

bar_deco = MidiTrack.get_bar_decorators_with_repeat()

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

    del_silence = True
    while del_silence:
        for k in all_lily:
            if bars[k][0] != 'r1':
                del_silence = False
                break
        if del_silence:
            for k in all_lily:
                bars[k].pop(0)


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
            if mt.advise_treble():
                rpiano_voices.append(mt.key)
            else:
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

if len(song_voices) > 0:
    songstaff  = '\\new Staff <<'
    for v,x in zip(song_voices,['One','Two','Three','Four']):
        songstaff += '\\new Voice {\\voice%s \\clef "treble" %s \\%s}' % (x,time_sig,v)
    songstaff += '>>'


print("""
% The score definition
\\book {
  \\score {
    <<
            \\set Score.alternativeNumberingStyle = #'numbers-with-letters
""")
#for v,x in zip(song_voices,['One','Two','Three','Four']):
#    print('\\new Voice = "melody%s" { \\voice%s \\clef "bass" \\key %s %s \\%s}' % (x,x,key,time_sig,v))
print(songstaff)
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
print(songstaff)
print(pianostaff)
print(drumstaff)
print("""
    >>
    \\midi {
            \\tempo 4 = 127
    }
}
""")

