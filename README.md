MIDI2LY
-------

A MIDI to Lilypond converter with these features:

    - Let's you select tracks and lyrics to be embedded
    - Automatic selection of piano tracks to bass/treble (no left/right split though)
    - Automatic key detection
    - Automatic detection of repeats based on identical (!) bars
    - Repeats will fold lyrics along the bar
    - Notes are adjusted (rounded) to 1/32 boundaries

Background:
-----------
In order to compile the scores for the band of my son, I have bought Logic Pro X. Nice tool, but making short scores using repeats is just a nightmare. Typical workflow is:

    1. Get the song ready in Logic primarily for Piano.
    2. Then create two more tracks for the printout
    3. In these new scores all loops are removed and repeats are type set manually.

The bad thing is:

    * If you print the long track, those repeat signs are disturbing
    * You cannot listen to the song with the repeats set.
    * Hell of manual work
    * And now imagine you want to add lyrics somehow....

So I have looked around for a solution. For music typesetting lilypond is great, so I "just" need to convert the Logic Pro music to lilypond format.
There is a nice tool musicxml2ly and Logic Pro X can export MusicXML format. So I have given it a try and it has failed miserably.
After some time looking around and looking at the MusicXML format, I have come to the conclusion of this being a dead end.
Next try has been with midi. The converter - I have found for midi to lilypond - haven't worked so well either.
Not to mention automatic repeats detection. As I have come across python-midi and I like python programming, I have decided to write my own converter.

Here it is.

Usage:
------
Please try for the latest usage:

    ./midi2ly.py -h

In case you have Logic Pro X, then follow these steps:

    1. Duplicate those tracks you want to export (assume you have used Alias+Loops)
    2. Copy whole content of the original tracks
    3. Select the new tracks and press 'J' in order to convert Alias+Loops into one region per track
    4. Export as MIDI with Alt+Apple+E
    5. Run midi2ly.py and lilypond => Done

Example:
--------

I have one midifile called "Randy Newman - When I am Gone.mid".
The embedded tracks can be listed with:

    ./midi2ly.py -l Randy\ Newman\ -\ When\ I\ am\ Gone.mid >RN.ly

And the output is:

    1 : Track(None,None)
    2 : Track(Voice,Orchestra Oboe) with 184 lyric events
    3 : Track(Intro,R)
    4 : Track(Intro,L)

The first track is the meta track. For print out of the piano score with embedded lyrics the invocation would be:

    ./midi2ly.py -L 2 -P 3,4 Randy\ Newman\ -\ When\ I\ am\ Gone.mid >RN.ly

And then for type setting + midi output with repeats expanded just do:

    lilypond RN.ly

This will create:

    RN.pdf      ... the scores
    RN-1.mid    ... with repeats unfolded

Docker:
-------

In case you lack python v3, then you can use a docker container. Either use the official one:

    docker pull gin66/midi2ly

Or create it locally with:

    docker build -t midi2ly .

And run it with

    docker run -it --rm -v "`pwd`":/in midi2ly -L 2 -P 3,4 Randy\ Newman\ -\ When\ I\ am\ Gone.mid >RN.ly

