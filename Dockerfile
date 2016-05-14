# BUILD:        docker build -t pymidi .
# RUN:          docker run -it --rm -v "`pwd`":/in pymidi '<MIDI-FILE>'
#
# Midi-file shall not be a symbolic link.
# Output is the ly file to stdout

FROM python:3.5.1-slim

RUN mkdir -p /usr/src/app/lib
RUN mkdir -p /usr/src/app/python_midi
RUN mkdir -p /in

WORKDIR /in

COPY *.py /usr/src/app/
COPY lib/*.py /usr/src/app/lib/
COPY python_midi/*.py /usr/src/app/python_midi/

ENTRYPOINT [ "python", "/usr/src/app/midi2ly.py" ]

