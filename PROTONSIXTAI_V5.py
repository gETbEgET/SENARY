#!/usr/bin/env python3
# PROTONSIXTAI v5.0 — Living Proton Mind with 144 Moebius Pathways
# - Extended from v4.0: 144 dynamic Moebius pathways for token propagation
# - Pathways: Loops with "twist" (orientation flip), all intersecting in central C
# - Token "sees" modifications: Logs transformations from operations/functions applied along path
# - Influences concept birth/mutations based on observed effects
# - Visualization: Draws Moebius-like paths in Pygame
#
# Save as PROTONSIXTAI_v5.py and run: python PROTONSIXTAI_v5.py
import math, random, time
import pygame
import numpy as np
import matplotlib.pyplot as plt
from collections import deque, defaultdict, Counter
from scipy.special import jn  # For Bessel functions in cymatics
random.seed(42)
pygame.init()

# ------------------------------
# Constants
# ------------------------------
FACE_LIST = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PROTONSIXTAI v5.0 - Proton with Moebius Pathways")

NUM_MOEBIUS_PATHS = 144  # Exact 144 pathways

# ------------------------------
# Token type (extended with transformation log)
# ------------------------------
class Token:
    def __init__(self, proto_id, color, ascii8, origin):
        self.proto_id = proto_id
        self.color = color
        self.ascii8 = ascii8
        self.origin = origin
        self.transform_log = []  # List of (operation, before, after) to "see" modifications

# ------------------------------
# Hypercube (extended with pathways support)
# ------------------------------
class Hypercube:
    def __init__(self, name):
        self.name = name
        self.ports = {f: None for f in FACE_LIST}
        self.queue = deque()
        self.memory = []
        self.forwarded = 0
        self.rotors = [random.random() for _ in range(96)]
        self.last_face_intensity = [0.0] * 6
        self.tension = 0.4
        self.curiosity = 0.5
        self.excited = 0.4
        self.spin_x = random.uniform(-1.0, 1.0)
        self.spin_y = random.uniform(-1.0, 1.0)
        self.spin_z = random.uniform(-1.0, 1.0)
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.angle_z = 0.0
        self.grip_locks = {f: False for f in FACE_LIST}
        self.cymatics_pattern = None
        # NEW: Local pathways passing through this cube
        self.local_paths = []

    # ... (attach, detach, enqueue, step_rotors, process_tokens, update_grip_lock, compute_patterns, generate_cymatics, visualize methods unchanged from v4.0)

    def apply_operation(self, token, op_type):
        # Apply a function/operation and log the change
        before_color = token.color
        before_ascii = token.ascii8
        if op_type == "color_jitter":
            token.color = int((token.color ^ random.randint(0, 0x0A0A0A)) & 0xFFFFFF)
        elif op_type == "ascii_shift":
            token.ascii8 = (token.ascii8 + random.randint(-5, 5)) % 256
        elif op_type == "intensity_mod":
            # Mod based on face intensity
            token.color = int(token.color * (1 + random.choice(self.last_face_intensity)))
        after_color = token.color
        after_ascii = token.ascii8
        token.transform_log.append((op_type, (before_color, before_ascii), (after_color, after_ascii)))

