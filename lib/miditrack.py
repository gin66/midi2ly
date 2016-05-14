import python_midi   as midi
import lib.lilypond  as lilypond

class MidiNote(object):
    def __init__(self,track,pitch,velocity,at_tick,duration):
        self.note     = midi.constants.NOTE_VALUE_MAP_FLAT[pitch]
        self.track    = track
        self.pitch    = pitch
        self.velocity = velocity
        self.at_tick  = at_tick
        self.duration = duration

    def __str__(self):
        return 'Note(%s:%d,%d,%d ticks) in %s at %d' \
                % (self.note,self.pitch,self.velocity,self.duration,self.track,self.at_tick)

class MidiLyric(object):
    def __init__(self,track,text,at_tick):
        self.track    = track
        self.text     = text
        self.at_tick  = at_tick

    def __str__(self):
        return 'Lyric(%s) in %s at %d' \
                % (self.text,self.track,self.at_tick)

class MidiTrack(object):
    tracks = {}
    ticks_set = set()
    ticks     = []

    def __new__(self,pattern):
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
        if key in MidiTrack.tracks:
            return MidiTrack.tracks[key]

        instance = super().__new__(MidiTrack)

        instance.key           = key
        instance.trackname     = trackname
        instance.instrument    = instrument
        instance.notecount_128 = [0]*128
        instance.notecount_12  = [0]*12
        instance.notes         = []
        instance.lyrics        = []
        MidiTrack.tracks[key]  = instance
        return instance

    def __init__(self,pattern):
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
        print(len(MidiTrack.ticks))

        # Logic Pro X seldom uses NoteOff but NoteOn with velocity zero instead
        transient = {}
        for e in pattern:
            if type(e) is midi.events.LyricsEvent:
                lyr = MidiLyric(self,e.text,e.tick)
                self.lyrics.append(lyr)
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
                print('%% => ',note)
        if len(transient) > 0:
            raise Exception('MIDI-File damaged: Stuck Notes detected')

    def __str__(self):
        return 'Track(%s,%s)' % (self.trackname,self.instrument)
