#!/usr/bin/env python3
# PROTONSIXTAI v3.1 — Living Proton Mind (filtered memetic births)
# - Word / 3-gram based concept birth
# - Repetition requirement before birth
# - Filters for alphabetic tokens
# - Birth rate limiting & consolidation
# - Archive cap & automatic archival of weakest
# - Lower mutation rate for stabilization
# - Keeps life_pulse + interactive keyboard input
#
# Save as PROTONSIXTAI.py and run: python PROTONSIXTAI.py

import math, random, time
from collections import deque, defaultdict, Counter

random.seed(42)

# ------------------------------
# Token type (simple)
# ------------------------------
class Token:
    def __init__(self, proto_id, color, ascii8, origin):
        self.proto_id = proto_id
        self.color = color
        self.ascii8 = ascii8
        self.origin = origin

# ------------------------------
# Hypercube primitive (simpler model like v3)
# ------------------------------
FACE_LIST = ["+X","-X","+Y","-Y","+Z","-Z"]

class Hypercube:
    def __init__(self, name):
        self.name = name
        self.ports = {f: None for f in FACE_LIST}
        self.queue = deque()
        self.memory = []            # list[(Token, origin_face_or_hint)]
        self.forwarded = 0
        self.rotors = [random.random() for _ in range(96)]
        self.last_face_intensity = [0.0]*6
        # Homeostasis
        self.tension = 0.4
        self.curiosity = 0.5
        self.excited = 0.4

    def attach(self, face, other):
        self.ports[face] = other

    def enqueue(self, token):
        self.queue.append(token)

    def step_rotors(self):
        # small dynamics to keep "alive" behavior
        for i in range(len(self.rotors)):
            self.rotors[i] += random.uniform(-0.01, 0.01)
            if self.rotors[i] < 0: self.rotors[i] += 1
            if self.rotors[i] > 1: self.rotors[i] -= 1
        for f in range(6):
            base = f*16
            rblock = sum(self.rotors[base:base+16])
            # small offset to avoid zero intensities
            self.last_face_intensity[f] = max(0.0, rblock/16.0 + 0.1)

    def process_tokens(self):
        # Move all incoming tokens into memory with an origin hint
        while self.queue:
            t = self.queue.popleft()
            self.memory.append((t, t.origin))
        # simple forwarding: occasionally forward last tokens to random neighbor
        for t,_ in self.memory[-4:]:
            idx = random.randrange(6)
            port = FACE_LIST[idx]
            target = self.ports.get(port)
            if target:
                target.enqueue(t)
                self.forwarded += 1