# ------------------------------
# ProtonMind v5.0
# ------------------------------
class ProtonMind:
    def __init__(self):
        # Hypercubes setup (unchanged)
        self.C = Hypercube("C")
        self.Xp = Hypercube("Xp"); self.Xn = Hypercube("Xn")
        self.Yp = Hypercube("Yp"); self.Yn = Hypercube("Yn")
        self.Zp = Hypercube("Zp"); self.Zn = Hypercube("Zn")
        self.IFACE = Hypercube("IFACE")
        # Attachments (unchanged)
        self.C.attach("+X", self.Xp); self.Xp.attach("-X", self.C)
        self.C.attach("-X", self.Xn); self.Xn.attach("+X", self.C)
        self.C.attach("+Y", self.Yp); self.Yp.attach("-Y", self.C)
        self.C.attach("-Y", self.IFACE); self.IFACE.attach("+Y", self.C)
        self.C.attach("+Z", self.Zp); self.Zp.attach("-Z", self.C)
        self.C.attach("-Z", self.Zn); self.Zn.attach("+Z", self.C)
        self.all_cubes = [self.C, self.Xp, self.Xn, self.Yp, self.Yn, self.Zp, self.Zn, self.IFACE]
        self.cube_positions = {
            "C": (400, 300), "Xp": (500, 300), "Xn": (300, 300),
            "Yp": (400, 200), "Yn": (400, 400), "Zp": (500, 200), "Zn": (300, 400),
            "IFACE": (400, 500)
        }
        # NEW: Generate 144 Moebius pathways
        self.moebius_pathways = self.generate_moebius_pathways()
        # Assign local paths to cubes
        for path_id, path in self.moebius_pathways.items():
            for cube in path['sequence']:
                cube.local_paths.append(path_id)
        # Rest (memetic, etc.) unchanged
        self.active_concepts = {}
        self.archived_concepts = {}
        self._concept_counter = 0
        self._token_counter = 0
        self.metabolic_phase = 0.0
        self.mutation_rate = 0.03
        self.birth_min_repeats = 2
        self.birth_window = 28
        self.birth_min_word_len = 3
        self.max_active_concepts = 200
        self.archive_threshold = 0.23
        self.relevance_decay = 0.994
        self._consolidate_counter = 0

    def generate_moebius_pathways(self):
        # Generate 144 unique Moebius-like pathways: loops with twist, all intersecting C
        pathways = {}
        cubes = self.all_cubes[1:]  # Exclude C for starting points
        for i in range(NUM_MOEBIUS_PATHS):
            # Random sequence: start from random cube, go through 3-5 cubes, always include C in middle, loop back with twist
            start = random.choice(cubes)
            seq = [start]
            for _ in range(random.randint(2, 4)):
                next_cube = random.choice(list(start.ports.values())) if start.ports else random.choice(cubes)
                seq.append(next_cube)
                start = next_cube
            # Insert C in middle (intersection)
            mid = len(seq) // 2
            seq.insert(mid, self.C)
            # Loop back to start
            seq.append(seq[0])
            # Simulate Moebius twist: At mid-point, flip orientation (reverse a face direction)
            twist_point = mid
            twist = random.choice(FACE_LIST)  # Face to flip
            pathways[i] = {
                'sequence': seq,
                'twist_point': twist_point,
                'twist_face': twist,
                'operations': random.sample(["color_jitter", "ascii_shift", "intensity_mod"], k=3)  # Functions along path
            }
        return pathways

    def propagate_token_via_path(self, token, path_id):
        # Propagate token through a Moebius pathway, applying operations and logging
        path = self.moebius_pathways[path_id]
        current = path['sequence'][0]
        for idx, cube in enumerate(path['sequence']):
            current.enqueue(token)
            # Apply operation if any
            if idx < len(path['operations']):
                op = path['operations'][idx]
                cube.apply_operation(token, op)
            # Twist at point: Flip token orientation (e.g., invert color)
            if idx == path['twist_point']:
                token.color = 0xFFFFFF - token.color  # Simple inversion for Moebius twist
                token.transform_log.append(("moebius_twist", token.color, 0xFFFFFF - token.color))
            current = cube
        # At end (back to start), if intersects C, evaluate log for effects
        if self.C in path['sequence']:
            self.evaluate_token_effects(token)

    def evaluate_token_effects(self, token):
        # Token "sees" its modifications: Use log to influence system (e.g., boost mutation if many changes)
        num_changes = len(token.transform_log)
        if num_changes > 2:
            self.mutation_rate += 0.01 * num_changes  # Temporary boost
            print(f"[Effect] Token {token.proto_id} saw {num_changes} modifications - boosting mutation rate")

    # Token helpers (updated)
    def _mk_token(self, ch, origin):
        t = Token(self._token_counter, random.randint(0, 0xFFFFFF), ord(ch) % 256, origin)
        self._token_counter += 1
        return t

    def inject_text_to_iface(self, text, origin="USER"):
        for ch in text:
            t = self._mk_token(ch, origin)
            # NEW: Propagate via random Moebius path instead of direct enqueue
            path_id = random.randint(0, NUM_MOEBIUS_PATHS - 1)
            self.propagate_token_via_path(t, path_id)
        # Cymatics (unchanged)
        freq = len(text) * 10 + 440
        for cube in self.all_cubes:
            cube.generate_cymatics(freq)

    # ... (restul: read_iface_memory, life_pulse, step, maybe_birth_concept_once, etc. unchanged)
    # In step: Add pathway influence to grip locks
    def step(self):
        for cube in self.all_cubes:
            cube.step_rotors()
            cube.process_tokens()
            for face in FACE_LIST:
                cube.update_grip_lock(face)
            cube.compute_patterns()
            # NEW: If active paths, force grip lock temporarily
            if cube.local_paths:
                random_path = random.choice(cube.local_paths)
                if random.random() < 0.1:
                    face = self.moebius_pathways[random_path]['twist_face']
                    cube.grip_locks[face] = True
        # Rest unchanged

    def visualize_proton(self):
        screen.fill((0, 0, 0))
        for name, pos in self.cube_positions.items():
            cube = [c for c in self.all_cubes if c.name == name][0]
            cube.visualize(pos)
            font = pygame.font.SysFont(None, 24)
            text = font.render(name, True, (255, 255, 255))
            screen.blit(text, (pos[0] - 20, pos[1] - 30))
        # NEW: Draw Moebius pathways as curved lines
        for path_id, path in self.moebius_pathways.items():
            if random.random() < 0.05:  # Draw subset for performance
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                prev_pos = self.cube_positions[path['sequence'][0].name]
                for cube in path['sequence'][1:]:
                    pos = self.cube_positions[cube.name]
                    # Curved line for Moebius feel
                    mid_x = (prev_pos[0] + pos[0]) / 2 + random.uniform(-20, 20)
                    mid_y = (prev_pos[1] + pos[1]) / 2 + random.uniform(-20, 20)
                    pygame.draw.line(screen, color, prev_pos, (mid_x, mid_y), 1)
                    pygame.draw.line(screen, color, (mid_x, mid_y), pos, 1)
                    prev_pos = pos
        pygame.display.flip()

    # tick (unchanged, with viz)

# ------------------------------
# Interactive CLI (unchanged)
# ------------------------------
def main():
    pm = ProtonMind()
    print("PROTONSIXTAI v5.0 — Proton with 144 Moebius Pathways.")
    print("Type messages (ENTER). Type 'exit' to quit.\n")
    clock = pygame.time.Clock()
    try:
        while True:
            user = input("YOU: ")
            if user.strip().lower() in ("exit", "quit"):
                break
            pm.inject_text_to_iface(user, origin="USER")
            for _ in range(20):
                pm.tick()
                clock.tick(60)
            recent = pm.read_iface_memory(200)
            print("MIND:", recent[-200:])
            print(f"Active concepts: {len(pm.active_concepts)} Archived: {len(pm.archived_concepts)}")
            ratios, complexity = pm.C.compute_patterns()
            print(f"Central Patterns: Ratios {ratios}, Complexity {complexity:.2f}")
    except KeyboardInterrupt:
        print("\nInterrupted — exiting.")
    pygame.quit()

if __name__ == "__main__":
    main()