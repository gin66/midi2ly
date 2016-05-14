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
            if dt > 0:
                print('%% trim note %s by shifting %d ticks (res=%d)' % (n,dt,res))
                n.at_tick  += dt
                n.duration += dt
            dt = ((n.duration+res//2)//res)*res - n.duration
            if dt > 0:
                print('%% trim note %s by %d ticks (res=%d)' % (n,dt,res))
                n.duration += dt

    def split_same_time_notes_to_same_length(self):
        active   = []
        newnotes = []
        for n in self.notes:
            active.append(n)
            newnotes.append(n)
            active = [nx for nx in active if nx.at_tick+nx.duration > n.at_tick]
            to_cut = [nx for nx in active if nx.at_tick != n.at_tick]
            for nx in to_cut:
                dt = n.at_tick-nx.at_tick-1
                print('%% split note %s after %d ticks' % (n,dt))
                np = MidiNote(nx.track,nx.pitch,nx.velocity,nx.at_tick,dt,True)
                newnotes.append(np)
                nx.duration -= dt
                nx.at_tick   = n.at_tick

        while len(active) > 0:
            dt = min(n.duration for n in active)
            active = [n for n in active if n.duration > dt]
            for n in to_cut:
                np = MidiNote(n.track,n.pitch,n.velocity,n.at_tick,dt,True)
                newnotes.append(np)
                n.duration -= dt
                n.at_tick  += dt
                print('%% split note %s after %d ticks' % (n,dt))

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