# ------------------------------
# ProtonMind v3.1
# ------------------------------
class ProtonMind:
    def __init__(self):
        # create cubes (central + 6 + iface)
        self.C = Hypercube("C")
        self.Xp = Hypercube("Xp"); self.Xn = Hypercube("Xn")
        self.Yp = Hypercube("Yp"); self.Yn = Hypercube("Yn")
        self.Zp = Hypercube("Zp"); self.Zn = Hypercube("Zn")
        self.IFACE = Hypercube("IFACE")

        # attach symmetric neighbors (C center)
        self.C.attach("+X", self.Xp); self.Xp.attach("-X", self.C)
        self.C.attach("-X", self.Xn); self.Xn.attach("+X", self.C)
        self.C.attach("+Y", self.Yp); self.Yp.attach("-Y", self.C)
        # note: we attach IFACE to -Y (back-of-mind)
        self.C.attach("-Y", self.IFACE); self.IFACE.attach("+Y", self.C)
        self.C.attach("+Z", self.Zp); self.Zp.attach("-Z", self.C)
        self.C.attach("-Z", self.Zn); self.Zn.attach("+Z", self.C)

        self.all_cubes = [self.C, self.Xp, self.Xn, self.Yp, self.Yn, self.Zp, self.Zn, self.IFACE]

        # memetic structures
        self.active_concepts = {}    # name -> dict {text,color,strength,relevance,assoc,...}
        self.archived_concepts = {}
        self._concept_counter = 0

        # token counter
        self._token_counter = 0

        # life pulse
        self.metabolic_phase = 0.0

        # memetic tuning (adjusted)
        self.mutation_rate = 0.03          # lower mutation
        self.birth_min_repeats = 2         # require repetition
        self.birth_window = 28             # number of recent tokens to consider for frequency
        self.birth_min_word_len = 3        # prefer full words >= 3 chars
        self.max_active_concepts = 200     # cap active memory
        self.archive_threshold = 0.23      # more aggressive archiving
        self.relevance_decay = 0.994

        # consolidation timer
        self._consolidate_counter = 0

    # --------------------------
    # token helpers
    # --------------------------
    def _mk_token(self, ch, origin):
        t = Token(self._token_counter, random.randint(0,0xFFFFFF), ord(ch) % 256, origin)
        self._token_counter += 1
        return t

    def inject_text_to_iface(self, text, origin="USER"):
        # enqueue tokens for each character; also keep words in IFACE.memory
        for ch in text:
            t = self._mk_token(ch, origin)
            self.IFACE.enqueue(t)

    def read_iface_memory(self, n=120):
        s = ""
        for t,_ in self.IFACE.memory[-n:]:
            try:
                s += chr(t.ascii8)
            except:
                s += '?'
        return s

    # --------------------------
    # life pulse (blood flow)
    # --------------------------
    def life_pulse(self):
        self.metabolic_phase += 0.035
        pulse = math.sin(self.metabolic_phase)
        C = self.C
        # modulate homeostasis lightly
        C.tension = max(0.0, min(1.0, C.tension + 0.0015 * pulse))
        C.curiosity = max(0.0, min(1.0, C.curiosity + 0.002 * (0.5 - C.tension)))
        C.excited = max(0.0, min(1.0, C.excited + 0.003 * pulse))
        # small random spike occasionally
        if random.random() < 0.06:
            f = random.randrange(6)
            C.last_face_intensity[f] = min(10.0, C.last_face_intensity[f] + random.uniform(0.08, 0.2))
        # occasional spontaneous low-prob reply
        if random.random() < 0.03:
            self.generate_reply()

    # --------------------------
    # main step
    # --------------------------
    def step(self):
        # rotor & token processing
        for cube in self.all_cubes:
            cube.step_rotors()
            cube.process_tokens()

        # births: attempt one birth per step at most
        born = self.maybe_birth_concept_once()

        # memetic drift, consolidation & archival housekeeping
        self.mutate_concepts()
        self.consolidate_duplicates_if_needed()
        self.degrade_and_archive_if_needed()

    # --------------------------
    # concept-birth utilities
    # --------------------------
    def _extract_recent_strings(self, source_cube, window):
        """
        From a cube's recent memory, extract candidate strings:
        - words (split on whitespace) lowercased if alphabetic and length >= birth_min_word_len
        - and character 3-grams for other sequences
        Returns a list of candidate strings (may contain duplicates).
        """
        recent = source_cube.memory[-window:]
        chars = []
        for t,_ in recent:
            try:
                chars.append(chr(t.ascii8))
            except:
                chars.append('?')
        text = ''.join(chars)
        candidates = []
        # split into words
        words = [w.strip() for w in text.split()]
        for w in words:
            if len(w) >= self.birth_min_word_len and any(ch.isalpha() for ch in w):
                # normalize to lower alpha-only substring
                filtered = ''.join(ch.lower() for ch in w if ch.isalpha())
                if len(filtered) >= self.birth_min_word_len:
                    candidates.append(filtered)
        # also extract char 3-grams as fallback
        if len(text) >= 3:
            for i in range(max(0, len(text)-3)):
                ng = text[i:i+3]
                # filter out whitespace-only ngrams
                if any(ch.isalpha() for ch in ng):
                    ngf = ''.join(ch.lower() for ch in ng if ch.isalpha())
                    if len(ngf) >= 2:
                        candidates.append(ngf)
        return candidates

    def maybe_birth_concept_once(self):
        """
        Try to create at most one new concept per call.
        Look for frequent candidates in IFACE memory first, then in central memory.
        Require candidate count >= birth_min_repeats in the window.
        """
        # Search order: IFACE (external) first, then central
        for src in (self.IFACE, self.C):
            candidates = self._extract_recent_strings(src, self.birth_window)
            if not candidates:
                continue
            counts = Counter(candidates)
            # pick candidate with highest count meeting threshold
            best, best_count = None, 0
            for k,v in counts.items():
                if v >= self.birth_min_repeats and v > best_count:
                    # ignore tokens that are solely punctuation/space
                    if all(not ch.isalpha() for ch in k):
                        continue
                    best, best_count = k, v
            if not best:
                continue
            # check it's not already present (text match)
            if any(c["text"] == best for c in self.active_concepts.values()):
                # reinforce existing one instead of creating duplicate
                for name,c in self.active_concepts.items():
                    if c["text"] == best:
                        c["strength"] = min(5.0, c["strength"] + 0.06)
                        c["relevance"] = min(1.0, c["relevance"] + 0.06)
                        # small assoc bump
                        return None
            # create the concept from the best candidate
            # ensure it's not whitespace-only and contains letters
            if not any(ch.isalpha() for ch in best):
                return None
            cname = f"LEARNED_{self._concept_counter}"
            self._concept_counter += 1
            avg_color = 0
            # attempt to average recent colors if available
            mem = src.memory[-self.birth_window:]
            colors = [t.color for t,_ in mem] if mem else []
            if colors:
                avg_color = sum(colors)//len(colors)
            else:
                avg_color = random.randint(0,0xFFFFFF)
            concept = {
                "text": best,
                "color": int(avg_color) & 0xFFFFFF,
                "strength": 0.6,
                "relevance": 0.5,
                "assoc": {f: self.C.last_face_intensity[i] for i,f in enumerate(FACE_LIST)},
                "created_from": "IFACE" if src is self.IFACE else "CENTRAL",
                "birth_time": time.time()
            }
            self.active_concepts[cname] = concept
            print(f"[ProtonMind] New concept born: {cname}='{best}' (count={best_count}) source={concept['created_from']}")
            # ensure cap
            self._enforce_active_cap()
            return cname
        return None

    # --------------------------
    # memetic mutation & consolidation
    # --------------------------
    def mutate_concepts(self):
        # small, rare mutations
        for cname, c in list(self.active_concepts.items()):
            if random.random() < self.mutation_rate:
                txt = c["text"]
                if len(txt) >= 3 and random.random() < 0.6:
                    # small char substitution inside the text (keep alpha)
                    i = random.randrange(len(txt))
                    ch = chr((ord(txt[i]) + random.choice([-1,1,2,-2])) % 122)
                    if ch.isalpha():
                        c["text"] = txt[:i] + ch + txt[i+1:]
                # color jitter
                c["color"] = int((c["color"] ^ random.randint(0,0x0A0A0A)) & 0xFFFFFF)
                # gentle relevance jitter
                c["relevance"] = max(0.0, min(1.0, c["relevance"] * (0.98 + random.random()*0.04)))
                # slight strength drift
                c["strength"] = max(0.01, min(5.0, c["strength"] * (0.99 + (random.random()-0.5)*0.02)))

    def _enforce_active_cap(self):
        if len(self.active_concepts) <= self.max_active_concepts:
            return
        # archive weakest until under cap
        sorted_items = sorted(self.active_concepts.items(), key=lambda kv: (kv[1]["relevance"], kv[1]["strength"]))
        while len(self.active_concepts) > self.max_active_concepts and sorted_items:
            name, c = sorted_items.pop(0)
            self.archived_concepts[name] = c
            if name in self.active_concepts:
                del self.active_concepts[name]
            print(f"[Archive] Cap enforce: archived {name} ('{c['text']}')")

    def consolidate_duplicates_if_needed(self):
        # occasionally run consolidation
        self._consolidate_counter += 1
        if self._consolidate_counter < 40:
            return
        self._consolidate_counter = 0
        # merge same-text concepts into one
        text_map = {}
        for name, c in list(self.active_concepts.items()):
            t = c["text"]
            if t in text_map:
                # merge into previous
                prev = text_map[t]
                # combine strength & relevance, average color
                prev["strength"] = min(5.0, prev["strength"] + c["strength"]*0.6)
                prev["relevance"] = min(1.0, (prev["relevance"] + c["relevance"])/1.9)
                prev["color"] = int((prev["color"] + c["color"])//2) if prev["color"] and c["color"] else prev["color"] or c["color"]
                # remove duplicate entry
                del self.active_concepts[name]
            else:
                text_map[t] = c

    # --------------------------
    # degrade & archive
    # --------------------------
    def degrade_and_archive_if_needed(self):
        to_archive = []
        for name, c in list(self.active_concepts.items()):
            c["relevance"] *= self.relevance_decay
            # if very stale, archive
            if c["relevance"] < self.archive_threshold and c["strength"] < 0.35:
                to_archive.append((name, c))
        for name, c in to_archive:
            self.archived_concepts[name] = c
            del self.active_concepts[name]
            print(f"[Archive] Concept archived: {name} ('{c['text']}')")

    # --------------------------
    # reply generation
    # --------------------------
    def generate_reply(self):
        # pick highest scoring active concept based on alignment to central face intensities and relevance
        if not self.active_concepts:
            return None
        scores = []
        for name, c in self.active_concepts.items():
            score = c["relevance"] * c["strength"]
            # alignment boost: dot product between assoc and current face intensities
            align = 0.0
            for i, f in enumerate(FACE_LIST):
                align += c.get("assoc", {}).get(f, 0.0) * self.C.last_face_intensity[i]
            score *= (1.0 + 0.6 * align)
            scores.append((score, name))
        scores.sort(reverse=True)
        best_score, best_name = scores[0]
        if best_score <= 0.05:
            return None
        # emit text
        concept = self.active_concepts[best_name]
        text = concept["text"]
        color = concept["color"] or random.randint(0,0xFFFFFF)
        # reinforce
        concept["strength"] = min(5.0, concept["strength"] + 0.03)
        concept["relevance"] = min(1.0, concept["relevance"] + 0.04)
        # enqueue tokens into IFACE (char by char)
        for ch in text:
            t = Token(self._token_counter, color, ord(ch) % 256, "CORE")
            self._token_counter += 1
            self.IFACE.enqueue(t)
        return best_name

    # --------------------------
    # step wrapper with life pulse convenience
    # --------------------------
    def tick(self):
        # run life pulse, then step, then try to reply (spontaneously)
        self.life_pulse()
        self.step()
        # occasionally produce reply
        if random.random() < 0.12:
            self.generate_reply()

# ------------------------------
# Interactive CLI (same style as v3)
# ------------------------------
def main():
    pm = ProtonMind()
    print("ProtonSixTAI v3.1 — Alive & learning (word-based births).")
    print("Type messages (ENTER). Type 'exit' to quit.\n")
    try:
        while True:
            user = input("YOU: ")
            if user.strip().lower() in ("exit","quit"):
                break
            # inject
            pm.inject_text_to_iface(user, origin="USER")
            # let it run for a little while after input
            for _ in range(20):
                pm.tick()
            # show a brief readout
            recent = pm.read_iface_memory(200)
            print("MIND:", recent[-200:])
            print(f"Active concepts: {len(pm.active_concepts)}  Archived: {len(pm.archived_concepts)}")
    except KeyboardInterrupt:
        print("\nInterrupted — exiting.")

if __name__ == "__main__":
    main()
