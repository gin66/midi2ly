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
parser.add_argument('-n', action='store_true', dest='no_repeat', help='Do not use repeats')
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
    mt.trim_lyrics()
    mt.split_same_time_notes_to_same_length()

MidiTrack.fill_bars()
print('%% ',MidiTrack.bars)
print('%% ',len(MidiTrack.bars))
for mt in MidiTrack.tracklist:
    mt.split_notes_at_bar()

key_tracks = [ mt for mt in MidiTrack.tracklist if mt.output_piano or mt.output_voice]
# Tuples with (starttick,endtick,key,stats)
key_list = key_guess.calculate(key_tracks)
print('%% KEYS: ',key_list)

for mt in MidiTrack.tracklist:
    mt.convert_notes_to_bars_as_lilypond()
    mt.convert_lyrics_to_bars_as_lilypond()

if not args.no_repeat:
    MidiTrack.identify_repeats()
    for mt in MidiTrack.tracklist:
        mt.collect_lyrics_for_repeats()

bar_deco = MidiTrack.get_bar_decorators_with_repeat(key_list)

if False:
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
lyric_voices  = []
for mt in MidiTrack.tracklist:
    if mt.output:
        mode = ''
        key = 'Track%c' % (64+mt.index)
        fmt = None
        if mt.output_drums:
            drum_voices.append(key)
            bars = mt.bar_lily_notes
            mode = '\\drummode'
            fmt = 'fmt_drum'
        if mt.output_piano:
            if mt.advise_treble():
                rpiano_voices.append(key)
            else:
                lpiano_voices.append(key)
            bars = mt.bar_lily_notes
            fmt = 'fmt_voice'
        if mt.output_voice:
            song_voices.append(key)
            bars = mt.bar_lily_notes
            fmt = 'fmt_voice'
        if fmt is not None:
            print(key,'= ' + mode + '{')
            for deco,bar in zip(bar_deco,bars):
                deco['bar'] = bar
                print(deco[fmt] % deco)
            print('}')
for mt in MidiTrack.tracklist:
    if mt.output:
        if mt.output_lyrics:
            mode = ''
            for bars,cnt in zip(mt.bar_lily_words,'ABCDEFGHIJKLM'):
                key = mt.key + '_Lyric_' + cnt
                lyric_voices.append(key)
                mode = '\\lyricmode'
                fmt = 'fmt_lyric'
                print(key,'= ' + mode + '{')
                for deco,bar in zip(bar_deco,bars):
                    deco['bar'] = bar
                    print(deco[fmt] % deco)
                print('}')

print('%% Piano links =',lpiano_voices)
print('%% Piano rechts=',rpiano_voices)
print('%% Drum=' ,drum_voices)
print('%% Song=' ,song_voices)

pianostaff = ''
drumstaff  = ''
songstaff  = ''
lyricstaff = ''

key = '\\key c \\major'
if len(lpiano_voices) > 0 or len(rpiano_voices) > 0:
    pianostaff  = '\\new PianoStaff << \\context Staff = "1" << '
    pianostaff += '\\set PianoStaff.instrumentName = #"Piano"'
    for v,x in zip(rpiano_voices,['One','Two','Three','Four']):
        pianostaff += '\\context Voice = "RPiano%s" { \\voice%s \\clef "treble" \\%s }' % (x,x,v)
    pianostaff += '>> \\context Staff = "2" <<'
    for v,x in zip(lpiano_voices,['One','Two','Three','Four']):
        pianostaff += '\\context Voice = "LPiano%s" { \\voice%s \\clef "bass" \\%s }' % (x,x,v)
    pianostaff += ' >> >>'

if len(drum_voices) > 0:
    drumstaff  = '\\new DrumStaff <<'
    for v,x in zip(drum_voices,['One','Two','Three','Four']):
        drumstaff += '\\new DrumVoice {\\voice%s \\clef "percussion" \\%s }' % (x,v)
    drumstaff += ' >>'

if len(song_voices) > 0:
    songstaff  = '\\new Staff <<'
    for v,x in zip(song_voices,['One','Two','Three','Four']):
        songstaff += '\\new Voice {\\voice%s \\clef "treble" \\%s }' % (x,v)
    songstaff += ' >>'

if len(lyric_voices) > 0:
    for v in lyric_voices:
        lyricstaff += '\\new Lyrics \\' + v

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
print(lyricstaff)
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

