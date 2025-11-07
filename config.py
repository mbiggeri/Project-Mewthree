# config.py

# --- Evolution Mode Parameters ---
# These are the new parameters for the NEAT (speciation) algorithm
COMPATIBILITY_THRESHOLD = 4.0 # How different genomes must be to be in different species
STAGNATION_LIMIT = 5          # Generations a species can go without improvement
SURVIVAL_THRESHOLD = 0.4      # Percentage of a species to keep for reproduction

# --- NEAT Compatibility Coefficients ---
# These weigh the importance of each genomic difference
C1_STATS = 1.0       # Weight for base stat differences (custom only)
C2_TYPES = 1.0       # Weight for type differences (custom only)
C3_MOVES = 0.8       # Weight for move differences
C4_EVS = 0.5         # Weight for EV differences
C5_NATURE = 0.2      # Weight for nature difference


# --- Evolutionary Algorithm Parameters ---
MINIMAX_DEPTH = 2
POPULATION_SIZE = 20
GENERATIONS = 10
MUTATION_RATE = 0.3
ELITISM_COUNT = 1  # How many of the best individuals to carry over directly (NOW PER-SPECIES)
MAX_CONCURRENT_EVALUATIONS = 6  # Limit concurrent battles to avoid overwhelming the server

# --- Pokémon Constraints ---
MAX_BASE_STATS = 600
MAX_EVS = 510

# --- Pokémon Data Pools ---
MOVE_POOL = [
    "superpower", "close-combat", "dragon-claw", "earthquake",
    "facade", "flare-blitz", "giga-drain", "ice-beam", "iron-head",
    "shadow-claw", "shadow-ball", "stealth-rock", "surf",
    "swords-dance", "thunderbolt", "u-turn", "discharge", "will-o-wisp",
    "stone-edge", "waterfall", "crunch", "poison-jab", "sucker-punch",
    "bullet-punch", "aqua-jet", "return", "brick-break", "rock-slide",
    "fire-punch", "ice-punch", "thunder-punch",
    "flamethrower", "fire-blast", "hydro-pump", "focus-blast", "energy-ball",
    "psychic", "dark-pulse", "dragon-pulse", "aura-sphere", "grass-knot",
    "sludge-bomb", "power-gem",
    "toxic", "protect", "recover", "roost", "calm-mind", "dragon-dance",
    "nasty-plot", "bulk-up", "taunt", "spikes", "toxic-spikes", "wish",
    "substitute", "leech-seed", "sleep-powder", "stun-spore"
]

POKEMON_TYPES = [
    "normal", "fire", "water", "grass", "electric", "ice", "fighting",
    "poison", "ground", "flying", "psychic", "bug", "rock", "ghost",
    "dragon", "dark", "steel"
]

NATURES = {
    "Adamant": ("atk", "spa"), "Bashful": (None, None), "Bold": ("def", "atk"),
    "Brave": ("atk", "spe"), "Calm": ("spd", "atk"), "Careful": ("spd", "spa"),
    "Docile": (None, None), "Gentle": ("spd", "def"), "Hardy": (None, None),
    "Hasty": ("spe", "def"), "Impish": ("def", "spa"), "Jolly": ("spe", "spa"),
    "Lax": ("def", "spd"), "Lonely": ("atk", "def"), "Mild": ("spa", "def"),
    "Modest": ("spa", "atk"), "Naive": ("spe", "spd"), "Naughty": ("atk", "spd"),
    "Quiet": ("spa", "spe"), "Quirky": (None, None), "Rash": ("spa", "spd"),
    "Relaxed": ("def", "spe"), "Sassy": ("spd", "spe"), "Serious": (None, None),
    "Timid": ("spe", "atk")
}

