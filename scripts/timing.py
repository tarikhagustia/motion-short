"""Word timing lookups for scene generators.

    from timing import Timing
    T = Timing("path/to/project")        # reads timeline.json
    T.at("s03", "vato")                  # seconds from scene s03's start when "vato" is spoken
    T.at("s03", "vato", -0.2)            # nudge (anticipate by 0.2 s)
    T.end("s03", "vato")                 # when the word ends (scene-relative)
    T.dur("s03")                         # scene length in seconds

Matching is case-insensitive, ignores punctuation and matches prefixes ("barito" finds "Barito,").
A missing word falls back to 0.3 s and prints a warning, so a typo never breaks the build.
"""
import json
import re
import sys
from pathlib import Path


def _n(w):
    return re.sub(r"[^\w±%]", "", w.lower())


class Timing:
    def __init__(self, project):
        p = Path(project) / "timeline.json"
        self.ok = p.exists()
        self.tl = json.loads(p.read_text(encoding="utf-8")) if self.ok else {"scenes": [], "words": []}
        self.idx = {s["id"]: i for i, s in enumerate(self.tl["scenes"])}

    def _word(self, sid, word, nth=0):
        si = self.idx.get(sid)
        if si is None:
            return None
        want = _n(word)
        hits = [w for w in self.tl["words"] if w["scene"] == si and _n(w["text"]).startswith(want)]
        return hits[nth] if len(hits) > nth else None

    def at(self, sid, word, offset=0.0, nth=0):
        w = self._word(sid, word, nth)
        if not w:
            print(f"[timing] '{word}' not found in {sid}; using 0.3 s", file=sys.stderr)
            return round(0.3 + offset, 2)
        s0 = self.tl["scenes"][self.idx[sid]]["start"]
        return round(max(w["start"] - s0 + offset, 0), 2)

    def end(self, sid, word, offset=0.0, nth=0):
        w = self._word(sid, word, nth)
        if not w:
            return round(1.0 + offset, 2)
        s0 = self.tl["scenes"][self.idx[sid]]["start"]
        return round(max(w["end"] - s0 + offset, 0), 2)

    def dur(self, sid):
        si = self.idx.get(sid)
        if si is None:
            return 4.0
        s = self.tl["scenes"][si]
        return round(s["end"] - s["start"], 2)
