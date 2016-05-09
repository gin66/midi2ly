#!/usr/bin/env python3.4
import sys
import python_midi as midi

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