# The gauntlet of strong opponents our Pokémon must beat.
GAUNTLET = [
    # --- Advanced Gauntlet (with status/setup) ---
    {
        "name": "Garchomp", "moves": ["earthquake", "dragon-claw", "swords-dance", "stealth-rock"],
        "ability": "sand-veil", "evs": "252 Atk / 6 SpD / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Gengar", "moves": ["shadow-ball", "focus-blast", "u-turn", "thunderbolt"],
        "ability": "levitate", "evs": "252 SpA / 6 SpD / 252 Spe", "nature": "Timid"
    },
    {
        "name": "Scizor", "moves": ["bullet-punch", "swords-dance", "roost", "u-turn"],
        "ability": "technician", "evs": "248 HP / 252 Atk / 8 SpD", "nature": "Adamant"
    },
    {
        "name": "Heatran", "moves": ["lava-plume", "earth-power", "stealth-rock", "protect"],
        "ability": "flash-fire", "evs": "252 HP / 6 SpA / 252 SpD", "nature": "Calm"
    },
    {
        "name": "Salamence", "moves": ["dragon-dance", "dragon-claw", "earthquake", "roost"],
        "ability": "intimidate", "evs": "252 Atk / 6 Def / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Blissey", "moves": ["seismic-toss", "toxic", "soft-boiled", "protect"],
        "ability": "natural-cure", "evs": "252 HP / 252 Def / 6 SpD", "nature": "Bold"
    },
    {
        "name": "Tyranitar", "moves": ["stone-edge", "crunch", "earthquake", "dragon-dance"],
        "ability": "sand-stream", "evs": "252 Atk / 6 SpD / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Lucario", "moves": ["close-combat", "swords-dance", "extreme-speed", "iron-head"],
        "ability": "inner-focus", "evs": "252 Atk / 6 SpD / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "rotom", "moves": ["hydro-pump", "thunderbolt", "will-o-wisp", "shadow-ball"],
        "ability": "levitate", "evs": "252 HP / 252 SpA / 6 Spe", "nature": "Modest"
    }
]

# --- Simple Gauntlet ---
# The same Pokémon, but with all-out-attacker movesets
# No status moves, no boosting moves, no hazard moves.
SIMPLE_GAUNTLET = [
    {
        "name": "Garchomp", "moves": ["earthquake", "dragon-claw", "stone-edge", "fire-fang"],
        "ability": "sand-veil", "evs": "252 Atk / 6 SpD / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Gengar", "moves": ["shadow-ball", "focus-blast", "sludge-bomb", "thunderbolt"],
        "ability": "levitate", "evs": "252 SpA / 6 SpD / 252 Spe", "nature": "Timid"
    },
    {
        "name": "Scizor", "moves": ["bullet-punch", "bug-bite", "superpower", "u-turn"],
        "ability": "technician", "evs": "248 HP / 252 Atk / 8 SpD", "nature": "Adamant"
    },
    {
        "name": "Heatran", "moves": ["lava-plume", "earth-power", "flash-cannon", "dark-pulse"],
        "ability": "flash-fire", "evs": "252 HP / 252 SpA / 6 SpD", "nature": "Modest"
    },
    {
        "name": "Salamence", "moves": ["dragon-claw", "earthquake", "fire-blast", "hydro-pump"],
        "ability": "intimidate", "evs": "252 Atk / 6 Def / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Blissey", "moves": ["ice-beam", "thunderbolt", "flamethrower", "shadow-ball"],
        "ability": "natural-cure", "evs": "252 HP / 252 Def / 6 SpA", "nature": "Modest"
    },
    {
        "name": "Tyranitar", "moves": ["stone-edge", "crunch", "earthquake", "superpower"],
        "ability": "sand-stream", "evs": "252 Atk / 6 SpD / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Lucario", "moves": ["close-combat", "shadow-claw", "stone-edge", "iron-head"],
        "ability": "inner-focus", "evs": "252 Atk / 6 SpD / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "rotom", "moves": ["hydro-pump", "thunderbolt", "overheat", "shadow-ball"],
        "ability": "levitate", "evs": "252 HP / 252 SpA / 6 Spe", "nature": "Modest"
    }
]