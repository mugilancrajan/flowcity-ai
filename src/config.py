# =============================================================================
# SIMULATION TIME
# =============================================================================

# Total ticks in one full 24-hour simulated day
TICKS_PER_DAY = 28_800

# How many ticks equal one simulated minute
TICKS_PER_SIMULATED_MINUTE = 20

# Simulation starts at tick 0 = 12:00 AM
# Time of day = (tick % TICKS_PER_DAY) / TICKS_PER_SIMULATED_MINUTE minutes

# =============================================================================
# SIMULATION SPEED
# =============================================================================

# How many ticks advance per real second at each speed setting
SPEED_SLOW   = 24    # 10 minute day
SPEED_NORMAL = 48    # 5 minute day
SPEED_FAST   = 96    # 2.5 minute day
SPEED_ULTRA  = 240   # 1 minute day

# Default speed setting on simulation start
DEFAULT_SPEED = SPEED_NORMAL

# =============================================================================
# VEHICLE MOVEMENT
# =============================================================================

# Converts integer speed limits to tiles per tick
# speed_limit 1 (25 MPH) * scale = 0.02 tiles/tick
# speed_limit 4 (75 MPH) * scale = 0.08 tiles/tick
MOVEMENT_SCALE = 0.02

# Speed limit to MPH display mapping (for UI only)
SPEED_LIMIT_TO_MPH = {
    1: 35,
    2: 50,
    3: 65,
    4: 80,
}

# =============================================================================
# METRICS
# =============================================================================

# How often a full MetricsSnapshot is taken (every N ticks)
METRICS_SNAPSHOT_INTERVAL = 10

# =============================================================================
# TIME PERIODS
# =============================================================================

# Each period defined by start tick (inclusive)
# Tick to simulated hour = (tick % TICKS_PER_DAY) / 1200

TIME_PERIODS = {
    "early_morning": {
        "start_tick": 0,         # 12:00 AM
        "end_tick": 7_199,       # 5:59 AM
    },
    "morning_rush": {
        "start_tick": 7_200,     # 6:00 AM
        "end_tick": 10_799,      # 8:59 AM
    },
    "midday": {
        "start_tick": 10_800,    # 9:00 AM
        "end_tick": 19_199,      # 3:59 PM
    },
    "evening_rush": {
        "start_tick": 19_200,    # 4:00 PM
        "end_tick": 22_799,      # 6:59 PM
    },
    "night": {
        "start_tick": 22_800,    # 7:00 PM
        "end_tick": 28_799,      # 11:59 PM
    }
}

# =============================================================================
# SPAWN RATES
# =============================================================================

# Vehicles spawned per simulated minute per period
SPAWN_RATES = {
    "early_morning": 1,
    "morning_rush":  8,
    "midday":        3,
    "evening_rush":  8,
    "night":         1,
}

# Origin/destination zone weights per period
# Format: {(origin_type, destination_type): weight}
# Zone types match TileType names: residential, commercial, workplace
SPAWN_ZONE_WEIGHTS = {
    "early_morning": {
        ("residential", "workplace"):   3,
        ("residential", "commercial"):  1,
        ("workplace",   "residential"): 1,
    },
    "morning_rush": {
        ("residential", "workplace"):   8,
        ("residential", "commercial"):  2,
        ("workplace",   "residential"): 1,
    },
    "midday": {
        ("residential", "commercial"):  3,
        ("commercial",  "residential"): 3,
        ("workplace",   "commercial"):  2,
        ("commercial",  "workplace"):   2,
    },
    "evening_rush": {
        ("workplace",   "residential"): 8,
        ("commercial",  "residential"): 2,
        ("residential", "workplace"):   1,
    },
    "night": {
        ("workplace",   "residential"): 2,
        ("commercial",  "residential"): 2,
        ("residential", "commercial"):  1,
    }
}

# =============================================================================
# WINDOW
# =============================================================================
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
UI_PANEL_WIDTH = 300
DEFAULT_GRID_COLS = 20
DEFAULT_GRID_ROWS = 15
FPS = 60

# =============================================================================
# COLORS — TILES
# =============================================================================
COLOR_EMPTY         = (26,  26,  46)
COLOR_ROAD          = (74,  74,  74)
COLOR_HIGHWAY       = (42,  42,  42)
COLOR_RESIDENTIAL   = (74,  124, 89)
COLOR_COMMERCIAL    = (74,  111, 165)
COLOR_WORKPLACE     = (193, 127, 36)

# =============================================================================
# COLORS — VEHICLES
# =============================================================================
COLOR_VEHICLE_CONSERVATIVE = (70,  130, 180)
COLOR_VEHICLE_NORMAL       = (220, 220, 220)
COLOR_VEHICLE_AGGRESSIVE   = (255, 140, 0)
COLOR_VEHICLE_RECKLESS     = (200, 50,  50)

# =============================================================================
# COLORS — UI
# =============================================================================
COLOR_UI_BACKGROUND    = (20,  20,  35)
COLOR_UI_ACCENT        = (80,  80,  120)
COLOR_GRID_LINE        = (65,  65,  90)
COLOR_SELECTION        = (255, 255, 100)
COLOR_HIGHLIGHT_PATH   = (255, 255, 0)
COLOR_HIGHLIGHT_CONGESTION = (255, 0, 0)
COLOR_TEXT_PRIMARY     = (220, 220, 220)
COLOR_TEXT_SECONDARY   = (140, 140, 160)

# =============================================================================
# TRANSITION
# =============================================================================
TRANSITION_DURATION_MS = 400

# =============================================================================
# CHART
# =============================================================================
CHART_REFRESH_INTERVAL = 50

