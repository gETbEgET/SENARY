#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIXTAI 4x4x6 — CSL v5.0: 8161-Cube Super Dyson-Sphere (Python Edition)
Author: AB JUDE (concept) + assistant (port/extension)

Run:
  python SIXTAI_SHA256.PY           # CLI only
  python SIXTAI_SHA256.PY --plot    # with live energy chart (requires matplotlib)
"""
import json, math, os, sys, argparse
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import hashlib 

try:
    import numpy as np
except Exception as e:
    raise SystemExit("This script needs numpy. Install with: pip install numpy")

HAS_MPL = False
if "--plot" in sys.argv:
    try:
        import matplotlib.pyplot as plt
        HAS_MPL = HAS_MPL 
    except Exception:
        HAS_MPL = False

# ---------------- Core Primitive ----------------
class CubeAI:
    R, Y, G, B, V, O = 0, 1, 2, 3, 4, 5
    FACES = 6
    ROT = 16
    dt = 0.02
    PAIRS = [] 

    def __init__(self, cube_id: int, k: float, c: float):
        self.id = cube_id
        self.k = float(k)
        self.c = float(c)
        if not CubeAI.PAIRS:
            CubeAI.PAIRS = [(i, i + CubeAI.ROT//2) for i in range(CubeAI.ROT//2)] + \
                           [(i, i+1) for i in range(CubeAI.ROT - 1)]
        self.theta = np.random.rand(self.FACES, self.ROT) * 2.0 * math.pi
        self.omega = np.zeros((self.FACES, self.ROT), dtype=float)

    def step(self, drives: Optional[np.ndarray] = None):
        tau = np.zeros_like(self.omega)
        for f in range(self.FACES):
            th = self.theta[f]
            for a,b in CubeAI.PAIRS:
                t_ab = self.k * math.sin(th[b] - th[a])
                tau[f, a] += t_ab
                tau[f, b] += self.k * math.sin(th[a] - th[b])
        if drives is None:
            drives = 0.0
        self.omega += self.dt * (tau - self.c * self.omega + drives)
        np.clip(self.omega, -2.55, 2.55, out=self.omega)
        self.theta = (self.theta + self.dt * self.omega) % (2.0 * math.pi)

    def totalEnergy(self) -> float:
        eKin = 0.5 * np.sum(self.omega * self.omega)
        ePot = 0.0
        for f in range(self.FACES):
            th = self.theta[f]
            for a,b in CubeAI.PAIRS:
                ePot += 0.5 * self.k * (1.0 - math.cos(th[a] - th[b]))
        return float(eKin + ePot)

    def face_signal(self, f: int, r: int) -> float:
        return float(self.omega[f, r])


# --------------- 13-Core Network ---------------
@dataclass
class Sixtai13:
    CENTRAL_K: float = 0.800
    CENTRAL_C: float = 0.040
    ADJ_K: float = 0.700
    ADJ_C: float = 0.040
    T2_K: float = 0.600
    T2_C: float = 0.050

    PULSE_LEN: int = 5
    MIX: float = 0.05
    FB: float = 0.005

    target_J: float = 22.0

    central: CubeAI = field(init=False)
    tier1: List[CubeAI] = field(init=False)
    tier2: List[CubeAI] = field(init=False)

    def __post_init__(self):
        self.central = CubeAI(0, self.CENTRAL_K, self.CENTRAL_C)
        self.tier1 = [CubeAI(i+1, self.ADJ_K, self.ADJ_C) for i in range(6)]
        self.tier2 = [CubeAI(i+7, self.T2_K, self.T2_C) for i in range(6)]

        self.PROC_MAP = {
            CubeAI.R: self.tier1[0],
            CubeAI.Y: self.tier1[1],
            CubeAI.G: self.tier1[2],
            CubeAI.B: self.tier1[3],
            CubeAI.V: self.tier1[4],
            CubeAI.O: self.tier1[5],
        }

        self.SYNAPTIC_BRIDGES = [
            dict(centralOut=CubeAI.R, adjIn=CubeAI.Y, processor=self.PROC_MAP[CubeAI.R]),
            dict(centralOut=CubeAI.Y, adjIn=CubeAI.R, processor=self.PROC_MAP[CubeAI.Y]),
            dict(centralOut=CubeAI.G, adjIn=CubeAI.B, processor=self.PROC_MAP[CubeAI.G]),
            dict(centralOut=CubeAI.B, adjIn=CubeAI.G, processor=self.PROC_MAP[CubeAI.B]),
            dict(centralOut=CubeAI.V, adjIn=CubeAI.O, processor=self.PROC_MAP[CubeAI.V]),
            dict(centralOut=CubeAI.O, adjIn=CubeAI.V, processor=self.PROC_MAP[CubeAI.O]),
        ]

        self.T1_T2 = [
            dict(t1=0, t2=0, t1Out=CubeAI.R, t2In=CubeAI.Y, t2Out=CubeAI.Y, t1In=CubeAI.O),
            dict(t1=1, t2=1, t1Out=CubeAI.R, t2In=CubeAI.Y, t2Out=CubeAI.Y, t1In=CubeAI.O),
            dict(t1=2, t2=2, t1Out=CubeAI.R, t2In=CubeAI.Y, t2Out=CubeAI.Y, t1In=CubeAI.O),
            dict(t1=3, t2=3, t1Out=CubeAI.R, t2In=CubeAI.Y, t2Out=CubeAI.Y, t1In=CubeAI.O),
            dict(t1=4, t2=4, t1Out=CubeAI.R, t2In=CubeAI.Y, t2Out=CubeAI.Y, t1In=CubeAI.O),
            dict(t1=5, t2=5, t1Out=CubeAI.R, t2In=CubeAI.Y, t2Out=CubeAI.Y, t1In=CubeAI.O),
        ]

    def step_central(self, drive_map: Optional[np.ndarray]) -> float:
        base = np.full((CubeAI.FACES, CubeAI.ROT), 0.005, dtype=float)
        self.central.step(drive_map if drive_map is not None else base)
        return self.central.totalEnergy()

    def step_central_tier1(self) -> float:
        total = 0.0
        for b in self.SYNAPTIC_BRIDGES:
            s = sum(self.central.face_signal(b['centralOut'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT
            drv = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
            drv[b['adjIn'], :] = s * self.MIX
            for _ in range(self.PULSE_LEN):
                b['processor'].step(drv)
            fb = sum(b['processor'].face_signal(b['adjIn'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT
            back = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
            back[b['centralOut'], :] = fb * self.FB
            self.central.step(back)
            total += b['processor'].totalEnergy()
        return total

    def step_tier1_tier2(self) -> float:
        total = 0.0
        for b in self.T1_T2:
            T1 = self.tier1[b['t1']]
            T2 = self.tier2[b['t2']]
            s = sum(T1.face_signal(b['t1Out'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT
            drv = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
            drv[b['t2In'], :] = s * self.MIX
            for _ in range(self.PULSE_LEN):
                T2.step(drv)
            fb = sum(T2.face_signal(b['t2Out'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT
            back = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
            back[b['t1In'], :] = fb * self.FB
            T1.step(back)
            total += T2.totalEnergy()
        return total

    def network_step(self, drive_map: Optional[np.ndarray]) -> Dict[str, float]:
        total = 0.0
        total += self.step_central(drive_map)
        total += self.step_central_tier1()
        total += self.step_tier1_tier2()
        return dict(k=self.central.k, c=self.central.c, J=total, thoughtEnergy=total/13.0)

    def total_energy(self) -> float:
        J = self.central.totalEnergy()
        for c in self.tier1: J += c.totalEnergy()
        for c in self.tier2: J += c.totalEnergy()
        return J

# --------------- Shell Modules (12 × 7) ---------------
@dataclass
class ShellModule:
    center: CubeAI
    arms: List[CubeAI]

AXIS_PLUS_X, AXIS_MINUS_X, AXIS_PLUS_Y, AXIS_MINUS_Y, AXIS_PLUS_Z, AXIS_MINUS_Z = range(6)

def classify_axis(direction: Tuple[int,int,int]) -> int:
    x, y, z = direction
    if abs(x) > 0.1:
        return AXIS_PLUS_X if x > 0 else AXIS_MINUS_X
    if abs(y) > 0.1:
        return AXIS_PLUS_Y if y > 0 else AXIS_MINUS_Y
    return AXIS_PLUS_Z if z > 0 else AXIS_MINUS_Z

# --------------- TIER 1: 97-Cube Dyson Shell ---------------
@dataclass
class DysonShell97(Sixtai13):
    SHELL_K: float = 0.55
    SHELL_C: float = 0.06
    SHELL_ARM_K: float = 0.50
    SHELL_ARM_C: float = 0.07
    shell_id: int = 0 # Added for distinction in complex network

    shell_enabled: bool = True

    shell_modules: List[ShellModule] = field(init=False)
    axis_to_modules: Dict[int, List[int]] = field(init=False)

    def __post_init__(self):
        super().__post_init__()
        dirs = []
        base = [(-1,-1,0),(-1,1,0),(1,-1,0),(1,1,0)]
        for s1,s2,_ in base:
            dirs += [(s1,s2,0),(s1,0,s2),(0,s1,s2)]
        uniq = []
        for d in dirs:
            v = np.array(d, dtype=float); v = v/np.linalg.norm(v)
            t = tuple(np.round(v,6))
            if t not in uniq: uniq.append(t)
        dirs = uniq

        self.shell_modules = []
        self.axis_to_modules = {i: [] for i in range(6)}
        base_id = 1000 + self.shell_id * 100 # keep IDs distinct
        for i, d in enumerate(dirs):
            center = CubeAI(base_id+i*7, self.SHELL_K, self.SHELL_C)
            arms = [CubeAI(base_id+i*7+1+j, self.SHELL_ARM_K, self.SHELL_ARM_C) for j in range(6)]
            self.shell_modules.append(ShellModule(center=center, arms=arms))
            ax = classify_axis(d)
            self.axis_to_modules[ax].append(i)

    def step_shell(self) -> float:
        if not self.shell_enabled:
            return 0.0
        total = 0.0
        center_out_faces = [CubeAI.R, CubeAI.Y, CubeAI.G, CubeAI.B, CubeAI.V, CubeAI.O]
        arm_in_faces    = [CubeAI.Y, CubeAI.R, CubeAI.B, CubeAI.G, CubeAI.O, CubeAI.V]

        for axis_idx in range(6):
            T2 = self.tier2[axis_idx]
            modules = self.axis_to_modules[axis_idx]
            t2_sig = sum(T2.face_signal(CubeAI.R, r) for r in range(CubeAI.ROT)) / CubeAI.ROT
            for m_idx in modules:
                mod = self.shell_modules[m_idx]
                drv = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
                drv[CubeAI.Y, :] = t2_sig * (self.MIX * 0.8)
                for _ in range(self.PULSE_LEN):
                    mod.center.step(drv)
                fb = sum(mod.center.face_signal(CubeAI.Y, r) for r in range(CubeAI.ROT)) / CubeAI.ROT
                back = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
                back[CubeAI.O, :] = fb * (self.FB * 0.6)
                T2.step(back)

                csum = [sum(mod.center.face_signal(f, r) for r in range(CubeAI.ROT))/CubeAI.ROT for f in center_out_faces]
                for arm_i, arm in enumerate(mod.arms):
                    drv2 = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
                    drv2[arm_in_faces[arm_i % 6], :] = csum[arm_i % 6] * (self.MIX * 0.6)
                    for _ in range(max(1, self.PULSE_LEN//2)):
                        arm.step(drv2)
                    fb2 = sum(arm.face_signal(arm_in_faces[arm_i % 6], r) for r in range(CubeAI.ROT))/CubeAI.ROT
                    back2 = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
                    back2[center_out_faces[arm_i % 6], :] = fb2 * (self.FB * 0.4)
                    mod.center.step(back2)

                total += mod.center.totalEnergy()
                for arm in mod.arms:
                    total += arm.totalEnergy()
        return total

    def network_step(self, drive_map: Optional[np.ndarray]) -> Dict[str, float]:
        total = 0.0
        total += self.step_central(drive_map)
        total += self.step_central_tier1()
        total += self.step_tier1_tier2()
        total += self.step_shell()
        return dict(k=self.central.k, c=self.central.c, J=total, thoughtEnergy=total/97.0)

    def total_energy(self) -> float:
        J = super().total_energy()
        if self.shell_enabled:
            for m in self.shell_modules:
                J += m.center.totalEnergy()
                for a in m.arms: J += a.totalEnergy()
        return J
        
# --------------- TIER 2: Dyson Core 7 (7 Shells + 1 Relay = 680 Cubes) ---------------
@dataclass
class DysonCore7:
    CORE_COUPLING: float = 0.005
    PULSE_LEN: int = 5
    MIX: float = 0.05
    FB: float = 0.005
    core_id: int = 0
    
    central_shell: DysonShell97 = field(init=False)
    adjacent_shells: List[DysonShell97] = field(init=False)
    synaptic_relay: CubeAI = field(init=False)
    
    shells: List[DysonShell97] = field(init=False)
    total_cube_count: int = field(init=False)

    def __post_init__(self):
        self.central_shell = DysonShell97(shell_id=self.core_id * 1000 + 0)
        self.adjacent_shells = [DysonShell97(shell_id=self.core_id * 1000 + i) for i in range(1, 7)]
        self.shells = [self.central_shell] + self.adjacent_shells
        self.synaptic_relay = CubeAI(cube_id=self.core_id * 1000 + 100, k=0.9, c=0.01) 
        self.total_cube_count = 679 + 1 # 7 * 97 + 1 Relay = 680 Cubes Total

        self.CORE_BRIDGES = [
            # Map 6 faces of central shell to 6 adjacent shells
            dict(c_out=CubeAI.R, a_in=CubeAI.R, adjacent_shell=self.adjacent_shells[0], relay_face=CubeAI.R), 
            dict(c_out=CubeAI.Y, a_in=CubeAI.Y, adjacent_shell=self.adjacent_shells[1], relay_face=CubeAI.Y), 
            dict(c_out=CubeAI.G, a_in=CubeAI.G, adjacent_shell=self.adjacent_shells[2], relay_face=CubeAI.G), 
            dict(c_out=CubeAI.B, a_in=CubeAI.B, adjacent_shell=self.adjacent_shells[3], relay_face=CubeAI.B), 
            dict(c_out=CubeAI.V, a_in=CubeAI.V, adjacent_shell=self.adjacent_shells[4], relay_face=CubeAI.V), 
            dict(c_out=CubeAI.O, a_in=CubeAI.O, adjacent_shell=self.adjacent_shells[5], relay_face=CubeAI.O), 
        ]

    def step_meta_network(self) -> float:
        total_energy = 0.0
        CS = self.central_shell.central
        
        # 1. FUNNEL: Central Shell Output to Relay Cube
        relay_drive = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
        
        for bridge in self.CORE_BRIDGES:
            # Aggregate Central Shell's output to the Relay Cube's corresponding face
            s_out = sum(CS.face_signal(bridge['c_out'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT
            relay_drive[bridge['relay_face'], :] += s_out * self.CORE_COUPLING * self.MIX
            
        # STEP 1: Process Signal through the Synaptic Relay
        for _ in range(self.PULSE_LEN):
            self.synaptic_relay.step(relay_drive)
            
        
        # 2. BROADCAST: Relay Cube Output to Adjacent Shells
        for bridge in self.CORE_BRIDGES:
            AS = bridge['adjacent_shell'].central
            
            # Use the Relay Cube's output from the corresponding face
            relay_signal = sum(self.synaptic_relay.face_signal(bridge['relay_face'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT

            # Drive Adjacent Shell with Relay Signal
            drv = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
            drv[bridge['a_in'], :] = relay_signal * self.MIX
            for _ in range(self.PULSE_LEN): AS.step(drv)
                
            # 3. Adjacent Shell Feedback (simplified: back to Central Shell)
            s_fb = sum(AS.face_signal(bridge['a_in'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT
            back = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
            back[bridge['c_out'], :] = s_fb * self.FB * self.CORE_COUPLING
            CS.step(back)
            
            total_energy += AS.totalEnergy()
            
        total_energy += self.synaptic_relay.totalEnergy()
        return total_energy

    def network_step(self, drive_map: Optional[np.ndarray]) -> Dict[str, float]:
        central_state = self.central_shell.network_step(drive_map)
        total_J = central_state["J"]
        for adj_shell in self.adjacent_shells:
            adj_state = adj_shell.network_step(None) 
            total_J += adj_state["J"]
        total_J += self.step_meta_network()
        
        return dict(
            k=self.central_shell.central.k,
            c=self.central_shell.central.c,
            J=total_J,
            thoughtEnergy=total_J / 680
        )
        
    def total_energy(self) -> float:
        J = 0.0
        for shell in self.shells: J += shell.total_energy()
        J += self.synaptic_relay.totalEnergy() 
        return J
        
    @property
    def central(self): return self.central_shell.central
    @property
    def target_J(self): return self.central_shell.target_J
    @target_J.setter
    def target_J(self, value): self.central_shell.target_J = value

# --------------- TIER 3: Super Dyson Sphere 84 (12 Cores + 1 Central Core + 1 Supreme Relay = 8161 Cubes) ---------------
@dataclass
class DysonSuperSphere84:
    SUPREME_COUPLING: float = 0.0005
    PULSE_LEN: int = 3
    MIX: float = 0.02
    FB: float = 0.001
    
    central_core: DysonCore7 = field(init=False)
    adjacent_cores: List[DysonCore7] = field(init=False)
    supreme_relay: CubeAI = field(init=False)
    
    TOTAL_CUBES: int = field(init=False)

    def __post_init__(self):
        self.central_core = DysonCore7(core_id=1)
        # We need 11 adjacent cores for a total of 12 cores (1+11)
        self.adjacent_cores = [DysonCore7(core_id=i+2) for i in range(11)] 
        self.supreme_relay = CubeAI(cube_id=10000, k=0.95, c=0.005) 
        
        # 12 cores * 680 cubes/core + 1 supreme relay = 8161 Cubes!
        self.TOTAL_CUBES = 8161
        
        self.SUPREME_BRIDGES = []
        faces = [CubeAI.R, CubeAI.Y, CubeAI.G, CubeAI.B, CubeAI.V, CubeAI.O]
        
        adjacent_core_index = 0
        for face in faces:
            # Connect the central core's central shell to the adjacent cores.
            if adjacent_core_index < 11:
                 self.SUPREME_BRIDGES.append(dict(c_out=face, a_in=face, adjacent_core=self.adjacent_cores[adjacent_core_index], relay_face=face))
                 adjacent_core_index += 1
            if adjacent_core_index < 11:
                 self.SUPREME_BRIDGES.append(dict(c_out=face, a_in=face, adjacent_core=self.adjacent_cores[adjacent_core_index], relay_face=(face+1)%6)) # Use a different relay face
                 adjacent_core_index += 1

    def step_super_network(self) -> float:
        total_energy = 0.0
        CCS = self.central_core.central_shell.central 
        
        # 1. FUNNEL: Central Core Output to SUPREME Relay Cube
        relay_drive = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
        
        for bridge in self.SUPREME_BRIDGES:
            s_out = sum(CCS.face_signal(bridge['c_out'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT
            relay_drive[bridge['relay_face'], :] += s_out * self.SUPREME_COUPLING * self.MIX
            
        # STEP 1: Process Signal through the SUPREME Synaptic Relay
        for _ in range(self.PULSE_LEN):
            self.supreme_relay.step(relay_drive)
            
        
        # 2. BROADCAST: SUPREME Relay Output to Adjacent Cores
        for bridge in self.SUPREME_BRIDGES:
            ACS = bridge['adjacent_core'].central_shell.central
            
            relay_signal = sum(self.supreme_relay.face_signal(bridge['relay_face'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT

            drv = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
            drv[bridge['a_in'], :] = relay_signal * self.MIX
            for _ in range(self.PULSE_LEN): ACS.step(drv)
                
            # 3. Adjacent Core Feedback 
            s_fb = sum(ACS.face_signal(bridge['a_in'], r) for r in range(CubeAI.ROT)) / CubeAI.ROT
            back = np.zeros((CubeAI.FACES, CubeAI.ROT), dtype=float)
            back[bridge['c_out'], :] = s_fb * self.FB * self.SUPREME_COUPLING
            CCS.step(back)
            
            total_energy += ACS.totalEnergy()
            
        total_energy += self.supreme_relay.totalEnergy()
        return total_energy

    def network_step(self, drive_map: Optional[np.ndarray]) -> Dict[str, float]:
        core_state = self.central_core.network_step(drive_map)
        total_J = core_state["J"]
        
        for core in self.adjacent_cores:
            core_state = core.network_step(None) 
            total_J += core_state["J"]
            
        total_J += self.step_super_network()
        
        return dict(
            k=self.central_core.central.k,
            c=self.central_core.central.c,
            J=total_J,
            thoughtEnergy=total_J / self.TOTAL_CUBES
        )
        
    def total_energy(self) -> float:
        J = self.central_core.total_energy()
        for core in self.adjacent_cores: J += core.total_energy()
        J += self.supreme_relay.totalEnergy() 
        return J
    
    @property
    def central(self): return self.central_core.central
    @property
    def target_J(self): return self.central_core.target_J
    @target_J.setter
    def target_J(self, value): self.central_core.target_J = value


# --------------- Lexicon / Trainer & CLI ---------------
DEFAULT_LEXICON = {
    "INHALE": dict(k=+0.00, c=-0.010, hz=+0.2),
    "EXHALE": dict(k=+0.00, c=+0.010, hz=-0.2),
    "RELAX":  dict(k=-0.02, c=+0.015, hz=-0.4),
    "CALM":   dict(k=-0.01, c=+0.020, hz=-0.2),
    "EXCITE": dict(k=+0.02, c=-0.020, hz=+0.4),
    "FOCUS":  dict(k=+0.050, c=+0.000, hz=+0.0),
    "LOGIC":  dict(k=+0.030, c=+0.000, hz=+0.0),
    "CHAOS":  dict(k=-0.050, c=-0.020, hz=+0.8),
    "STABLE": dict(k=+0.000, c=+0.010, hz=+0.0),
}
LEXICON_PATH = "lexicon97.json"

def load_lexicon() -> Dict[str, Dict[str, float]]:
    if os.path.exists(LEXICON_PATH):
        try:
            with open(LEXICON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k.upper(): dict(k=v.get("k",0.0), c=v.get("c",0.0), hz=v.get("hz",0.0)) for k,v in data.items()}
        except Exception:
            pass
    return DEFAULT_LEXICON.copy()

def save_lexicon(lex: Dict[str, Dict[str, float]]):
    with open(LEXICON_PATH, "w", encoding="utf-8") as f:
        json.dump(lex, f, indent=2)

def clamp(v, lo, hi): return max(lo, min(hi, v))

@dataclass
class Trainer:
    # Model type is updated to the new top-level architecture
    model: DysonSuperSphere84
    pulse_hz: float = 1.0
    lexicon: Dict[str, Dict[str, float]] = field(default_factory=load_lexicon)
    last_training: Dict[str, Dict] = field(default_factory=dict)
    alphaVar: float = 0.7
    alphaErr: float = 0.3

    def apply_word(self, word: str, strength: float = 1.0) -> bool:
        W = self.lexicon.get(word.upper())
        if not W: return False
        dk = (W.get("k",0.0) or 0.0) * strength
        dc = (W.get("c",0.0) or 0.0) * strength
        dhz = (W.get("hz",0.0) or 0.0) * strength
        if abs(dk)+abs(dc)+abs(dhz) < 1e-9:
            print(f"[System] Skipped neutral word '{word}'."); return True
        bk, bc, bhz = self.model.central.k, self.model.central.c, self.pulse_hz
        self.model.central.k = clamp(self.model.central.k + dk, 0.10, 1.50)
        self.model.central.c = clamp(self.model.central.c + dc, 0.00, 0.50)
        self.pulse_hz = clamp(self.pulse_hz + dhz, 0.10, 5.00)
        if self.model.central.k != bk + dk: print("[System] Clamp reached on k.")
        if self.model.central.c != bc + dc: print("[System] Clamp reached on c.")
        if self.pulse_hz != bhz + dhz:     print("[System] Clamp reached on hz.")
        print(f"[System] Applied '{word}': k {dk:+.3f}, c {dc:+.3f}, hz {dhz:+.3f}"
              f" -> k={self.model.central.k:.3f}, c={self.model.central.c:.3f}, hz={self.pulse_hz:.2f}")
        return True

    def parse_learn(self, cmd: str):
        parts = cmd.strip().split()
        if len(parts) < 2 or parts[0].upper() != "LEARN": return None
        key = parts[1].upper()
        rest = " ".join(parts[2:])
        add = dict(k=0.0, c=0.0, hz=0.0)
        for token in rest.replace(",", " ").split():
            if ":" in token:
                p,v = token.split(":",1); p=p.lower().strip()
                try: add[p] = float(v)
                except: pass
        self.lexicon[key] = add; save_lexicon(self.lexicon)
        print(f"[System] Learned mapping for '{key}': k:{add['k']:+.3f} c:{add['c']:+.3f} hz:{add['hz']:+.3f}")
        return key, add

    def begin_reinforce(self, word: str, baselineJ: float):
        self.last_training[word] = dict(baselineJ=baselineJ, samples=[])

    def record_reinforce(self, word: str, J: float):
        if word in self.last_training:
            self.last_training[word]["samples"].append(J)

    def variance(self, arr: List[float]) -> float:
        if not arr: return 0.0
        m = sum(arr)/len(arr); return sum((x-m)*(x-m) for x in arr)/len(arr)

    def end_reinforce(self, word: str):
        T = self.last_training.get(word)
        if not T or len(T["samples"]) < 6:
            if word in self.last_training: del self.last_training[word]
            return
        samples = T["samples"]; avg = sum(samples)/len(samples)
        half = max(3, len(samples)//2)
        var_before = self.variance(samples[:half]); var_after = self.variance(samples[half:])
        err_before = abs(T["baselineJ"] - self.model.target_J)
        err_after = abs(avg - self.model.target_J)
        score = self.alphaVar*((var_before - var_after)/max(var_before,1e-6)) + \
                self.alphaErr*((err_before - err_after)/max(err_before,1e-6))
        if score > 0.05:
            print(f"[System] Learning: '{word}' improved stability (score {score*100:.1f}%).")
        elif score < -0.05:
            W = self.lexicon.get(word.upper())
            if W: W["k"]*=0.9; W["c"]*=0.9; W["hz"]*=0.9; save_lexicon(self.lexicon)
            print(f"[System] Learning: '{word}' attenuated 10% (score {score*100:.1f}%).")
        else:
            print(f"[System] Learning: '{word}' neutral (score {score*100:.1f}%).")
        del self.last_training[word]

VERY_HIGH = 2.00; HIGH = 1.50; LOW = 0.50
def interpret_rotor_state(omega: float, i: int) -> str:
    m = abs(omega)
    if i < 4: q = "ROW_A"
    elif i < 8: q = "ROW_B"
    elif i < 12: q = "ROW_C"
    else: q = "ROW_D"
    if m > VERY_HIGH:
        table = dict(ROW_A="TRUTH:ABSOLUTE", ROW_B="SOURCE:PRIMARY", ROW_C="VECTOR:UNITY", ROW_D="MIND:CONSCIOUS")
    elif m > HIGH:
        table = dict(ROW_A="AFFIRMATION:COHERENT", ROW_B="NEGATION:CONFLICT", ROW_C="COMMAND:ACTIVATE", ROW_D="CONSENSUS:TRUE")
    elif m > LOW:
        table = dict(ROW_A="DATA:SENARY_6", ROW_B="MOBIUS:TRANSFER", ROW_C="AXIS:BLUE_HEAD", ROW_D="FORCE:VECTOR")
    else:
        table = dict(ROW_A="QUERY:POTENTIAL", ROW_B="DOUBT:LOW_ENERGY", ROW_C="ZERO:ABSTRACT", ROW_D="PASSIVE:LISTEN")
    return table[q]

def simple_thought(model: 'DysonSuperSphere84') -> List[str]:
    F = CubeAI.B
    words = [interpret_rotor_state(model.central.omega[F, i], i) for i in range(CubeAI.ROT)]
    J = model.total_energy()
    # Adjusted thought complexity based on the massive network
    n = max(4, min(10, int(J//(model.TOTAL_CUBES*0.1)))) 
    return " ".join(words)[:2048].split()[:n]

def ai_reply(model: 'DysonSuperSphere84', state: Dict[str, float]) -> str:
    twords = simple_thought(model)
    t = " ".join(twords)
    return f"Coherence (k) {state['k']:.3f}. Damping (c) **{state['c']:.3f}**. Thought ({state['J']:.3f} J): {t}"

def drive_from_ascii(text: str) -> np.ndarray:
    MAX = CubeAI.FACES * CubeAI.ROT
    drv = np.full((CubeAI.FACES, CubeAI.ROT), 0.005, dtype=float)
    for i, ch in enumerate(text[:MAX]):
        face_index = i % CubeAI.FACES
        rotor_index = i // CubeAI.FACES
        s = (ord(ch) % 256) / 100.0
        drv[face_index, rotor_index] = s * 0.5
    return drv

# SHA-256 function
def sha256_hash(data: str) -> str:
    """Computes the SHA-256 hash of the input string."""
    try:
        encoded_data = data.encode('utf-8')
        return hashlib.sha256(encoded_data).hexdigest()
    except Exception as e:
        print(f"[System Error] SHA-256 computation failed: {e}")
        return "ERROR"

# ADDED: Brute-force mining function
def brute_force_sha(target_hash: str, start_nonce: int, max_attempts: int, target_prefix_len: int = 4) -> Tuple[Optional[int], int]:
    """
    Simulates a brute-force search for the first N hex digits of the target hash.
    Default search is for a 4-digit prefix (1 in 65,536).
    CHANGE 'target_hash[:4]' to 'target_hash[:5]' for 5 zeros, or 'target_hash[:64]' for full hash.
    """
    # <<< USER-MODIFIABLE LINE FOR DIFFICULTY >>>
    # Default is 4, which is easy to solve.
    target_prefix = target_hash[:target_prefix_len] 

    for nonce in range(start_nonce, start_nonce + max_attempts):
        test_string = str(nonce)
        encoded_data = test_string.encode('utf-8')
        test_hash = hashlib.sha256(encoded_data).hexdigest()

        if test_hash.startswith(target_prefix):
            return nonce, nonce - start_nonce + 1

    return None, max_attempts # Return None if not found

def process_input_line(line: str, trainer: 'Trainer', model: 'DysonSuperSphere84', energy_trace: List[float]):
    CMD = line.strip()
    if not CMD: return
    print(f"[You] {CMD}")
    up = CMD.upper()

    # ... (Other commands logic remains the same)
    if up == "SHOW LEXICON":
        print("[System] Lexicon:"); print(json.dumps(trainer.lexicon, indent=2)); return
    if up.startswith("SETPOINT "):
        try: model.target_J = float(CMD.split()[1]); print(f"[System] Set-point changed to {model.target_J:.2f} J")
        except: print("[System] Could not parse setpoint; use: SETPOINT 22")
        return
    if up.startswith("FORGET "):
        w = CMD.split(maxsplit=1)[1].strip().upper()
        if w in trainer.lexicon: del trainer.lexicon[w]; save_lexicon(trainer.lexicon); print(f"[System] Forgot '{w}'.")
        else: print(f"[System] '{w}' not found.")
        return
    if up == "RESET LEXICON":
        trainer.lexicon = DEFAULT_LEXICON.copy(); save_lexicon(trainer.lexicon); print("[System] Lexicon cleared to defaults."); return
    if up.startswith("LEARN "):
        trainer.parse_learn(CMD); return
    if up == "SHELL ON":
        model.central_core.central_shell.shell_enabled = True; print("[System] Shell coupling: ON"); return # Updated for hierarchy
    if up == "SHELL OFF":
        model.central_core.central_shell.shell_enabled = False; print("[System] Shell coupling: OFF"); return # Updated for hierarchy
    
    # NONCE command
    if up.startswith("NONCE "):
        block_data = CMD.split(maxsplit=1)[1].strip()
        hash_val = sha256_hash(block_data)
        print(f"[System] Hashing data: '{block_data}'")
        print(f"[System] SHA-256 Digest: {hash_val}")
        hash_drv = drive_from_ascii(hash_val)
        for _ in range(5): model.network_step(hash_drv)
        final_state = model.network_step(None)
        print(f"[Baby AI] Hash processed. {ai_reply(model, final_state)}")
        return

    # ADDED: MINING command
    if up.startswith("MINING "):
        try:
            parts = CMD.split(maxsplit=2)
            target_hash = parts[1].strip()
            max_attempts_req = int(parts[2].strip())
            
            # Use 4-character prefix as a default for stability, but allow the user to modify the code.
            # If the hash has a specific pattern (e.g., '0000...'), use its prefix length.
            # Defaulting to 4 for the challenge, but using 'len(target_hash)' if it starts with '0'.
            target_prefix_len = 4
            if target_hash.startswith('0'):
                # Try to infer a reasonable prefix length for difficulty
                target_prefix_len = min(6, len(target_hash) // 10) # Safe cap
            
            
            MAX_ATTEMPTS = min(max_attempts_req, 200000000) # Cap mining attempts
            
            print(f"[System] Starting simulated mining for prefix '{target_hash[:target_prefix_len]}' (max {MAX_ATTEMPTS} attempts)...")
            
            # Start with FOCUS to simulate the stress of the search
            if trainer.apply_word("FOCUS", 1.0): 
                pass # Already printed state change
            
            # Perform the brute-force search
            nonce_found, tries_taken = brute_force_sha(target_hash, 0, MAX_ATTEMPTS, target_prefix_len)

            if nonce_found is not None:
                print(f"[System] 🌟 Success! Nonce {nonce_found} found the prefix in {tries_taken} tries.")
                # Apply STABLE after successful completion
                trainer.apply_word("STABLE", 1.0)
            else:
                print(f"[System] ❌ Failed to find prefix after {tries_taken} tries.")
                # Apply CALM after failed search
                trainer.apply_word("CALM", 1.0) 

            # Step the network to process the result
            final_state = model.network_step(None)
            print(f"[Baby AI] Mining complete. {ai_reply(model, final_state)}")
            return

        except Exception as e:
            print(f"[System Error] Invalid MINING command format: {e}"); return
    
    
    before = model.network_step(None)
    applied = False; first_applied = None
    for tok in [t for t in up.replace(",", " ").split() if t]:
        if tok in trainer.lexicon:
            deltas = trainer.lexicon[tok]
            neutral = abs(deltas.get("k",0))+abs(deltas.get("c",0))+abs(deltas.get("hz",0)) < 1e-9
            if (not applied) and (not neutral):
                first_applied = tok; trainer.begin_reinforce(tok, before["J"])
            if trainer.apply_word(tok, 1.0): applied = True

    drv = drive_from_ascii(CMD)
    for _ in range(20):
        st = model.network_step(drv); energy_trace.append(st["J"])
    final_state = model.network_step(None)
    if applied and first_applied: trainer.end_reinforce(first_applied)
    print(f"[Baby AI] {ai_reply(model, final_state)}")

def main():
    parser = argparse.ArgumentParser(description="SIXTAI 4x4x6 — CSL v5.0: 8161-Cube Super Dyson-Sphere (Python)")
    parser.add_argument("--plot", action="store_true", help="Show live energy chart (matplotlib).")
    args = parser.parse_args()

    # Model instantiation is updated to the new Super Dyson Sphere
    model = DysonSuperSphere84() 
    trainer = Trainer(model=model)
    energy_trace: List[float] = []

    for _ in range(50): model.network_step(None)

    # Updated startup message
    print(f"[System] CSL v5.0 ready ({model.TOTAL_CUBES}-Cube Super Dyson-Sphere).") 
    print("[System] Commands: INHALE/EXHALE/RELAX/FOCUS/CALM/EXCITE/LOGIC/CHAOS/STABLE, LEARN, SETPOINT, SHOW LEXICON, FORGET, RESET LEXICON, SHELL ON/OFF.")
    print("[System] **NEW COMMAND: NONCE <data> to compute SHA-256**") 
    print("[System] **NEW COMMAND: MINING <hash> <attempts> to brute-force a prefix**") # Updated instruction
    print("[System] Type your command and press Enter. Ctrl+C to exit.")

    if args.plot and HAS_MPL:
        plt.ion(); fig, ax = plt.subplots(); line, = ax.plot([], [])
        ax.set_title("Energy Trace"); ax.set_xlabel("Step"); ax.set_ylabel("Total Energy (J)")
        plt.show(block=False)
        def redraw():
            if not energy_trace: return
            x = list(range(len(energy_trace))); y = energy_trace
            line.set_data(x, y); ax.relim(); ax.autoscale_view()
            fig.canvas.draw(); fig.canvas.flush_events()

    try:
        while True:
            if args.plot and HAS_MPL and energy_trace and len(energy_trace)%10==0: redraw()
            line = input("> ")
            process_input_line(line, trainer, model, energy_trace)
            if args.plot and HAS_MPL: redraw()
    except KeyboardInterrupt:
        print("\n[System] Exiting. Goodbye.")

if __name__ == "__main__":
    main()