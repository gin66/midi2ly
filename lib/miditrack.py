import python_midi   as midi
import lib.lilypond  as lilypond

class MidiNote(object):
    def __init__(self,track,pitch,velocity,at_tick,duration,extended=False):
        self.note     = midi.constants.NOTE_VALUE_MAP_FLAT[pitch]
        self.track    = track
        self.pitch    = pitch
        self.velocity = velocity
        self.at_tick  = at_tick
        self.duration = duration
        self.extended = extended      # is True, if has following note

    def __str__(self):
        return 'Note(%s:%d,%d,%d ticks) in %s at %d' \
                % (self.note,self.pitch,self.velocity,\
                   self.duration,self.track,self.at_tick)

class MidiLyric(object):
    def __init__(self,track,text,at_tick):
        self.track    = track
        self.text     = text
        self.at_tick  = at_tick

    def __str__(self):
        return 'Lyric(%s) in %s at %d' \
                % (self.text,self.track,self.at_tick)

class MidiTrack(object):
    tracklist  = []
    tracks     = {}
    ticks_set  = set()
    ticks      = []
    bars       = []     # List of tuples (start tick,end tick)
    resolution = None   # Ticks per quarter note

    @classmethod
    def fill_bars(cls): # for now assume 4/4
        max_tick = 0
        for mtk in cls.tracks:
            notes = cls.tracks[mtk].notes
            if len(notes) > 0:
                max_tick = max(max(n.at_tick+n.duration for n in notes),max_tick)
        st = 0
        while st < max_tick:
            cls.bars.append( (st,st+4*cls.resolution-1) )
            st += 4*cls.resolution

    @classmethod
    def get_bar_decorators_with_repeat(cls):
        bar_deco = []
        for i in range(len(MidiTrack.bars)):
            bar_deco.append( { 'info'     :'orig',
                               'pre'      : '',
                               'fmt'      : '%(pre)s %(bar)s %(post)s  %% %(info)s',
                               'post'     : ' |',
                               'repeated' : False} )

        # join all lilypond representation of all bars together
        # Only bars to be printed have those. No further selection needed.
        bar_dict = {}
        max_bar = len(cls.bars)
        for i in range(max_bar):
            bdata = ''
            for mt in cls.tracklist:
                if len(mt.bar_lily_notes) > i:
                    bdata += mt.bar_lily_notes[i]
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

        # Check for sequences > 2
        for v in dup_dict:
            d = dup_dict[v]
            c = sorted([x for x in d if x >= v])
            if len(c) > 2 and c[-1]-v == len(c)-1:
                feasible.append( (c,1,0,len(c)) )

        feasible = sorted(feasible,key=lambda x:(x[1]-x[2])*x[3],reverse=True)

        for c in feasible:
            print('%% feasible:',c)

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
        return bar_deco

    def __new__(self,pattern,verbose):
        trackname = None
        for e in pattern:
            if type(e) is midi.events.TrackNameEvent:
                trackname = e.text
                break

        instrument = None
        for e in pattern:
            if type(e) is midi.events.InstrumentNameEvent:
                instrument = e.text
                break

        key = '%s_%s' % (trackname,instrument)
        key = key.replace(' ','_')
        if key in MidiTrack.tracks:
            return MidiTrack.tracks[key]

        instance = super().__new__(MidiTrack)

        instance.index          = len(MidiTrack.tracklist)+1
        instance.verbose        = verbose
        instance.key            = key
        instance.trackname      = trackname
        instance.instrument     = instrument
        instance.notecount_128  = [0]*128
        instance.notecount_12   = [0]*12
        instance.notes          = []
        instance.lyrics         = []
        instance.output         = False
        instance.output_piano   = False
        instance.output_drums   = False
        instance.output_voice   = False
        instance.output_lyrics  = False
        instance.bar_lily_notes = []
        instance.bar_lily_words = []
        MidiTrack.tracks[key]   = instance
        MidiTrack.tracklist.append(instance)
        return instance

    def __init__(self,pattern,verbose):
        # Be careful here, because self may be a reused instance
        # with same track and instrument name.
        # Reason:
        #    Logic Pro X puts regions in a track into separate midi patterns
        pattern.make_ticks_abs()

        # Collect all ticks in class variable ticks for all tracks
        for e in pattern:
            if type(e) is midi.events.NoteOnEvent and e.velocity > 0:
                MidiTrack.ticks_set.add(e.tick)
        MidiTrack.ticks=sorted(list(MidiTrack.ticks_set))

        # Logic Pro X seldom uses NoteOff but NoteOn with velocity zero instead
        transient = {}
        for e in pattern:
            if verbose:
                print('%% Event: ',e)
            if type(e) is midi.events.LyricsEvent:
                lyr = MidiLyric(self,e.text,e.tick)
                self.lyrics.append(lyr)
                if verbose:
                    print('%% => ',lyr)

            if type(e) is midi.events.NoteOnEvent and e.velocity > 0:
                if e.pitch in transient:
                    transient[e.pitch].append(e)
                else:
                    transient[e.pitch] = [e]

                self.notecount_128[e.pitch     ] += 1
                self.notecount_12 [e.pitch % 12] += 1

            if type(e) is midi.events.NoteOnEvent and e.velocity == 0 \
                    or type(e) is midi.events.NoteOffEvent:
                if e.pitch not in transient:
                    print('%% NoteOff without NoteOn: ',e)
                    raise
                se = transient[e.pitch].pop(0)
                if len(transient[e.pitch]) == 0:
                    del transient[e.pitch]

                note = MidiNote(self,se.pitch,se.velocity,se.tick,e.tick-se.tick)
                self.notes.append(note)
                if verbose:
                    print('%% => ',note)
        if len(transient) > 0:
            raise Exception('MIDI-File damaged: Stuck Notes detected')

        self.notes = sorted(self.notes,key=lambda n:n.at_tick)

    def advise_treble(self): # useful for piano to select bass or treble
        s_bass   = sum(self.notecount_128[:60])
        s_treble = sum(self.notecount_128[60:])
        return s_bass < s_treble

    def trim_notes(self):
        # Trim notes on 1/64 note
        res = MidiTrack.resolution // 16
        for n in self.notes:
            dt = ((n.at_tick+res//2)//res)*res - n.at_tick
            if dt != 0:
                print('%% trim note %s by shifting %d ticks (res=%d)' % (n,dt,res))
                n.at_tick  += dt
                n.duration += dt
            dt = ((n.duration+res//2)//res)*res - n.duration
            if dt != 0:
                print('%% trim note %s by %d ticks (res=%d)' % (n,dt,res))
                n.duration += dt

    def split_same_time_notes_to_same_length(self):
        active   = []
        newnotes = []
        for n in self.notes:
            active.append(n)
            newnotes.append(n)
            active = [nx for nx in active if nx.at_tick+nx.duration > n.at_tick]
            to_cut = [nx for nx in active if nx.at_tick <  n.at_tick]
            for nx in to_cut:
                dt = n.at_tick-nx.at_tick-1
                print('%% split %s after %d ticks' % (nx,dt))
                np = MidiNote(nx.track,nx.pitch,nx.velocity,nx.at_tick,dt,True)
                newnotes.append(np)
                nx.duration -= dt
                nx.at_tick   = n.at_tick

        while len(active) > 0:
            dt = min(n.duration for n in active)
            active = [n for n in active if n.duration > dt]
            for n in active:
                np = MidiNote(n.track,n.pitch,n.velocity,n.at_tick,dt,True)
                newnotes.append(np)
                n.duration -= dt
                n.at_tick  += dt
                print('%% split last %s after %d ticks' % (n,dt))

        self.notes = sorted(newnotes,key=lambda n:n.at_tick)

    def split_notes_at_bar(self):
        newnotes = []
        while(len(self.notes)) > 0:
            n = self.notes.pop(0)
            newnotes.append(n)
            for bs,be in MidiTrack.bars:
                if bs <= n.at_tick and be > n.at_tick:
                    if n.at_tick+n.duration-1 > be:
                        dt = n.at_tick + n.duration - (be + 1)
                        print('%% split note %s by %d ticks at bar %d-%d ticks' % (n,dt,bs,be))
                        np = MidiNote(n.track,n.pitch,n.velocity,be,dt,False)
                        self.notes.append(np)
                        n.duration -= dt
                    break
        self.notes = sorted(newnotes,key=lambda n:n.at_tick)

    def convert_notes_to_bars_as_lilypond(self):
        if not self.output:
            return
        for n in self.notes:
            if self.output_piano or self.output_voice:
                n.lily = lilypond.NOTE[n.pitch]
            elif self.output_drums:
                n.lily = lilypond.PERC[n.pitch]

        if self.output_drums or self.output_voice or self.output_piano:
            for bs,be in MidiTrack.bars:
                bar = [n for n in self.notes if bs <= n.at_tick and be > n.at_tick]
                print('%% Convert bar to lilypond (%d-%d) ticks' % (bs,be))
                for n in bar:
                    print('%%      ',n)
                l = self.__to_lily__(bar,bs,be)
                self.bar_lily_notes.append(l)
                print('%%  -> ',l)

    def __to_lily__(self,bar,bs,be):
        l = []
        tick = bs
        while tick <= be:
            notes     = [n for n in bar if n.at_tick >= tick]
            if len(notes) == 0:
                dt = be+1 - tick
            else:
                next_tick = min(n.at_tick for n in notes)
                notes     = [n for n in bar if n.at_tick == next_tick]
                dt = next_tick - tick

            if dt > 0:  # need pause
                dur,dt = lilypond.select_duration(tick,be+1,dt,MidiTrack.resolution*4)
                ls = 'r'
            elif len(notes) > 0:
                dt = notes[0].duration
                dur,dt = lilypond.select_duration(tick,be+1,dt,MidiTrack.resolution*4)
                ls = []
                if len(notes) > 1:
                    ls.append('<')
                for n in notes:
                    ls.append(n.lily)
                if len(notes) > 1:
                    ls.append('>')
                ls = ' '.join(ls)

            tick += dt
            for d in dur:
                l.append(ls + d)

        if tick-be != 1:
            raise Exception('Internal Error %d != %d + 1' % (tick,be))
        return ' '.join(l)

    def __str__(self):
        s = 'Track(%s,%s)' % (self.trackname,self.instrument)
        if len(self.lyrics) > 0:
            s += ' with %d lyric events' % len(self.lyrics)
        return s
