# =============================================================================
# SIMULATION TIME
# =============================================================================

# Total ticks in one full 24-hour simulated day
TICKS_PER_DAY = 14_400

# How many ticks equal one simulated minute
TICKS_PER_SIMULATED_MINUTE = 10

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
# speed_limit 1 (25 MPH) * scale = 0.05 tiles/tick
# speed_limit 4 (75 MPH) * scale = 0.20 tiles/tick
MOVEMENT_SCALE = 0.05

# Speed limit to MPH display mapping (for UI only)
SPEED_LIMIT_TO_MPH = {
    1: 25,
    2: 45,
    3: 60,
    4: 75
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
# Tick to simulated hour = (tick % TICKS_PER_DAY) / 600

TIME_PERIODS = {
    "early_morning": {
        "start_tick": 0,        # 12:00 AM
        "end_tick": 3_599,      # 5:59 AM
    },
    "morning_rush": {
        "start_tick": 3_600,    # 6:00 AM
        "end_tick": 5_399,      # 8:59 AM
    },
    "midday": {
        "start_tick": 5_400,    # 9:00 AM
        "end_tick": 9_599,      # 3:59 PM
    },
    "evening_rush": {
        "start_tick": 9_600,    # 4:00 PM
        "end_tick": 11_399,     # 6:59 PM
    },
    "night": {
        "start_tick": 11_400,   # 7:00 PM
        "end_tick": 14_399,     # 11:59 PM
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