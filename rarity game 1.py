import tkinter as tk
import random
import math
import time
import json
import os
import atexit

# --- GAME CONFIGURATION & 48 TIERS ---
WIDTH, HEIGHT = 940, 680
MAP_SIZE = 2400

# Store save file in user's permanent Home folder so closing Thonny
# or running unsaved tabs never loses or resets progress.
HOME_DIR = os.path.expanduser("~")
SAVE_FILE = os.path.join(HOME_DIR, "rarity_sword_save.json")

try:
    LEGACY_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    LEGACY_DIR = os.getcwd()
LEGACY_SAVE_FILE = os.path.join(LEGACY_DIR, "rarity_save.json")


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    r = max(0, min(255, int(round(rgb[0]))))
    g = max(0, min(255, int(round(rgb[1]))))
    b = max(0, min(255, int(round(rgb[2]))))
    return f"#{r:02X}{g:02X}{b:02X}"


def blend_palette(palette_rgb, phase):
    n = len(palette_rgb)
    pos = phase % n
    i0 = int(pos) % n
    i1 = (i0 + 1) % n
    t = pos - int(pos)
    smooth_t = t * t * (3.0 - 2.0 * t)
    c0 = palette_rgb[i0]
    c1 = palette_rgb[i1]
    return rgb_to_hex((
        c0[0] + (c1[0] - c0[0]) * smooth_t,
        c0[1] + (c1[1] - c0[1]) * smooth_t,
        c0[2] + (c1[2] - c0[2]) * smooth_t,
    ))


RAINBOW_STOPS = [
    "#EF4444", "#F97316", "#FACC15",
    "#22C55E", "#38BDF8", "#A855F7", "#EC4899"
]

# 48 Tiers: (Name, Color Stops, Cycle Speed, Sacrifice Multiplier)
# Tiers 1-14: Fixed colors | Tiers 15+: Smooth color cycle (+ = 2x speed)
TIER_DEFS = [
    ("Poor",          ["#9CA3AF"], 0.0, 0),
    ("Basic",         ["#E5E7EB"], 0.0, 0),
    ("Common",        ["#FFFFFF"], 0.0, 0),
    ("Common+",       ["#CBD5E1"], 0.0, 0),
    ("Uncommon",      ["#4ADE80"], 0.0, 1),
    ("Uncommon+",     ["#22C55E"], 0.0, 1),
    ("Rare",          ["#38BDF8"], 0.0, 2),
    ("Rare+",         ["#3B82F6"], 0.0, 3),
    ("Epic",          ["#A855F7"], 0.0, 4),
    ("Epic+",         ["#C084FC"], 0.0, 6),
    ("Legendary",     ["#FACC15"], 0.0, 8),
    ("Legendary+",    ["#FB923C"], 0.0, 11),
    ("Mythical",      ["#F43F5E"], 0.0, 15),
    ("Mythical+",     ["#EF4444"], 0.0, 20),
    # 15-16: Black to White
    ("Ethereal",      ["#111827", "#FFFFFF"], 1.0, 26),
    ("Ethereal+",     ["#111827", "#FFFFFF"], 2.0, 34),
    # 17-18: Red to Yellow
    ("Ultimate",      ["#EF4444", "#FACC15"], 1.0, 44),
    ("Ultimate+",     ["#EF4444", "#FACC15"], 2.0, 56),
    # 19-20: Light Purple to White
    ("Divine",        ["#D8B4FE", "#FFFFFF"], 1.0, 72),
    ("Divine+",       ["#D8B4FE", "#FFFFFF"], 2.0, 92),
    # 21-22: Cyan to White
    ("Godly",         ["#22D3EE", "#FFFFFF"], 1.0, 118),
    ("Godly+",        ["#22D3EE", "#FFFFFF"], 2.0, 150),
    # 23-24: Green to Salmon
    ("Unreal",        ["#4ADE80", "#FA8072"], 1.0, 190),
    ("Unreal+",       ["#4ADE80", "#FA8072"], 2.0, 240),
    # 25-26: Super Light Green -> Super Light Purple -> Super Light Blue -> White
    (
        "Impossible",
        ["#BBF7D0", "#E9D5FF", "#BAE6FD", "#FFFFFF", "#BAE6FD", "#E9D5FF"],
        1.2,
        305,
    ),
    (
        "Impossible+",
        ["#BBF7D0", "#E9D5FF", "#BAE6FD", "#FFFFFF", "#BAE6FD", "#E9D5FF"],
        2.4,
        390,
    ),
    # 27-28: Red to Black to White
    ("Eclipse",       ["#EF4444", "#111827", "#FFFFFF", "#111827"], 1.1, 500),
    ("Eclipse+",      ["#EF4444", "#111827", "#FFFFFF", "#111827"], 2.2, 640),
    # 29-30: Yellow to Black to White to Red
    ("Eternal",       ["#FACC15", "#111827", "#FFFFFF", "#EF4444"], 1.1, 820),
    ("Eternal+",      ["#FACC15", "#111827", "#FFFFFF", "#EF4444"], 2.2, 1050),
    # 31-32: Yellow to Red to Black to White
    ("Solar",         ["#FACC15", "#EF4444", "#111827", "#FFFFFF"], 1.1, 1350),
    ("Solar+",        ["#FACC15", "#EF4444", "#111827", "#FFFFFF"], 2.2, 1750),
    # 33-34: Green to Black
    ("Transcendent",  ["#22C55E", "#111827"], 1.0, 2250),
    ("Transcendent+", ["#22C55E", "#111827"], 2.0, 2900),
    # 35-36: Cyan to Pink with dark colors during transition
    (
        "Opulent",
        ["#22D3EE", "#0F172A", "#2E1065", "#F472B6", "#2E1065", "#0F172A"],
        1.3,
        3750,
    ),
    (
        "Opulent+",
        ["#22D3EE", "#0F172A", "#2E1065", "#F472B6", "#2E1065", "#0F172A"],
        2.6,
        4850,
    ),
    # 37-40: Rainbow (next two tier pairs)
    ("Unlimited",     RAINBOW_STOPS, 1.8, 6250),
    ("Unlimited+",    RAINBOW_STOPS, 3.6, 8000),
    ("Infinity",      RAINBOW_STOPS, 2.2, 10500),
    ("Infinity+",     RAINBOW_STOPS, 4.4, 14000),
    # 41-48: Custom endgame cosmic palettes
    ("Stellar",       ["#38BDF8", "#FDE047", "#FFFFFF", "#818CF8"], 1.4, 18000),
    ("Stellar+",      ["#38BDF8", "#FDE047", "#FFFFFF", "#818CF8"], 2.8, 23000),
    ("Transfinite",   ["#6366F1", "#EC4899", "#10B981", "#22D3EE"], 1.5, 30000),
    ("Transfinite+",  ["#6366F1", "#EC4899", "#10B981", "#22D3EE"], 3.0, 39000),
    ("Omega",         ["#DC2626", "#111827", "#9333EA", "#FACC15"], 1.5, 50000),
    ("Omega+",        ["#DC2626", "#111827", "#9333EA", "#FACC15"], 3.0, 65000),
    ("Omega++",       ["#DC2626", "#111827", "#9333EA", "#FACC15"], 4.5, 84000),
    (
        "ZENITH",
        ["#FFFFFF", "#FDE047", "#38BDF8", "#F43F5E", "#A855F7", "#4ADE80"],
        3.2,
        110000,
    ),
]

