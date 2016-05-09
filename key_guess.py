#!/usr/bin/env python3.4
import sys
import python_midi as midi

notes = ['C','Cis/Des','D','Dis/Es','E','F','Fis/Ges','G','Gis/As','A','Ais/Bb','B']

#                                               number of sharps +/flats -
ref = {             # c   d   e f   g   a   h   | / major 0/minor 1 fla
        'c \\major': [1,0,1,0,1,1,0,1,0,1,0,1,  0,0],
        'g \\major': [1,0,1,0,1,0,1,1,0,1,0,1,  1,0],
        'd \\major': [0,1,1,0,1,0,1,1,0,1,0,1,  2,0],
        'a \\major': [0,1,1,0,1,0,1,0,1,1,0,1,  3,0],
        'e \\major': [0,1,0,1,1,0,1,0,1,1,0,1,  4,0],
        'h \\major': [0,1,0,1,1,0,1,0,1,0,1,1,  5,0],

        'f \\major': [1,0,1,0,1,1,0,1,0,1,1,0, -1,1],
        'b \\major': [1,0,1,1,0,1,0,1,0,1,1,0, -2,1],
        'c \\minor': [1,0,1,1,0,1,0,1,1,0,1,0, -3,1],
        'f \\minor': [1,1,0,1,0,1,0,1,1,0,1,0, -4,1],
        'b \\minor': [1,1,0,1,0,1,1,0,1,0,1,0, -5,1]
    }

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
    # Experiment: Rotate c major profile and determine sharps/flats
    base = ref['c \\major'][:12]
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
        print(curr,notes[i],'major/',notes[(i+9)%12],'minor','#'*sharp + 'b'*flat)
        curr.insert(0,curr.pop())

