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




def pin_pieces(pieces, pins):
    """Hand-placed stretches of one tape (pipeline/placement_fixes.json):
    where the placement got a stretch wrong and the tape shows where it
    belongs (NASA's lines heard on it, to the second). Each pin
    {tape_from, tape_to, get_from} replaces whatever covered that part of
    the tape; pieces overlapping it are cut back to either side."""
    for pin in pins:
        a, b = pin['tape_from'], pin['tape_to']
        out = []
        for p in pieces:
            if p['to'] <= a or p['from'] >= b:
                out.append(p)
                continue
            if p['from'] < a:   # the part before the pin
                out.append({**p, 'to': a})
            if p['to'] > b:   # the part after it
                out.append({**p, 'from': b, 'get': round(p['get'] + (b - p['from']) * p['rate'], 2)})
        out.append({'from': a, 'to': b, 'get': pin['get_from'], 'rate': 1.0, 'anchors': 0, 'pinned': True})
        pieces = sorted(out, key=lambda p: p['from'])
    return pieces
