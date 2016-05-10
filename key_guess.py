#!/usr/bin/env python3.4
import sys
import python_midi as midi

notes = ['C  /C  ','Cis/Des','D  /D  ','Dis/Ees','E  /E  ','F  /F  ',
         'Fis/Ges','G  /G  ','Gis/As ','A  /A  ','Ais/Bb ','B  /B  ']

#                                                           number of sharps +/flats -
ref = {             # c   d   e f   g   a   h    alternate  |
        'C   \\major': [1,0,1,0,1,1,0,1,0,1,0,1,  'A   \\minor',0],
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

def calculate(p):
    global ref

    # Guess the key
    keys = list(ref.keys())

    stats = [0]*len(ref)

    key_ticks = []

    fifo = []
    for ev in p:
        if type(ev) is midi.events.NoteOnEvent and ev.data[1] > 0:
            fifo.append(ev)
            note = ev.data[0] % 12
            for i in range(len(ref)):
                stats[i] += ref[keys[i]][note]
            sm = max(stats)
            if stats.count(sm) == 1:
                key = keys[stats.index(sm)]
                if len(key_ticks) == 0:
                    key_ticks.append( [0,ev.tick,key] )
                elif key_ticks[-1][2] == key:
                    key_ticks[-1][1] = ev.tick
                else:
                    key_ticks.append( [fifo[0].tick,ev.tick,key] )

                while stats.count(sm) == 1:
                    ev = fifo.pop(0)
                    note = ev.data[0] % 12
                    for i in range(len(ref)):
                        stats[i] -= ref[keys[i]][note]
                    sm = max(stats)

    return(key_ticks)

if __name__ == '__main__':
    calculate_scales()
    for c in ref:
        print(c,ref[c])
