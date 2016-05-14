#!/usr/bin/env python3.4
import sys
import python_midi as midi

notes = ['C  /C  ','Cis/Des','D  /D  ','Dis/Ees','E  /E  ','F  /F  ',
         'Fis/Ges','G  /G  ','Gis/As ','A  /A  ','Ais/Bb ','B  /B  ']

#                                                           number of sharps +/flats -
ref = {             # c   d   e f   g   a   h    alternate  |
        'C   \\major': [1,0,1,0,1,1,0,1,0,1,0,1,  'A   \\minor',0],
    }

#
chords = {          # c   d   e f   g   a   h,c   d   e f   g   a   h c
        'Cdim'     : [1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Cdim7'    : [1,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Cdimb9'   : [1,0,0,1,0,0,1,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        'Cdim11'   : [1,0,0,1,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0],
        'Cdim9'    : [1,0,0,1,0,0,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
        'Cmin7dim5': [1,0,0,1,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'CØb9'     : [1,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        'CØ11'     : [1,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,0,0,0,0,0],
        'CØ13'     : [1,0,0,1,0,0,1,0,0,0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,0],
        'CØ9'      : [1,0,0,1,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
        'Cmin'     : [1,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Cmin7'    : [1,0,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Cminmaj9' : [1,0,0,1,0,0,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0],
        'Cminmaj11': [1,0,0,1,0,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0],
        'Cminmaj13': [1,0,0,1,0,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0,0,1,0,0,0],
        'Cmin9'    : [1,0,0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
        'Cmin11'   : [1,0,0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0],
        'Cmin13'   : [1,0,0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,0],
        'Cdom7dim5': [1,0,0,0,1,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Cmaj'     : [1,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Cmaj6'    : [1,0,0,0,1,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Cmaj7'    : [1,0,0,0,1,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Cmaj9'    : [1,0,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0],
        'Cmaj11'   : [1,0,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0],
        'Cmaj13'   : [1,0,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0,0,1,0,0,0],
        'Cdom7'    : [1,0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Cdom9'    : [1,0,0,0,1,0,0,1,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
        'Cdom11'   : [1,0,0,0,1,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0],
        'Cdom13'   : [1,0,0,0,1,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,0],
        'Caug'     : [1,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Caug7'    : [1,0,0,0,1,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Caug9'    : [1,0,0,0,1,0,0,0,1,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
        'Caug11'   : [1,0,0,0,1,0,0,0,1,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0],
        'Caug13'   : [1,0,0,0,1,0,0,0,1,0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,0],
        'Caugmaj7' : [1,0,0,0,1,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Caugmaj9' : [1,0,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0],
        'Caugmaj11': [1,0,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0],
        'Caugmaj13': [1,0,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0,1,0,0,0,1,0,0,0],
        'Csus'     : [1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Csus2'    : [1,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        'Csus4'    : [1,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    }

def calculate_scales():
    global ref
    # Rotate c major profile and determine sharps/flats
    base = ref['C   \\major'][:12]
    curr = base.copy()
    for i in range(12):
        bcnt  = 0
        ccnt  = 0
        sharp = 0
        flat  = 0
        for mx in zip(base,curr):
            bcnt += mx[0]
            ccnt += mx[1]
            if mx[1] and mx[0] != mx[1]:
                if bcnt < ccnt:
                    flat  += 1
                else:
                    sharp += 1
        major = notes[ i   %12]
        minor = notes[(i+9)%12]
        major = (major+'/'+major).split('/')[0] + ' \major'
        minor = (minor+'/'+minor).split('/')[0] + ' \minor'
        ref[major] = curr + [minor,sharp-flat]
        curr.insert(0,curr.pop())   # Rotate one half-tone

def calculate(tracks):
    global ref

    # Guess the key
    keys = list(ref.keys())

    stats = [0]*len(ref)

    key_ticks = []

    notes = []
    for mt in tracks:
        notes += mt.notes
    notes = sorted(notes,key=lambda n:n.at_tick)

    fifo = []
    for n in notes:
        if len(key_ticks) > 0:
            key_ticks[-1][1] = n.at_tick+n.duration
        fifo.append(n)
        note = n.pitch % 12
        for i in range(len(ref)):
            stats[i] += ref[keys[i]][note]-1
        sm = max(stats)
        #if stats.count(sm) == 1 and stats.count(sm-1) == 0 and stats.count(sm-2) == 0:
        if stats.count(sm) == 1 and stats.count(sm-1) == 0:
        #if stats.count(sm) == 1:
            key = keys[stats.index(sm)]
            if len(key_ticks) == 0:
                key_ticks.append( [0,n.at_tick,key,stats.copy()] )
            elif key_ticks[-1][2] == key:
                key_ticks[-1][1] = n.at_tick
            else:
                key_ticks.append( [fifo[0].at_tick,n.at_tick,key,stats.copy()] )

            while stats.count(sm) == 1:
                n = fifo.pop(0)
                note = n.pitch % 12
                for i in range(len(ref)):
                    stats[i] -= ref[keys[i]][note]-1
                sm = max(stats)
    return(key_ticks)

calculate_scales()

if __name__ == '__main__':
    for c in ref:
        print(c,ref[c])
