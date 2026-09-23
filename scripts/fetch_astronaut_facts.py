"""Fetch birthplace, military service and spaceflights for each astronaut.

Reads the Wikipedia link of every entry in src/data/astronauts.js, finds its
Wikidata item and takes:
  place of birth (P19), with its US state or its country
  military branch (P241)
  the spaceflights that list them as crew (P1029 on the mission), by launch date
Writes src/data/astronautFacts.json, which the astronaut pages show next to
each bio. Review the output before committing: Wikidata is edited by the
public, so check anything surprising against the Wikipedia article.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / 'src' / 'data' / 'astronauts.js'
OUT = ROOT / 'src' / 'data' / 'astronautFacts.json'
UA = {'User-Agent': 'ApolloAudioArchive/1.0 (educational project)'}


def get(url):
    for attempt in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(url)


# Only actual spaceflights: Wikidata also lists Armstrong's X-15 (which
# never reached space), the Apollo-Soyuz spacecraft "CSM-111", the Skylab
# station itself, and Mercury-Atlas 10, which was cancelled.
FLIGHT = re.compile(r'^(Mercury-(Redstone|Atlas) \d+|Gemini \d+A?|Apollo \d+|Apollo–Soyuz|Skylab \d|STS-[\w-]+)$')
CANCELLED = {'Mercury-Atlas 10'}

BRANCH = {'United States Navy': 'U.S. Navy', 'United States Air Force': 'U.S. Air Force',
          'United States Marine Corps': 'U.S. Marine Corps', 'United States Army': 'U.S. Army'}

# Checked against each Wikipedia article: Wikidata names a hospital for
# Aldrin, and the colony's formal name for Anders.
BORN = {'aldrin': 'Glen Ridge, New Jersey', 'anders': 'Hong Kong'}

# Where each grew up, from the early-life section of each Wikipedia article
# (Wikidata has no such field). Where the article says so, it's the town
# they "considered their hometown"; otherwise where they grew up and went
# to high school. (town, note)
HOMETOWN = {
    'armstrong': ('Wapakoneta, Ohio', None),
    'aldrin': ('Montclair, New Jersey', None),
    'collins': ('Washington, D.C.', 'an Army family that moved often'),
    'borman': ('Tucson, Arizona', None),
    'lovell': ('Milwaukee, Wisconsin', None),
    'anders': ('El Cajon, California', 'a Navy family: Hong Kong and Annapolis before California'),
    'mcdivitt': ('Kalamazoo, Michigan', None),
    'scott': ('Riverside, California, and Washington, D.C.', 'an Air Force family'),
    'schweickart': ('Neptune Township, New Jersey', 'on the family farm'),
    'stafford': ('Weatherford, Oklahoma', None),
    'young': ('Orlando, Florida', None),
    'cernan': ('Bellwood and Maywood, Illinois', None),
    'conrad': ('Philadelphia, Pennsylvania', None),
    'gordon': ('Seattle and Poulsbo, Washington', None),
    'bean': ('Fort Worth, Texas', None),
    'swigert': ('Denver, Colorado', None),
    'haise': ('Biloxi, Mississippi', None),
    'shepard': ('Derry, New Hampshire', None),
    'roosa': ('Claremore, Oklahoma', None),
    'mitchell': ('Artesia, New Mexico', None),
    'worden': ('Jackson, Michigan', None),
    'irwin': ('Salt Lake City, Utah', None),
    'mattingly': ('Miami, Florida', None),
    'duke': ('Lancaster, South Carolina', None),
    'evans': ('Topeka, Kansas', None),
    'schmitt': ('Silver City, New Mexico', None),
    'allen': ('Crawfordsville, Indiana', None),
    'fullerton': ('Portland, Oregon', None),
    'mccandless': ('Long Beach, California', 'a Navy family'),
    'carr': ('Santa Ana, California', None),
    'henize': ('Cincinnati, Ohio', 'on a dairy farm outside the city'),
    'overmyer': ('Westlake, Ohio', None),
    'hartsfield': ('Birmingham, Alabama', None),
    'lousma': ('Ann Arbor, Michigan', None),
    'peterson': ('Winona, Mississippi', None),
    'gibson': ('Kenmore, New York', None),
    'kerwin': ('Oak Park, Illinois', None),
}

# Wikidata lists military branches only; these were civilians when chosen.
CIVILIAN = {
    'armstrong': 'civilian NASA test pilot',
    'haise': 'civilian NASA test pilot',
    'schmitt': 'civilian scientist-astronaut (geologist)',
    'allen': 'civilian scientist-astronaut (physicist)',
    'henize': 'civilian scientist-astronaut (astronomer)',
    'gibson': 'civilian scientist-astronaut (solar physicist)',
}

SPARQL = """
SELECT ?item ?birthLabel ?stateLabel ?countryLabel ?branchLabel ?mission ?missionLabel ?launch WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item wdt:P19 ?birth .
             OPTIONAL { ?birth wdt:P131* ?state . ?state wdt:P31 wd:Q35657 . }
             OPTIONAL { ?birth wdt:P17 ?country . } }
  OPTIONAL { ?item wdt:P241 ?branch . }
  OPTIONAL { ?mission wdt:P1029 ?item .
             OPTIONAL { ?mission wdt:P619 ?launch . } }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}"""


def main():
    src = SRC.read_text()
    people = re.findall(r"\n  (\w+): \{.*?wikipedia: '([^']+)'", src, re.S)
    titles = {key: urllib.parse.unquote(url.rsplit('/', 1)[1]) for key, url in people}
    q = urllib.parse.urlencode({'action': 'query', 'prop': 'pageprops', 'ppprop': 'wikibase_item',
                                'titles': '|'.join(titles.values()), 'redirects': 1, 'format': 'json'})
    res = get(f'https://en.wikipedia.org/w/api.php?{q}')['query']
    hops = {n['from']: n['to'] for n in res.get('normalized', []) + res.get('redirects', [])}

    def resolve(t):
        for _ in range(3):  # underscores -> spaces, then any redirect
            t = hops.get(t, t)
        return t

    qid_by_title = {p['title']: p['pageprops']['wikibase_item'] for p in res['pages'].values() if 'pageprops' in p}
    qids = {key: qid_by_title.get(resolve(t)) for key, t in titles.items()}

    query = SPARQL % ' '.join(f'wd:{q}' for q in qids.values() if q)
    url = 'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': query, 'format': 'json'})
    rows = get(url)['results']['bindings']

    val = lambda r, k: r.get(k, {}).get('value')
    by_qid = {}
    for r in rows:
        f = by_qid.setdefault(val(r, 'item').rsplit('/', 1)[1], {'born': None, 'service': [], 'missions': {}})
        birth, state, country = val(r, 'birthLabel'), val(r, 'stateLabel'), val(r, 'countryLabel')
        if birth and not f['born']:
            f['born'] = ', '.join(x for x in (birth, state if country == 'United States of America' or state else country) if x)
        if val(r, 'branchLabel') and val(r, 'branchLabel') not in f['service']:
            f['service'].append(val(r, 'branchLabel'))
        if val(r, 'mission'):
            f['missions'].setdefault(val(r, 'missionLabel'), val(r, 'launch') or '')

    facts = {}
    for key, qid in qids.items():
        f = by_qid.get(qid, {'born': None, 'service': [], 'missions': {}})
        missions = [m for m, _ in sorted(f['missions'].items(), key=lambda kv: kv[1] or '9999')
                    if FLIGHT.match(m) and m not in CANCELLED]
        service = [BRANCH.get(b, b) for b in f['service']] + ([CIVILIAN[key]] if key in CIVILIAN else [])
        town, note = HOMETOWN.get(key, (None, None))
        facts[key] = {'wikidata': qid, 'hometown': town, 'hometownNote': note, 'born': BORN.get(key, f['born']),
                      'service': service, 'missions': missions}
        print(f"{key:12} born: {facts[key]['born']}  | {'; '.join(service)} | {', '.join(missions)}")
    OUT.write_text(json.dumps(facts, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
