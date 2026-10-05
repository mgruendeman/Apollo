"""Tape pieces in mission order."""

def _end(s):
    return s['get'] + (s['to'] - s['from']) * s['rate']


def _density(s):
    """How much of NASA's transcript a piece carries: anchors per minute."""
    if s.get('pinned'):
        return 1e9
    return 60 * s.get('anchors', 0) / max(1.0, (s['to'] - s['from']) * s['rate'])


def _part(s, g0, g1):
    """The part of piece s playing mission time g0..g1."""
    return {**s, 'from': round(s['from'] + (g0 - s['get']) / s['rate'], 2),
            'to': round(s['from'] + (g1 - s['get']) / s['rate'], 2), 'get': round(g0, 2)}


def trim_overlaps(segments):
    """Tapes were changed over with some overlap: play each tape to its end
    and pick up the next where it left off (trim the later piece's start).
    But where the piece playing carries few of NASA's lines (under an
    anchor a minute) and one it overlaps twice as many, the second plays
    instead, and the first is cut around it: on Apollo 8's launch tape the
    announcer relays the crew's calls live, over them, and plays the
    air-to-ground back a quarter hour later, so the playback is where the
    crew are heard. (Two recordings of the same conversation carry its
    lines alike, so the earlier plays on and the player doesn't hop between
    them.)"""
    segments.sort(key=lambda s: s['get'])
    out = []   # (in mission order, never overlapping)
    for b in segments:
        if b['to'] - b['from'] <= 1:
            continue
        claims = [(b['get'], _end(b))]   # the mission time b still plays
        kept = []
        for a in out:
            a0, a1 = a['get'], _end(a)
            new_claims, cut_a = [], []
            for c0, c1 in claims:
                lo, hi = max(a0, c0), min(a1, c1)
                if hi - lo <= 1:
                    new_claims.append((c0, c1))
                    continue
                # (b displaces a only from its first line on: the tape before that is the cut's slack)
                first = b['get'] + (b.get('first', b['from']) - b['from']) * b['rate']
                if _density(b) >= 2 * _density(a) and _density(a) < 1.0 and _density(b) > 0 and hi - max(lo, first) > 1:
                    if lo - c0 > 1:
                        new_claims.append((c0, lo))
                    new_claims.append((max(lo, first), c1))   # (before its first line, b yields to a as usual)
                    cut_a.append((max(lo, first), hi))
                else:   # a plays here; b keeps what's outside
                    if lo - c0 > 1:
                        new_claims.append((c0, lo))
                    if c1 - hi > 1:
                        new_claims.append((hi, c1))
            claims = new_claims
            if cut_a:
                edges = [a0] + [x for lo, hi in sorted(cut_a) for x in (lo, hi)] + [a1]
                for g0, g1 in zip(edges[::2], edges[1::2]):
                    if g1 - g0 > 1:
                        kept.append(_part(a, g0, g1))
            else:
                kept.append(a)
        out = kept + [_part(b, g0, g1) for g0, g1 in claims if g1 - g0 > 1]
        out.sort(key=lambda s: s['get'])
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