RARITIES = []
for idx, (r_name, r_cols, c_spd, reb_gain) in enumerate(TIER_DEFS):
    base_xp = int(round(100 * (1.65 ** idx)))
    is_last = idx == len(TIER_DEFS) - 1
    xp_req = base_xp if not is_last else 999_999_999_999_999_999
    RARITIES.append({
        "name": r_name,
        "color": r_cols[0],
        "palette_rgb": [hex_to_rgb(c) for c in r_cols],
        "cycle_speed": c_spd,
        "power": int(round(10 * (1.28 ** idx))),
        "npc_hp": int(round(115 * (1.33 ** idx))),
        "player_hp": int(round(55 * (1.25 ** idx))),
        "xp_req": xp_req,
        "npc_xp": max(1, base_xp // 4),
        "rebirth_gain": reb_gain,
    })


def format_num(val):
    val = int(val)
    units = [
        (1_000_000_000_000_000_000_000, 1_000_000_000_000_000_000_000, "Sx"),
        (1_000_000_000_000_000_000, 1_000_000_000_000_000_000, "Qi"),
        (1_000_000_000_000_000, 1_000_000_000_000_000, "Qa"),
        (1_000_000_000_000, 1_000_000_000_000, "T"),
        (1_000_000_000, 1_000_000_000, "B"),
        (1_000_000, 1_000_000, "M"),
        (10_000, 1_000, "K"),
    ]
    for threshold, divisor, suffix in units:
        if val >= threshold:
            return f"{val / divisor:.2f}{suffix}"
    return f"{val:,}"


def angle_diff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


class RaritySwordGame:
    def __init__(self, root):
        self.root = root
        self.root.title("2D Rarity Sword Simulator")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT,
            bg="#214729", highlightthickness=0
        )
        self.canvas.pack()
        self.canvas.focus_set()

        self.px = MAP_SIZE / 2
        self.py = MAP_SIZE / 2
        self.rarity_idx = 0
        self.xp = 0
        self.multiplier = 1
        self.prestige_mult = 1
        self.luck_level = 0
        self.load_progress()

        self.max_hp = RARITIES[self.rarity_idx]["player_hp"]
        self.hp = self.max_hp

        # Combat & Animation State
        self.mouse_x = WIDTH / 2 + 50
        self.mouse_y = HEIGHT / 2
        self.aim_angle = 0.0
        self.swing_timer = 0.0
        self.swing_dur = 0.22
        self.swing_dir = 1
        self.attack_cd = 0.0
        self.walk_phase = 0.0
        self.step_timer = 0.0
        self.shake_timer = 0.0
        self.shake_mag = 0.0
        self.anim_time = 0.0

        # Ability & UI Timers
        self.sacrifice_cd = 0.0
        self.summon_cd = 0.0
        self.reset_confirm = 0.0
        self.xp_tick_timer = 0.0
        self.autosave_timer = 0.0
        self.save_banner = 0.0
        self.announce_text = ""
        self.announce_color = "#FFFFFF"
        self.announce_tier = None
        self.announce_timer = 0.0

        self.last_time = time.time()
        self.keys = set()
        self.popups = []
        self.particles = []
        self.rings = []

        self.build_map_props()
        self.npcs = [self.create_npc(announce=False) for _ in range(34)]

        # Top-Right UI Button Rectangles
        bx1, bx2 = WIDTH - 235, WIDTH - 15
        self.sac_rect = (bx1, 12, bx2, 58)
        self.pres_rect = (bx1, 64, bx2, 110)
        self.luck_rect = (bx1, 116, bx2, 162)
        self.sum_rect = (bx1, 168, bx2, 214)
        self.rst_rect = (bx1, 220, bx2, 258)

        for widget in (root, self.canvas):
            widget.bind("<KeyPress>", self.on_key_down)
            widget.bind("<KeyRelease>", self.on_key_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_left_click)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        atexit.register(self.save_progress)

        self.game_loop()

    def get_tier_color(self, idx):
        data = RARITIES[idx]
        spd = data["cycle_speed"]
        if spd <= 0.0:
            return data["color"]
        return blend_palette(data["palette_rgb"], self.anim_time * spd * 1.6)

    def get_luck_val(self, lvl=None):
        if lvl is None:
            lvl = self.luck_level
        return round(1.0 + (lvl * 0.5) + (lvl ** 1.45) * 0.25, 1)

    def get_luck_cost(self):
        return int(round(5 * (1.42 ** self.luck_level)))

    def get_prestige_cost(self):
        return 10000 * self.prestige_mult

    def get_spawn_weights(self):
        luck = self.get_luck_val()
        decay = min(0.88, 0.26 ** (1.0 / (luck ** 0.48)))
        return [decay ** i for i in range(len(RARITIES))]

    def get_rare_announce_tier(self):
        # Dynamically raises the announcement threshold as Luck rises
        # so only spawns with <0.6% chance at your current Luck announce.
        weights = self.get_spawn_weights()
        total_w = sum(weights)
        max_thresh = len(RARITIES) - 4
        for i, w in enumerate(weights):
            if (w / total_w) < 0.006:
                return min(max_thresh, max(4, i))
        return max_thresh

    def build_map_props(self):
        self.trees = []
        for _ in range(55):
            tx = random.randint(90, MAP_SIZE - 90)
            ty = random.randint(90, MAP_SIZE - 90)
            if math.hypot(tx - MAP_SIZE / 2, ty - MAP_SIZE / 2) > 220:
                self.trees.append((tx, ty, random.randint(24, 38)))

        self.stones = [
            (
                random.randint(80, MAP_SIZE - 80),
                random.randint(80, MAP_SIZE - 80),
                random.randint(8, 16),
            )
            for _ in range(70)
        ]
        flower_cols = ["#FDE047", "#F472B6", "#60A5FA", "#FFFFFF"]
        self.flowers = [
            (
                random.randint(60, MAP_SIZE - 60),
                random.randint(60, MAP_SIZE - 60),
                random.choice(flower_cols),
            )
            for _ in range(130)
        ]

    def trigger_announce(self, text, color, tier_idx=None):
        self.announce_text = text
        self.announce_color = color
        self.announce_tier = tier_idx
        self.announce_timer = 3.2

    def add_shake(self, duration, mag):
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_mag = max(self.shake_mag, mag)

    def spawn_sparks(self, x, y, color, count=10, speed=180):
        for _ in range(count):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed * 0.35, speed)
            life = random.uniform(0.22, 0.48)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": life,
                "max_life": life,
                "size": random.uniform(2.5, 5.0),
                "color": color,
            })

    def spawn_ring(self, x, y, max_r, color, dur=0.45):
        self.rings.append({
            "x": x,
            "y": y,
            "r": 10.0,
            "max_r": max_r,
            "life": dur,
            "max_life": dur,
            "color": color,
        })

    def save_progress(self, show_banner=False):
        data = {
            "rarity_idx": self.rarity_idx,
            "xp": self.xp,
            "multiplier": self.multiplier,
            "prestige_mult": self.prestige_mult,
            "luck_level": self.luck_level,
        }
        tmp_file = SAVE_FILE + ".tmp"
        try:
            with open(tmp_file, "w") as f:
                json.dump(data, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, SAVE_FILE)
            if show_banner:
                self.save_banner = 1.5
        except Exception:
            pass

    def load_progress(self):
        target_file = None
        if os.path.exists(SAVE_FILE):
            target_file = SAVE_FILE
        elif os.path.exists(LEGACY_SAVE_FILE):
            target_file = LEGACY_SAVE_FILE

        if target_file:
            try:
                with open(target_file, "r") as f:
                    data = json.load(f)
                max_i = len(RARITIES) - 1
                raw_r = int(data.get("rarity_idx", 0))
                self.rarity_idx = max(0, min(max_i, raw_r))
                self.xp = max(0, int(data.get("xp", 0)))
                self.multiplier = max(1, int(data.get("multiplier", 1)))
                self.prestige_mult = max(
                    1, int(data.get("prestige_mult", 1))
                )
                self.luck_level = max(0, int(data.get("luck_level", 0)))
                if target_file == LEGACY_SAVE_FILE:
                    self.save_progress()
            except Exception:
                pass

    def reset_all_progress(self):
        self.rarity_idx = 0
        self.xp = 0
        self.multiplier = 1
        self.prestige_mult = 1
        self.luck_level = 0
        self.max_hp = RARITIES[0]["player_hp"]
        self.hp = self.max_hp
        self.px = MAP_SIZE / 2
        self.py = MAP_SIZE / 2
        self.sacrifice_cd = 0.0
        self.summon_cd = 0.0
        self.reset_confirm = 0.0
        self.npcs = [self.create_npc(announce=False) for _ in range(34)]
        self.save_progress(show_banner=True)
        self.spawn_ring(self.px, self.py, 110, "#EF4444", 0.5)
        self.trigger_announce("ALL PROGRESS RESET!", "#F87171")

    def on_close(self):
        self.save_progress()
        self.root.destroy()

    def create_npc(self, r_idx=None, pos=None, is_ally=False, announce=True):
        if r_idx is None:
            pool = range(len(RARITIES))
            weights = self.get_spawn_weights()
            r_idx = random.choices(pool, weights=weights, k=1)[0]
        data = RARITIES[r_idx]

        if pos is None:
            while True:
                nx = random.randint(100, MAP_SIZE - 100)
                ny = random.randint(100, MAP_SIZE - 100)
                if math.hypot(nx - self.px, ny - self.py) > 220:
                    break
        else:
            nx, ny = pos

        if announce and not is_ally and r_idx >= self.get_rare_announce_tier():
            self.trigger_announce(
                f"RARE SPAWN: [{data['name']}] (Tier {r_idx + 1})!",
                self.get_tier_color(r_idx),
                tier_idx=r_idx,
            )

        stat_mult = 1.35 if is_ally else 1.0
        npc_hp = int(round(data["npc_hp"] * stat_mult))
        npc_pwr = int(round(data["power"] * stat_mult))

        return {
            "x": nx,
            "y": ny,
            "rarity_idx": r_idx,
            "hp": npc_hp,
            "max_hp": npc_hp,
            "power": npc_pwr,
            "xp_reward": data["npc_xp"],
            "is_ally": is_ally,
            "facing": random.uniform(0, 2 * math.pi),
            "walk_phase": random.uniform(0, 6.28),
            "attack_cd": random.uniform(0.4, 1.2),
            "swing_timer": 0.0,
            "hit_flash": 0.0,
        }

    def add_popup(self, x, y, text, color="#FFFFFF"):
        self.popups.append({
            "x": x, "y": y, "text": text, "color": color, "life": 0.95
        })

    def add_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.rarity_idx < len(RARITIES) - 1:
            req = RARITIES[self.rarity_idx]["xp_req"]
            if self.xp >= req:
                self.xp -= req
                self.rarity_idx += 1
                leveled_up = True
            else:
                break
        if leveled_up:
            tier_num = self.rarity_idx + 1
            total_t = len(RARITIES)
            r_data = RARITIES[self.rarity_idx]
            cur_col = self.get_tier_color(self.rarity_idx)
            self.max_hp = r_data["player_hp"]
            self.hp = self.max_hp
            self.spawn_ring(self.px, self.py, 130, cur_col, 0.55)
            self.spawn_sparks(self.px, self.py, cur_col, 22, 240)
            self.add_shake(0.18, 5)
            self.add_popup(
                self.px, self.py - 40,
                f"RANK UP ({tier_num}/{total_t}): {r_data['name']}!",
                cur_col,
            )
            if tier_num == 20:
                self.trigger_announce(
                    "UNLOCKED: Tier 20 Summon Ability [E]!",
                    self.get_tier_color(19),
                    tier_idx=19,
                )
            self.save_progress(show_banner=True)

    def buy_luck_upgrade(self):
        cost = self.get_luck_cost()
        if self.multiplier - cost < 1:
            self.add_popup(
                self.px, self.py - 32,
                f"Need > {format_num(cost)}x Mult!", "#34D399"
            )
            return
        self.multiplier -= cost
        self.luck_level += 1
        new_luck = self.get_luck_val()
        self.spawn_ring(self.px, self.py, 115, "#10B981", 0.45)
        self.spawn_sparks(self.px, self.py, "#34D399", 18, 210)
        self.save_progress(show_banner=True)
        self.add_popup(
            self.px, self.py - 40,
            f"LUCK UP! Now {new_luck:.1f}x!", "#34D399"
        )

    def sacrifice(self):
        if self.sacrifice_cd > 0:
            self.add_popup(
                self.px, self.py - 32,
                f"Cooldown: {self.sacrifice_cd:.1f}s", "#CBD5E1"
            )
            return
        base_gain = RARITIES[self.rarity_idx]["rebirth_gain"]
        if base_gain <= 0:
            t5_name = RARITIES[4]["name"]
            self.add_popup(
                self.px, self.py - 32, f"Need {t5_name} (Tier 5)!", "#FF6B6B"
            )
            return
        self.sacrifice_cd = 5.0
        total_gain = base_gain * self.prestige_mult
        self.multiplier += total_gain
        self.xp = 0
        self.rarity_idx = 0
        self.max_hp = RARITIES[0]["player_hp"]
        self.hp = self.max_hp
        self.spawn_ring(self.px, self.py, 140, "#FACC15", 0.55)
        self.spawn_sparks(self.px, self.py, "#FACC15", 24, 250)
        self.save_progress(show_banner=True)
        self.add_popup(
            self.px, self.py - 40,
            f"SACRIFICED! +{format_num(total_gain)}x Mult!", "#FFD700"
        )

    def prestige(self):
        cost = self.get_prestige_cost()
        if self.multiplier < cost:
            self.add_popup(
                self.px, self.py - 32,
                f"Need {format_num(cost)} Multiplier!", "#F472B6"
            )
            return
        self.prestige_mult += 1
        self.multiplier = 1
        self.xp = 0
        self.rarity_idx = 0
        self.sacrifice_cd = 0.0
        self.max_hp = RARITIES[0]["player_hp"]
        self.hp = self.max_hp
        self.spawn_ring(self.px, self.py, 160, "#38BDF8", 0.65)
        self.spawn_sparks(self.px, self.py, "#38BDF8", 30, 280)
        self.save_progress(show_banner=True)
        self.add_popup(
            self.px, self.py - 44,
            f"PRESTIGED! Sac Mult: {self.prestige_mult}x!", "#38BDF8"
        )

    def use_summon_ability(self):
        if self.rarity_idx < 19:
            self.add_popup(
                self.px, self.py - 32, "Unlocks at Tier 20!", "#FDA4AF"
            )
            return
        if self.summon_cd > 0:
            self.add_popup(
                self.px, self.py - 32,
                f"Cooldown: {self.summon_cd:.1f}s", "#CBD5E1"
            )
            return

        self.summon_cd = 60.0
        allies = [n for n in self.npcs if n["is_ally"]]
        while len(allies) > 4:
            oldest = allies.pop(0)
            if oldest in self.npcs:
                self.npcs.remove(oldest)

        mult_bonus = min(20, int(math.log(max(1, self.multiplier), 2.35)))
        luck_val = max(1.0, self.get_luck_val())
        luck_stat_bonus = min(10, int(math.log(luck_val, 2.0)))
        offsets = [(-75, -75), (75, -75), (-75, 75), (75, 75)]
        best_tier = 0

        for ox, oy in offsets:
            roll = random.random()
            rng_bonus = int(-math.log(max(1e-6, 1.0 - roll)) * 1.15)
            raw_tier = 1 + mult_bonus + luck_stat_bonus + rng_bonus
            r_idx = max(0, min(len(RARITIES) - 1, raw_tier))
            best_tier = max(best_tier, r_idx)

            sx = max(40, min(MAP_SIZE - 40, self.px + ox))
            sy = max(40, min(MAP_SIZE - 40, self.py + oy))
            ally = self.create_npc(
                r_idx=r_idx, pos=(sx, sy), is_ally=True, announce=False
            )
            self.npcs.append(ally)
            col = self.get_tier_color(r_idx)
            self.spawn_ring(sx, sy, 65, col, 0.45)
            self.spawn_sparks(sx, sy, col, 14, 170)

        self.add_shake(0.15, 4)
        best_name = RARITIES[best_tier]["name"]
        self.trigger_announce(
            f"SUMMONED 4 ALLIES! Best: [{best_name}]",
            self.get_tier_color(best_tier),
            tier_idx=best_tier,
        )

    def kill_npc(self, npc):
        if npc not in self.npcs:
            return

        xp_per_sec = 5 * self.multiplier
        xp_gained = npc["xp_reward"] + xp_per_sec
        self.add_xp(xp_gained)

        col = self.get_tier_color(npc["rarity_idx"])
        self.spawn_ring(npc["x"], npc["y"], 55, col, 0.35)
        self.spawn_sparks(npc["x"], npc["y"], col, 16, 200)
        self.add_popup(
            npc["x"], npc["y"] - 42,
            f"+{format_num(xp_gained)} XP!", col
        )

        if npc["rarity_idx"] > self.rarity_idx:
            self.multiplier += 1
            self.save_progress()
            self.add_popup(
                npc["x"], npc["y"] - 64,
                "+1x MULTIPLIER!", "#FACC15"
            )

        was_ally = npc["is_ally"]
        self.npcs.remove(npc)
        if not was_ally:
            self.npcs.append(self.create_npc(announce=True))

    def swing_player_sword(self):
        if self.attack_cd > 0:
            return
        self.attack_cd = 0.32
        self.swing_timer = self.swing_dur
        self.swing_dir *= -1

        sword_range = 92
        p_data = RARITIES[self.rarity_idx]
        p_power = p_data["power"]
        p_col = self.get_tier_color(self.rarity_idx)

        tip_x = self.px + math.cos(self.aim_angle) * 58
        tip_y = self.py + math.sin(self.aim_angle) * 58
        self.spawn_sparks(tip_x, tip_y, p_col, 6, 120)

        for npc in list(self.npcs):
            dx = npc["x"] - self.px
            dy = npc["y"] - self.py
            dist = math.hypot(dx, dy)
            if dist <= sword_range + 18:
                ang = math.atan2(dy, dx)
                if abs(angle_diff(ang, self.aim_angle)) <= 1.2:
                    npc["hp"] -= p_power
                    npc["hit_flash"] = 0.12
                    if dist > 0.01:
                        npc["x"] += (dx / dist) * 22
                        npc["y"] += (dy / dist) * 22
                    self.spawn_sparks(npc["x"], npc["y"], "#FDE047", 9, 170)
                    self.add_shake(0.07, 2.5)
                    self.add_popup(
                        npc["x"], npc["y"] - 26,
                        f"-{format_num(p_power)}", "#FDE047"
                    )
                    if npc["hp"] <= 0:
                        self.kill_npc(npc)

    def on_key_down(self, event):
        key = event.keysym.lower()
        self.keys.add(key)
        if key == "space":
            self.swing_player_sword()
        elif key == "r":
            self.sacrifice()
        elif key == "p":
            self.prestige()
        elif key == "l":
            self.buy_luck_upgrade()
        elif key == "e":
            self.use_summon_ability()

    def on_key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def in_rect(self, x, y, rect):
        return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]

    def on_left_click(self, event):
        self.canvas.focus_set()
        mx, my = event.x, event.y
        if self.in_rect(mx, my, self.sac_rect):
            self.sacrifice()
        elif self.in_rect(mx, my, self.pres_rect):
            self.prestige()
        elif self.in_rect(mx, my, self.luck_rect):
            self.buy_luck_upgrade()
        elif self.in_rect(mx, my, self.sum_rect):
            self.use_summon_ability()
        elif self.in_rect(mx, my, self.rst_rect):
            if self.reset_confirm > 0:
                self.reset_all_progress()
            else:
                self.reset_confirm = 3.0
        else:
            self.swing_player_sword()

    def update(self, dt):
        self.anim_time += dt
        self.swing_timer = max(0.0, self.swing_timer - dt)
        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.sacrifice_cd = max(0.0, self.sacrifice_cd - dt)
        self.summon_cd = max(0.0, self.summon_cd - dt)
        self.reset_confirm = max(0.0, self.reset_confirm - dt)
        self.save_banner = max(0.0, self.save_banner - dt)
        self.announce_timer = max(0.0, self.announce_timer - dt)
        self.shake_timer = max(0.0, self.shake_timer - dt)

        self.autosave_timer += dt
        if self.autosave_timer >= 5.0:
            self.autosave_timer = 0.0
            self.save_progress(show_banner=True)

        self.xp_tick_timer += dt
        if self.xp_tick_timer >= 1.0:
            self.xp_tick_timer -= 1.0
            tick_xp = 5 * self.multiplier
            self.add_xp(tick_xp)
            self.save_progress()
            self.add_popup(
                self.px, self.py - 30, f"+{format_num(tick_xp)} XP", "#A7F3D0"
            )

        if self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.max_hp * 0.04 * dt)

        vx, vy = 0, 0
        if "w" in self.keys or "up" in self.keys:
            vy -= 1
        if "s" in self.keys or "down" in self.keys:
            vy += 1
        if "a" in self.keys or "left" in self.keys:
            vx -= 1
        if "d" in self.keys or "right" in self.keys:
            vx += 1

        if vx != 0 or vy != 0:
            mag = math.hypot(vx, vy)
            spd = 270
            nx = self.px + (vx / mag) * spd * dt
            ny = self.py + (vy / mag) * spd * dt
            self.px = max(35, min(MAP_SIZE - 35, nx))
            self.py = max(35, min(MAP_SIZE - 35, ny))
            self.walk_phase += dt * 11
            self.step_timer += dt
            if self.step_timer >= 0.22:
                self.step_timer = 0.0
                self.spawn_sparks(self.px, self.py + 12, "#86EFAC", 2, 45)
        else:
            self.walk_phase += dt * 2.5

        self.aim_angle = math.atan2(
            self.mouse_y - HEIGHT / 2, self.mouse_x - WIDTH / 2
        )

        for npc in list(self.npcs):
            if npc not in self.npcs:
                continue
            npc["hit_flash"] = max(0.0, npc["hit_flash"] - dt)
            npc["swing_timer"] = max(0.0, npc["swing_timer"] - dt)
            npc["attack_cd"] = max(0.0, npc["attack_cd"] - dt)

            if npc["is_ally"]:
                self.update_ally_npc(npc, dt)
            else:
                self.update_hostile_npc(npc, dt)

        for pt in list(self.particles):
            pt["x"] += pt["vx"] * dt
            pt["y"] += pt["vy"] * dt
            pt["vx"] *= 0.92
            pt["vy"] *= 0.92
            pt["life"] -= dt
            if pt["life"] <= 0:
                self.particles.remove(pt)

        for rg in list(self.rings):
            rg["life"] -= dt
            prog = 1.0 - max(0.0, rg["life"] / rg["max_life"])
            rg["r"] = 10.0 + (rg["max_r"] - 10.0) * prog
            if rg["life"] <= 0:
                self.rings.remove(rg)

        for p in list(self.popups):
            p["y"] -= 36 * dt
            p["life"] -= dt
            if p["life"] <= 0:
                self.popups.remove(p)

    def update_ally_npc(self, ally, dt):
        target = None
        best_dist = 460.0
        for other in self.npcs:
            if not other["is_ally"]:
                d = math.hypot(other["x"] - ally["x"], other["y"] - ally["y"])
                if d < best_dist:
                    best_dist = d
                    target = other

        if target is not None:
            dx = target["x"] - ally["x"]
            dy = target["y"] - ally["y"]
            ally["facing"] = math.atan2(dy, dx)
            if best_dist > 50:
                spd = 225
                ally["x"] += (dx / best_dist) * spd * dt
                ally["y"] += (dy / best_dist) * spd * dt
                ally["walk_phase"] += dt * 11
            elif ally["attack_cd"] <= 0:
                ally["attack_cd"] = 0.72
                ally["swing_timer"] = 0.2
                dmg = ally["power"]
                target["hp"] -= dmg
                target["hit_flash"] = 0.12
                self.spawn_sparks(target["x"], target["y"], "#38BDF8", 7, 150)
                self.add_popup(
                    target["x"], target["y"] - 24,
                    f"-{format_num(dmg)}", "#38BDF8"
                )
                if target["hp"] <= 0:
                    self.kill_npc(target)
        else:
            dx = self.px - ally["x"]
            dy = self.py - ally["y"]
            dist = math.hypot(dx, dy)
            if dist > 115:
                ally["facing"] = math.atan2(dy, dx)
                ally["x"] += (dx / dist) * 205 * dt
                ally["y"] += (dy / dist) * 205 * dt
                ally["walk_phase"] += dt * 9

    def update_hostile_npc(self, npc, dt):
        target_type = "player"
        target_npc = None
        tx, ty = self.px, self.py
        best_dist = math.hypot(self.px - npc["x"], self.py - npc["y"])

        for other in self.npcs:
            if other["is_ally"]:
                d = math.hypot(other["x"] - npc["x"], other["y"] - npc["y"])
                if d < best_dist:
                    best_dist = d
                    target_type = "ally"
                    target_npc = other
                    tx, ty = other["x"], other["y"]

        if best_dist < 280:
            dx = tx - npc["x"]
            dy = ty - npc["y"]
            npc["facing"] = math.atan2(dy, dx)
            if best_dist > 52:
                spd = min(195, 110 + npc["rarity_idx"] * 2.5)
                npc["x"] += (dx / best_dist) * spd * dt
                npc["y"] += (dy / best_dist) * spd * dt
                npc["walk_phase"] += dt * 9
            elif npc["attack_cd"] <= 0:
                npc["attack_cd"] = 1.25
                npc["swing_timer"] = 0.2
                dmg = npc["power"]
                if target_type == "ally" and target_npc in self.npcs:
                    target_npc["hp"] -= dmg
                    target_npc["hit_flash"] = 0.12
                    self.spawn_sparks(tx, ty, "#EF4444", 6, 140)
                    if target_npc["hp"] <= 0:
                        self.npcs.remove(target_npc)
                else:
                    self.hp -= dmg
                    self.add_shake(0.1, 3.5)
                    self.spawn_sparks(self.px, self.py, "#EF4444", 8, 160)
                    self.add_popup(
                        self.px, self.py - 22,
                        f"-{format_num(dmg)} HP", "#EF4444"
                    )
                    if self.hp <= 0:
                        self.px, self.py = MAP_SIZE / 2, MAP_SIZE / 2
                        self.hp = self.max_hp
                        self.add_popup(
                            self.px, self.py - 42,
                            "DEFEATED! Respawned", "#F87171"
                        )

    # --- DRAWING HELPERS ---
    def draw_slash_wave(self, cx, cy, base_ang, col, prog, s_dir):
        pts = []
        steps = 7
        start_a = base_ang - 1.1 * s_dir
        end_a = base_ang + (-1.1 + prog * 2.2) * s_dir
        for i in range(steps + 1):
            a = start_a + (end_a - start_a) * (i / steps)
            pts.extend([cx + math.cos(a) * 88, cy + math.sin(a) * 88])
        for i in range(steps, -1, -1):
            t = i / steps
            a = start_a + (end_a - start_a) * t
            r_in = 88 - 24 * math.sin(t * math.pi)
            pts.extend([cx + math.cos(a) * r_in, cy + math.sin(a) * r_in])
        self.canvas.create_polygon(pts, fill=col, outline="#FFFFFF", width=2)

    def draw_sword(self, cx, cy, base_ang, blade_col, swing_t, max_t, s_dir):
        ang = base_ang
        if swing_t > 0:
            prog = 1.0 - (swing_t / max_t)
            ang = base_ang + (-1.15 + prog * 2.30) * s_dir
            self.draw_slash_wave(cx, cy, base_ang, blade_col, prog, s_dir)

        perp = ang + math.pi / 2
        cos_a, sin_a = math.cos(ang), math.sin(ang)
        cos_p, sin_p = math.cos(perp), math.sin(perp)

        gx1, gy1 = cx + cos_a * 12, cy + sin_a * 12
        gx2, gy2 = cx + cos_a * 23, cy + sin_a * 23
        self.canvas.create_line(gx1, gy1, gx2, gy2, fill="#451A03", width=5)
        self.canvas.create_oval(
            gx1 - 4, gy1 - 4, gx1 + 4, gy1 + 4, fill="#F59E0B", outline=""
        )

        cx1, cy1 = gx2 + cos_p * 11, gy2 + sin_p * 11
        cx2, cy2 = gx2 - cos_p * 11, gy2 - sin_p * 11
        self.canvas.create_line(cx1, cy1, cx2, cy2, fill="#F59E0B", width=5)

        b1x, b1y = gx2 + cos_p * 4.5, gy2 + sin_p * 4.5
        b2x, b2y = gx2 - cos_p * 4.5, gy2 - sin_p * 4.5
        tipx, tipy = cx + cos_a * 58, cy + sin_a * 58
        self.canvas.create_polygon(
            b1x, b1y, tipx, tipy, b2x, b2y,
            fill=blade_col, outline="#FFFFFF", width=1
        )
        self.canvas.create_line(
            gx2, gy2, cx + cos_a * 50, cy + sin_a * 50,
            fill="#FFFFFF", width=2
        )

    def draw_fighter(self, sx, sy, col, facing, phase, is_player, is_ally, tier):
        bob = math.sin(phase) * 2.2
        sy_b = sy + bob

        self.canvas.create_oval(
            sx - 18, sy + 10, sx + 18, sy + 22, fill="#14301B", outline=""
        )
        if is_ally:
            self.canvas.create_oval(
                sx - 24, sy - 24, sx + 24, sy + 24,
                outline="#38BDF8", width=2
            )
        elif tier >= 14:
            self.canvas.create_oval(
                sx - 23, sy_b - 23, sx + 23, sy_b + 23,
                outline=col, width=2
            )

        back_ang = facing + math.pi
        sway = math.sin(phase * 1.3) * 0.25
        c_left = back_ang - 0.55 + sway
        c_right = back_ang + 0.55 + sway
        cape_pts = [
            sx, sy_b,
            sx + math.cos(c_left) * 26, sy_b + math.sin(c_left) * 26,
            sx + math.cos(back_ang + sway) * 30,
            sy_b + math.sin(back_ang + sway) * 30,
            sx + math.cos(c_right) * 26, sy_b + math.sin(c_right) * 26,
        ]
        cape_col = "#1E293B" if not is_player else "#0F172A"
        self.canvas.create_polygon(cape_pts, fill=cape_col, outline=col, width=1)

        perp = facing + math.pi / 2
        for side in (-1, 1):
            px = sx + math.cos(perp) * 15 * side
            py = sy_b + math.sin(perp) * 15 * side
            self.canvas.create_oval(
                px - 7, py - 7, px + 7, py + 7,
                fill=col, outline="#111827", width=2
            )

        ring_col = "#FFFFFF" if is_player else "#111827"
        ring_w = 3 if is_player else 2
        self.canvas.create_oval(
            sx - 16, sy_b - 16, sx + 16, sy_b + 16,
            fill=col, outline=ring_col, width=ring_w
        )

        vx = sx + math.cos(facing) * 8
        vy = sy_b + math.sin(facing) * 8
        ex1 = vx + math.cos(perp) * 4
        ey1 = vy + math.sin(perp) * 4
        ex2 = vx - math.cos(perp) * 4
        ey2 = vy - math.sin(perp) * 4
        eye_col = "#38BDF8" if is_ally else "#FFFFFF"
        self.canvas.create_oval(
            ex1 - 2.5, ey1 - 2.5, ex1 + 2.5, ey1 + 2.5,
            fill=eye_col, outline=""
        )
        self.canvas.create_oval(
            ex2 - 2.5, ey2 - 2.5, ex2 + 2.5, ey2 + 2.5,
            fill=eye_col, outline=""
        )

    def draw(self):
        self.canvas.delete("all")

        ox, oy = 0.0, 0.0
        if self.shake_timer > 0:
            ox = random.uniform(-self.shake_mag, self.shake_mag)
            oy = random.uniform(-self.shake_mag, self.shake_mag)
        cam_x = self.px - WIDTH / 2 + ox
        cam_y = self.py - HEIGHT / 2 + oy

        # Checkerboard Grass Tiles
        tile = 120
        sx0 = int(cam_x // tile) * tile
        sy0 = int(cam_y // tile) * tile
        for gx in range(sx0, int(cam_x + WIDTH + tile), tile):
            for gy in range(sy0, int(cam_y + HEIGHT + tile), tile):
                if ((gx // tile) + (gy // tile)) % 2 == 0:
                    x1, y1 = gx - cam_x, gy - cam_y
                    self.canvas.create_rectangle(
                        x1, y1, x1 + tile, y1 + tile,
                        fill="#265230", outline=""
                    )

        # Central Sanctuary Stone Plaza
        mid = MAP_SIZE / 2
        px1, py1 = mid - 190 - cam_x, mid - 190 - cam_y
        px2, py2 = mid + 190 - cam_x, mid + 190 - cam_y
        if px2 >= 0 and px1 <= WIDTH and py2 >= 0 and py1 <= HEIGHT:
            self.canvas.create_oval(
                px1, py1, px2, py2,
                fill="#334155", outline="#FACC15", width=4
            )
            self.canvas.create_oval(
                px1 + 28, py1 + 28, px2 - 28, py2 - 28,
                outline="#64748B", width=2
            )

        # Map Border
        self.canvas.create_rectangle(
            -cam_x, -cam_y, MAP_SIZE - cam_x, MAP_SIZE - cam_y,
            outline="#0F2414", width=10
        )

        # Stones & Wildflowers
        for stx, sty, strad in self.stones:
            x, y = stx - cam_x, sty - cam_y
            if -30 <= x <= WIDTH + 30 and -30 <= y <= HEIGHT + 30:
                self.canvas.create_oval(
                    x - strad, y - strad * 0.7, x + strad, y + strad * 0.7,
                    fill="#475569", outline="#334155", width=2
                )

        for flx, fly, flc in self.flowers:
            x, y = flx - cam_x, fly - cam_y
            if -10 <= x <= WIDTH + 10 and -10 <= y <= HEIGHT + 10:
                self.canvas.create_oval(
                    x - 3, y - 3, x + 3, y + 3, fill=flc, outline=""
                )

        # Layered Trees
        for tx, ty, tr in self.trees:
            x, y = tx - cam_x, ty - cam_y
            if -60 <= x <= WIDTH + 60 and -60 <= y <= HEIGHT + 60:
                self.canvas.create_oval(
                    x - tr, y + 8 - tr * 0.7, x + tr, y + 8 + tr * 0.7,
                    fill="#132B18", outline=""
                )
                self.canvas.create_oval(
                    x - tr, y - tr, x + tr, y + tr,
                    fill="#1B3B22", outline="#122917", width=2
                )
                self.canvas.create_oval(
                    x - tr * 0.65, y - tr * 0.75, x + tr * 0.65, y + tr * 0.55,
                    fill="#265230", outline=""
                )

        # Shockwave Rings
        for rg in self.rings:
            x, y, r = rg["x"] - cam_x, rg["y"] - cam_y, rg["r"]
            self.canvas.create_oval(
                x - r, y - r, x + r, y + r, outline=rg["color"], width=3
            )

        # NPCs & Summoned Allies
        for npc in self.npcs:
            sx, sy = npc["x"] - cam_x, npc["y"] - cam_y
            if -100 <= sx <= WIDTH + 100 and -100 <= sy <= HEIGHT + 100:
                data = RARITIES[npc["rarity_idx"]]
                live_col = self.get_tier_color(npc["rarity_idx"])
                col = "#FFFFFF" if npc["hit_flash"] > 0 else live_col
                self.draw_sword(
                    sx, sy, npc["facing"], col,
                    npc["swing_timer"], 0.2, 1
                )
                self.draw_fighter(
                    sx, sy, col, npc["facing"], npc["walk_phase"],
                    False, npc["is_ally"], npc["rarity_idx"]
                )
                tag = "ALLY " if npc["is_ally"] else ""
                lbl = f"{tag}[{data['name']}] PWR:{format_num(npc['power'])}"
                self.canvas.create_text(
                    sx, sy - 41, text=lbl, fill=live_col,
                    font=("Arial", 10, "bold")
                )
                hp_r = max(0.0, npc["hp"] / npc["max_hp"])
                bar_c = "#38BDF8" if npc["is_ally"] else "#22C55E"
                self.canvas.create_rectangle(
                    sx - 24, sy - 31, sx + 24, sy - 26,
                    fill="#1F2937", outline=""
                )
                self.canvas.create_rectangle(
                    sx - 24, sy - 31, sx - 24 + 48 * hp_r, sy - 26,
                    fill=bar_c, outline=""
                )

        # Player & Player Sword
        cx, cy = WIDTH / 2, HEIGHT / 2
        p_data = RARITIES[self.rarity_idx]
        p_col = self.get_tier_color(self.rarity_idx)
        self.draw_sword(
            cx, cy, self.aim_angle, p_col,
            self.swing_timer, self.swing_dur, self.swing_dir
        )
        self.draw_fighter(
            cx, cy, p_col, self.aim_angle,
            self.walk_phase, True, False, self.rarity_idx
        )
        self.canvas.create_text(
            cx, cy - 32, text=f"YOU [{p_data['name']}]",
            fill=p_col, font=("Arial", 10, "bold")
        )

        # Sparks & Floating Popups
        for pt in self.particles:
            x, y = pt["x"] - cam_x, pt["y"] - cam_y
            sz = pt["size"] * (pt["life"] / pt["max_life"])
            self.canvas.create_oval(
                x - sz, y - sz, x + sz, y + sz, fill=pt["color"], outline=""
            )

        for p in self.popups:
            self.canvas.create_text(
                p["x"] - cam_x, p["y"] - cam_y, text=p["text"],
                fill=p["color"], font=("Arial", 11, "bold")
            )

        self.draw_hud(p_data, p_col)

    def draw_hud(self, p_data, p_col):
        self.canvas.create_rectangle(
            15, 12, 290, 186, fill="#0F172A", outline="#334155", width=2
        )
        xp_sec = 5 * self.multiplier
        t_num = self.rarity_idx + 1
        total_t = len(RARITIES)
        luck_val = self.get_luck_val()
        mult_str = f"Multiplier: {format_num(self.multiplier)}x"
        luck_str = f"Luck: {luck_val:.1f}x (Lvl {self.luck_level})"
        tier_str = f"Tier: {t_num}/{total_t} ({p_data['name']})"
        pwr_str = f"Sword Power: {format_num(p_data['power'])}"
        hp_str = f"HP: {format_num(self.hp)}/{format_num(self.max_hp)}"
        stats = [
            (29, mult_str, "#FACC15", 13),
            (51, f"Sacrifice Bonus: {self.prestige_mult}x", "#38BDF8", 11),
            (72, luck_str, "#34D399", 11),
            (93, tier_str, p_col, 11),
            (114, pwr_str, "#FFFFFF", 11),
            (135, f"XP / Sec: +{format_num(xp_sec)}", "#4ADE80", 11),
            (156, hp_str, "#F87171", 11),
        ]
        for y_pos, txt, col, fsz in stats:
            self.canvas.create_text(
                26, y_pos, anchor="w", text=txt, fill=col,
                font=("Arial", fsz, "bold")
            )

        if self.save_banner > 0:
            self.canvas.create_text(
                15, 198, anchor="w", text="● Progress Saved",
                fill="#4ADE80", font=("Arial", 10, "bold")
            )

        if self.announce_timer > 0:
            ann_col = (
                self.get_tier_color(self.announce_tier)
                if self.announce_tier is not None else self.announce_color
            )
            self.canvas.create_rectangle(
                WIDTH / 2 - 215, 14, WIDTH / 2 + 215, 52,
                fill="#0F172A", outline=ann_col, width=2
            )
            self.canvas.create_text(
                WIDTH / 2, 33, text=self.announce_text,
                fill=ann_col, font=("Arial", 11, "bold")
            )

        # Sacrifice Button (with 5s Cooldown)
        gain = p_data["rebirth_gain"] * self.prestige_mult
        t5_name = RARITIES[4]["name"]
        if self.sacrifice_cd > 0:
            sac_col = "#7F1D1D"
            sac_txt = f"SACRIFICE [R]\nCooldown: {self.sacrifice_cd:.1f}s"
        elif gain > 0:
            sac_col = "#B91C1C"
            sac_txt = f"SACRIFICE [R]\n(+{format_num(gain)}x Multiplier)"
        else:
            sac_col = "#334155"
            sac_txt = f"SACRIFICE\n(Need {t5_name} - Tier 5)"
        self.draw_btn(self.sac_rect, sac_col, sac_txt)

        # Prestige Button (+10K cost per prestige)
        p_cost = self.get_prestige_cost()
        can_p = self.multiplier >= p_cost
        p_col_btn = "#7E22CE" if can_p else "#334155"
        m_str = format_num(self.multiplier)
        c_str = format_num(p_cost)
        p_txt = (
            f"PRESTIGE [P]\n(Cost: {c_str} -> +1x Sac)"
            if can_p else f"PRESTIGE ({m_str}/{c_str})\n(+1x Sac Mult)"
        )
        self.draw_btn(self.pres_rect, p_col_btn, p_txt)

        # Luck Upgrade Button
        l_cost = self.get_luck_cost()
        next_l = self.get_luck_val(self.luck_level + 1)
        can_l = (self.multiplier - l_cost) >= 1
        l_col = "#059669" if can_l else "#334155"
        l_txt = (
            f"UPGRADE LUCK [L]\n"
            f"(-{format_num(l_cost)}x Mult -> {next_l:.1f}x)"
        )
        self.draw_btn(self.luck_rect, l_col, l_txt)

        # Summon Ability Button
        unlocked = self.rarity_idx >= 19
        if not unlocked:
            s_col, s_txt = "#334155", "SUMMON 4x [E]\n(Unlocks at Tier 20)"
        elif self.summon_cd > 0:
            s_col = "#1E3A8A"
            s_txt = f"SUMMON 4x [E]\nCooldown: {self.summon_cd:.1f}s"
        else:
            s_col, s_txt = "#0284C7", "SUMMON 4x [E]\n(Luck + Mult Allies)"
        self.draw_btn(self.sum_rect, s_col, s_txt)

        # Reset Progress Button
        rst_col = "#DC2626" if self.reset_confirm > 0 else "#475569"
        rst_txt = (
            "CLICK AGAIN TO CONFIRM!"
            if self.reset_confirm > 0 else "RESET PROGRESS"
        )
        self.draw_btn(self.rst_rect, rst_col, rst_txt)

        # Bottom Rarity XP Bar
        bar_w, bar_h = 620, 34
        bx1 = (WIDTH - bar_w) / 2
        by1 = HEIGHT - 52
        self.canvas.create_rectangle(
            bx1, by1, bx1 + bar_w, by1 + bar_h,
            fill="#0F172A", outline="#FFFFFF", width=2
        )

        if self.rarity_idx < len(RARITIES) - 1:
            nxt = RARITIES[self.rarity_idx + 1]
            ratio = min(1.0, self.xp / p_data["xp_req"])
            self.canvas.create_rectangle(
                bx1 + 2, by1 + 2, bx1 + 2 + (bar_w - 4) * ratio,
                by1 + bar_h - 2, fill=p_col, outline=""
            )
            b_txt = (
                f"[{t_num}/{total_t}] {p_data['name']} -> {nxt['name']}  |  "
                f"XP: {format_num(self.xp)} / {format_num(p_data['xp_req'])}"
            )
        else:
            self.canvas.create_rectangle(
                bx1 + 2, by1 + 2, bx1 + bar_w - 2, by1 + bar_h - 2,
                fill=p_col, outline=""
            )
            xp_s = format_num(self.xp)
            b_txt = f"MAX TIER [{total_t}/{total_t}]: {p_data['name']}  |  XP: {xp_s}"

        self.canvas.create_text(
            WIDTH / 2 + 1, by1 + bar_h / 2 + 1, text=b_txt,
            fill="#000000", font=("Arial", 11, "bold")
        )
        self.canvas.create_text(
            WIDTH / 2, by1 + bar_h / 2, text=b_txt,
            fill="#FFFFFF", font=("Arial", 11, "bold")
        )
        controls = (
            "WASD: Move | Click/Space: Slash | L: Luck | "
            "E: Summon | R: Sacrifice | P: Prestige"
        )
        self.canvas.create_text(
            WIDTH / 2, HEIGHT - 10, text=controls,
            fill="#CBD5E1", font=("Arial", 9)
        )

    def draw_btn(self, rect, fill_col, label):
        x1, y1, x2, y2 = rect
        self.canvas.create_rectangle(
            x1, y1, x2, y2, fill=fill_col, outline="#FFFFFF", width=2
        )
        self.canvas.create_text(
            (x1 + x2) / 2, (y1 + y2) / 2, text=label,
            fill="#FFFFFF", font=("Arial", 9, "bold"), justify="center"
        )

    def game_loop(self):
        now = time.time()
        dt = min(0.05, now - self.last_time)
        self.last_time = now

        self.update(dt)
        self.draw()
        self.root.after(16, self.game_loop)


if __name__ == "__main__":
    root = tk.Tk()
    root.lift()
    root.focus_force()
    game = RaritySwordGame(root)
    root.mainloop()