# =============================================================================
# EDIT MODE UI
# =============================================================================

# Tool modes
TOOL_PAINT  = "paint"
TOOL_SELECT = "select"

# Tile palette entries — (TileType name, display label)
# Order determines grid layout (2 columns, top to bottom)
PALETTE_TILE_ENTRIES = [
    ("empty",       "Empty"),
    ("road",        "Road"),
    ("highway",     "Highway"),
    ("residential", "Residential"),
    ("commercial",  "Commercial"),
    ("workplace",   "Workplace"),
]

# Traffic control palette entries — (TrafficControl name, display label)
PALETTE_TRAFFIC_ENTRIES = [
    ("none",          "None"),
    ("stop_sign",     "Stop Sign"),
    ("traffic_light", "Traffic Light"),
]

# Speed limit popup
COLOR_POPUP_BG     = (30,  30,  50)
COLOR_POPUP_BORDER = (120, 120, 180)

# Hover shadow alpha (0-255)
HOVER_SHADOW_ALPHA = 80

# Selection rectangle — fill is RGBA (4-channel), border is RGB
COLOR_SELECTION_FILL   = (255, 255, 100, 40)
COLOR_SELECTION_BORDER = (255, 255, 100)

# =============================================================================
# SIMULATE MODE
# =============================================================================

# Playback speed multipliers — (tick multiplier, display label)
SIMULATE_SPEEDS = [
    (1,  "1x"),
    (2,  "2x"),
    (4,  "4x"),
    (8,  "8x"),
]

# Vehicle rendering
VEHICLE_SIZE_FRACTION    = 0.38  # legacy — used for hit-detection only (app.py)
VEHICLE_LENGTH_FRACTION  = 0.72  # car body length as fraction of tile size
VEHICLE_WIDTH_FRACTION   = 0.40  # car body width  as fraction of tile size
VEHICLE_ROAD_OFFSET      = 0.25  # perpendicular offset from tile centre (tiles) — 0.25 = lane centre of a 2-lane road
VEHICLE_MIN_GAP          = 0.85  # minimum centre-to-centre following gap (tiles); must be > VEHICLE_LENGTH_FRACTION to prevent sprite overlap

# Vehicle archetype base colors — keyed by VehicleArchetype enum
from src.vehicle.vehicle import VehicleArchetype
ARCHETYPE_COLORS = {
    VehicleArchetype.conservative: COLOR_VEHICLE_CONSERVATIVE,
    VehicleArchetype.normal:       COLOR_VEHICLE_NORMAL,
    VehicleArchetype.aggressive:   COLOR_VEHICLE_AGGRESSIVE,
    VehicleArchetype.reckless:     COLOR_VEHICLE_RECKLESS,
}

# Vehicle archetype behaviour — tune these to change driving personalities.
# speed_range: (min, max) multiplier applied on top of the tile speed limit.
# following_range: (min, max) safe-follow distance in tiles.
# weight: relative spawn probability across archetypes.
ARCHETYPE_CONFIGS = {
    VehicleArchetype.conservative: {
        "speed_range":     (0.75, 0.95),
        "following_range": (1.75, 2.5),
        "weight":          20,
        "accel_mult":      0.7,   # gentle throttle — slow to get up to speed
        "decel_mult":      0.8,   # gradual braking — comfortable stops
        "corner_fraction": 0.35,  # slows to 35% of desired speed at corner apex
        "speed_noise":     0.02,  # ±2% random jitter per tick
    },
    VehicleArchetype.normal: {
        "speed_range":     (0.85, 1.15),
        "following_range": (1.0, 2.0),
        "weight":          50,
        "accel_mult":      1.0,
        "decel_mult":      1.0,
        "corner_fraction": 0.55,
        "speed_noise":     0.04,
    },
    VehicleArchetype.aggressive: {
        "speed_range":     (1.1, 1.35),
        "following_range": (0.5, 1.0),
        "weight":          20,
        "accel_mult":      1.4,   # rapid throttle response
        "decel_mult":      1.3,   # firm late braking
        "corner_fraction": 0.75,  # barely slows for corners
        "speed_noise":     0.06,
    },
    VehicleArchetype.reckless: {
        "speed_range":     (1.3, 1.6),
        "following_range": (0.1, 0.5),
        "weight":          10,
        "accel_mult":      1.8,   # aggressive acceleration
        "decel_mult":      1.6,   # hard late braking
        "corner_fraction": 0.90,  # takes corners at nearly full speed
        "speed_noise":     0.08,
    },
}

# Congestion marker border color
COLOR_CONGESTION_MARKER = (255, 60, 60)

# Vehicle inspector popup dimensions
INSPECTOR_WIDTH  = 200
INSPECTOR_HEIGHT = 160

# Chart rolling window — number of snapshots to show
CHART_WINDOW = 200

# =============================================================================
# VEHICLE PHYSICS — tune here, applied in simulation_engine.py
# =============================================================================

# Corner deceleration: vehicles slow when a turn is ahead in the path.
CORNER_DECEL_DISTANCE = 1.2   # tiles before the corner waypoint to start braking
CORNER_SPEED_FRACTION = 0.55  # target speed fraction at the corner apex (0-1)

# Traffic lights: all signals share a global phase based on tick count.
# Horizontal (E/W) traffic gets the first half of the cycle as green;
# vertical (N/S) traffic gets the second half.
TRAFFIC_LIGHT_CYCLE       = 120  # ticks per full signal cycle
TRAFFIC_LIGHT_GREEN_TICKS = 60   # ticks spent green per cycle per direction

# Stop signs: vehicle comes to a full stop for this many ticks, then goes.
STOP_SIGN_WAIT_TICKS = 20