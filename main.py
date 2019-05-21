from mido import MidiFile
NOTES = [
    "c",
    "d-",
    "d",
    "e-",
    "e",
    "f",
    "g-",
    "g",
    "a-",
    "a",
    "b-",
    "b",
]
ZERO_OCTAVE_START = 12
OCTAVE_SIZE = 12

TICKS_PER_SECOND = 960 * 4
SECONDS_PER_SEGMENT = 2
TICKS_PER_SEGMENT = float(TICKS_PER_SECOND * SECONDS_PER_SEGMENT)
SMALLEST_DURATION = TICKS_PER_SEGMENT / 64
MAX_NOTES = 4750

SIMULATION_STEP_SIZE = SMALLEST_DURATION
NOTE_DURATION = "8"
PAN_OUT = True


def convert_midi_note(midi_note, velocity):
    octave = int((midi_note - ZERO_OCTAVE_START) / OCTAVE_SIZE)
    note_index = int(midi_note % OCTAVE_SIZE)
    if velocity > 0:
        note = NOTES[note_index]
    else:
        note = "r"
    return octave, note

class Note:
    def __init__(self, absolute_time, octave, note):
        self.octave = octave
        self.absolute_time = absolute_time
        self.note = note
        self.has_played = False

    def render(self, current_time):
        if current_time >= self.absolute_time and not self.has_played:
            self.has_played = True
            return {
                "result": f"{self.note}{NOTE_DURATION}",
                "octave": self.octave,
            }
        return None


def parse_track(track):
    last_octave = None
    current_time = 0
    notes = []
    for event in track:
        if event.is_meta:
            print(event)
            current_time += event.time
            continue
        if event.type != "note_on":
            print(event)
            continue
        octave, note = convert_midi_note(event.note, event.velocity)
        last_octave = octave

        current_time = current_time + event.time
        if note == "r":
            continue
        notes.append(Note(
            absolute_time=current_time,
            octave=octave,
            note=note,
        ))
    return notes

def get_octave_prefix(last_octave, current_octave):
    octave_prefix = ""
    if last_octave is None:
        octave_prefix = f"o{current_octave}"
    elif current_octave > last_octave:
        diff = current_octave - last_octave
        if diff <= 2:
            octave_prefix = ">" * diff
        else:
            octave_prefix = f"o{current_octave}"
    elif current_octave < last_octave:
        diff = (last_octave - current_octave)
        if diff <= 2:
            octave_prefix = "<" * diff
        else:
            octave_prefix = f"o{current_octave}"
    return octave_prefix

def measure_length(tracks):
    total = ""
    for track in tracks:
        if not track.replace(f"r{NOTE_DURATION}", ""):
            continue
        total += track
    total = total.replace("r64r64", "r32")
    total = total.replace("r32r32", "r16")
    total = total.replace("r16r16", "r8")
    total = total.replace("r8r8", "r4")
    total = total.replace("r4r4", "r2")
    total = total.replace("r2r2", "r1")
    return len(total)

def render_notes(notes):
    simulate = True
    current_time = 0
    time_per_simulation_step = SIMULATION_STEP_SIZE
    last_octaves = [None for i in range(10)]
    tracks = ["" for i in range(10)]
    while simulate:
        events = [note.render(current_time) for note in notes]
        events = [x for x in events if x is not None]
        for i in range(len(tracks)):
            if len(events) > i:
                event = events[i]
                octave_prefix = get_octave_prefix(
                    last_octaves[i],
                    event["octave"]
                )
                tracks[i] += octave_prefix + event["result"]
                last_octaves[i] = event["octave"]
            else:
                tracks[i] += f"r{NOTE_DURATION}"
        notes = [x for x in notes if not x.has_played]
        simulate = len(notes) > 0
        current_time += time_per_simulation_step
        if measure_length(tracks) > MAX_NOTES:
            break
    for i in range(len(tracks)):
        if not tracks[i].replace(f"r{NOTE_DURATION}", ""):
            tracks[i] = ""
            continue
        tracks[i] = tracks[i].replace("r64r64", "r32")
        tracks[i] = tracks[i].replace("r32r32", "r16")
        tracks[i] = tracks[i].replace("r16r16", "r8")
        tracks[i] = tracks[i].replace("r8r8", "r4")
        tracks[i] = tracks[i].replace("r4r4", "r2")
        tracks[i] = tracks[i].replace("r2r2", "r1")
    for track in tracks:
        if track:
            print("#" * 2)
            prefix = "v15t124"
            if PAN_OUT:
                prefix += "s1"
            print(prefix + track)

def convert_file(path):
    mid = MidiFile(path)
    notes = []
    for track in mid.tracks:
        notes = notes + parse_track(track)
    render_notes(notes)


def main():
    convert_file("Command__Conquer_Red_Alert_3_-_Soviet_March_piano_solo.mid")

if __name__ == "__main__":
    main()
