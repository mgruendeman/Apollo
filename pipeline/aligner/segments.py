"""Tape pieces in mission order."""

def trim_overlaps(segments):
    """Tapes were changed over with some overlap: play each tape to its end
    and pick up the next where it left off (trim the later piece's start)."""
    segments.sort(key=lambda s: s['get'])
    out, reach = [], -1e9   # reach: the furthest mission time played so far
    for b in segments:
        if b['get'] < reach:
            cut = min(reach - b['get'], (b['to'] - b['from']) * b['rate'])
            b['from'] = round(b['from'] + cut / b['rate'], 2)
            b['get'] = round(b['get'] + cut, 2)
        if b['to'] - b['from'] > 1:
            out.append(b)
            reach = max(reach, b['get'] + (b['to'] - b['from']) * b['rate'])
    return out


