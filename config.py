# config.py

# --- Evolution Mode Parameters ---
# These parameters control the NEAT-style speciation process.

# Controls the "barrier" between species. Any two genomes with a compatibility
# distance *below* this value are considered the same species.
# **Higher Value**: Creates FEWER, broader, more diverse species.
# **Lower Value**: Creates MORE, specific, niche species.
COMPATIBILITY_THRESHOLD = 2.5

# The "patience" of the algorithm. If a species' best fitness does not
# improve for this many generations, it's considered "stagnant" and
# will be removed (unless it's the last species).
# **Higher Value**: Protects species longer, letting them explore.
# **Lower Value**: Culls underperforming species quickly, focusing on success.
STAGNATION_LIMIT = 15

# Controls the "selection pressure" *within* a species. After each
# generation, only this percentage (e.g., 0.4 = 40%) of the *best*
# genomes in that species survive to reproduce.
# **Higher Value**: Low pressure. Keeps more genetic diversity (and weak genomes).
# **Lower Value**: High pressure. Only the elite survive, leading to faster
# optimization but a higher risk of getting stuck in a local optimum.
SURVIVAL_THRESHOLD = 0.4

# --- NEAT Compatibility Coefficients ---
# These C-values are *multipliers* in the compatibility distance formula.
# They define **what "similar" means** when deciding if two genomes
# belong in the same species. They are the *most important* levers for
# shaping how the population explores the search space.

# How much do differences in **base stats** matter? (Custom 'Mewthree' only)
# **Higher Value**: Separates physical attackers (high Atk) from special
# attackers (high SpA) into *different species* very quickly.
C1_STATS = 1.0

# How much do differences in **types** matter? (Custom 'Mewthree' only)
# **Higher Value**: Makes 'Fire/Steel' and 'Fire/Ground' very different,
# encouraging the creation of a new species for each type combo.
C2_TYPES = 1.0

# How much do differences in **movesets** matter?
# **Higher Value**: A genome with 'Swords Dance' and 'Recover' will be
# seen as *very different* from one with four attack moves. This helps
# separate "roles" (e.g., stall vs. sweeper) into different species.
C3_MOVES = 0.5

# How much do differences in **EV spreads** matter?
# **(Set to 0)**: Currently, EV spreads *do not* influence speciation.
# The algorithm assumes EVs are for fine-tuning *within* a species.
C4_EVS = 0.0

# How much do differences in **nature** matter?
# **(Set to 0)**: Currently, nature *does not* influence speciation.
# An 'Adamant' genome is considered the same as a 'Modest' one
# for speciation purposes.
C5_NATURE = 0.0

# How much do differences in **ability** matter?
# **Higher Value**: Creates a new species for different key abilities
# (e.g., separates a 'Levitate' genome from an 'Intimidate' one).
C6_ABILITY = 0.5


# --- Evolutionary Algorithm Parameters ---

# The "look-ahead" for the 'Advanced Mode' (Minimax) AI.
# **Depth 1**: "What's my best move *right now*?" (Fast, but weak).
# **Depth 2**: "What's my best move *after* I see their best reply?" (Smarter).
# **Depth 3+**: Becomes *exponentially* slower. Depth 2 is a good balance.
MINIMAX_DEPTH = 2

# Total number of "individuals" in the entire gene pool, distributed
# across all species.
# **Higher Value**: Explores *more* options at once and is less likely
# to get stuck. Each generation takes *much longer* to evaluate.
# **Lower Value**: Faster generations, but higher risk of losing good
# genetic diversity or getting stuck on a suboptimal solution.
POPULATION_SIZE = 75

# The total number of cycles (evaluate, cull, reproduce) the algorithm
# will run. This is the main "timer" for the entire experiment.
GENERATIONS = 100

# The chance (e.g., 0.3 = 30%) that a new child genome will have a
# *random change* (e.g., new move, different EVs, mutated stats).
# **Higher Value**: More chaos and new ideas. Good for exploration,
# but can prevent the algorithm from "settling" on a good solution.
# **Lower Value**: More focus on fine-tuning existing solutions.
MUTATION_RATE = 0.3

# When a 'stats' mutation occurs (for custom 'Mewthree'), this is the
# max number of points moved from one random stat to another.
# **Higher Value**: Faster, more drastic changes to stat builds.
# **Lower Value**: Slower, more careful fine-tuning of stat builds.
MUTATION_STAT_CHANGE_MAX = 20

# The number of best genomes *per species* that are carried into the
# next generation *unchanged* (no mutation, no crossover).
# **Value of 1**: Standard. Guarantees the species' "champion" always
# survives, ensuring fitness never *decreases* in a species.
ELITISM_COUNT = 1

# A performance-tuning knob. This sets how many fitness evaluations
# (which involve running multiple battles) to run in *parallel*.
# **Higher Value**: Faster generations, *if* your CPU has enough cores.
# **Lower Value**: Safer, runs fewer things at once.
MAX_CONCURRENT_EVALUATIONS = 6

# --- Pokémon Constraints ---
# These are the "rules of the game" that all genomes must follow.

# The "Base Stat Total" (BST) for custom 'Mewthree' genomes.
# All base stats (HP, Atk, Def, etc.) must sum to this value.
# This defines the "power level" of the created Pokémon.
MAX_BASE_STATS = 600

# The "legal" limit for total EVs in competitive Pokémon.
# The algorithm will ensure all EV spreads sum to this value or less.
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

# missing "Fairy" type added in later generations
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

# A pool of viable abilities for 'Mewthree' to evolve.
# This list excludes 'Wonder Guard' to prevent trivial, invincible solutions
# (e.g., a Dark/Ghost type with it).
ABILITY_POOL = [
    "Stench", "Drizzle", "Speed-Boost", "Battle-Armor", "Sturdy", "Damp", "Limber", 
    "Sand-Veil", "Static", "Volt-Absorb", "Water-Absorb", "Oblivious", "Cloud-Nine", 
    "Compound-Eyes", "Insomnia", "Color-Change", "Immunity", "Flash-Fire", 
    "Shield-Dust", "Own-Tempo", "Suction-Cups", "Intimidate", "Shadow-Tag", 
    "Rough-Skin", "Levitate", "Effect-Spore", "Synchronize", "Clear-Body", 
    "Natural-Cure", "Lightning-Rod", "Serene-Grace", "Swift-Swim", "Chlorophyll", 
    "Illuminate", "Trace", "Huge-Power", "Poison-Point", "Inner-Focus", 
    "Magma-Armor", "Water-Veil", "Magnet-Pull", "Soundproof", "Rain-Dish", 
    "Sand-Stream", "Pressure", "Thick-Fat", "Early-Bird", "Flame-Body", "Run-Away", 
    "Keen-Eye", "Hyper-Cutter", "Pickup", "Truant", "Hustle", "Cute-Charm", "Plus", 
    "Minus", "Forecast", "Sticky-Hold", "Shed-Skin", "Guts", "Marvel-Scale", 
    "Liquid-Ooze", "Overgrow", "Blaze", "Torrent", "Swarm", "Rock-Head", "Drought", 
    "Arena-Trap", "Vital-Spirit", "White-Smoke", "Pure-Power", "Shell-Armor", 
    "Air-Lock", "Tangled-Feet", "Motor-Drive", "Rivalry", "Steadfast", "Snow-Cloak", 
    "Gluttony", "Anger-Point", "Unburden", "Heatproof", "Simple", "Dry-Skin", 
    "Download", "Iron-Fist", "Poison-Heal", "Adaptability", "Skill-Link", "Hydration", 
    "Solar-Power", "Quick-Feet", "Normalize", "Sniper", "Magic-Guard", "No-Guard", 
    "Stall", "Technician", "Leaf-Guard", "Klutz", "Mold-Breaker", "Super-Luck", 
    "Aftermath", "Anticipation", "Forewarn", "Unaware", "Tinted-Lens", "Filter", 
    "Slow-Start", "Scrappy", "Storm-Drain", "Ice-Body", "Solid-Rock", "Snow-Warning", 
    "Honey-Gather", "Frisk", "Reckless", "Multitype", "Flower-Gift"
]

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
# This is useful for simple mode (with Max-Damage AI).
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


# --- Extension for the base gauntlets with more Pokémon from Gen I-IV ---
GAUNTLET.extend([
    {
        "name": "Metagross", "moves": ["iron-head", "earthquake", "bullet-punch", "stealth-rock"],
        "ability": "clear-body", "evs": "252 HP / 252 Atk / 6 Def", "nature": "Adamant"
    },
    {
        "name": "Latias", "moves": ["dragon-pulse", "psychic", "calm-mind", "recover"],
        "ability": "levitate", "evs": "252 HP / 6 SpA / 252 Spe", "nature": "Timid"
    },
    {
        "name": "Gyarados", "moves": ["dragon-dance", "waterfall", "stone-edge", "earthquake"],
        "ability": "intimidate", "evs": "252 Atk / 6 Def / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Swampert", "moves": ["earthquake", "waterfall", "stealth-rock", "ice-beam"],
        "ability": "torrent", "evs": "252 HP / 252 Atk / 6 Def", "nature": "Adamant"
    },
    {
        "name": "Zapdos", "moves": ["thunderbolt", "ice-beam", "roost", "u-turn"],
        "ability": "pressure", "evs": "252 SpA / 6 SpD / 252 Spe", "nature": "Timid"
    },
    {
        "name": "Breloom", "moves": ["sleep-powder", "substitute", "leech-seed", "brick-break"],
        "ability": "effect-spore", "evs": "252 HP / 6 Def / 252 SpD", "nature": "Careful"
    },
    {
        "name": "Snorlax", "moves": ["bulk-up", "return", "earthquake", "fire-punch"],
        "ability": "thick-fat", "evs": "252 HP / 6 Atk / 252 SpD", "nature": "Careful"
    },
    {
        "name": "Jirachi", "moves": ["iron-head", "stun-spore", "wish", "u-turn"],
        "ability": "serene-grace", "evs": "252 HP / 220 SpD / 36 Spe", "nature": "Careful"
    },
    {
        "name": "Starmie", "moves": ["surf", "ice-beam", "thunderbolt", "recover"],
        "ability": "natural-cure", "evs": "252 SpA / 6 SpD / 252 Spe", "nature": "Timid"
    },
    {
        "name": "Gliscor", "moves": ["swords-dance", "earthquake", "stone-edge", "roost"],
        "ability": "hyper-cutter", "evs": "252 Atk / 6 Def / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Infernape", "moves": ["stealth-rock", "close-combat", "fire-blast", "u-turn"],
        "ability": "blaze", "evs": "6 Atk / 252 SpA / 252 Spe", "nature": "Naive"
    }
])

SIMPLE_GAUNTLET.extend([
    {
        "name": "Metagross", "moves": ["iron-head", "earthquake", "ice-punch", "thunder-punch"],
        "ability": "clear-body", "evs": "252 HP / 252 Atk / 6 Def", "nature": "Adamant"
    },
    {
        "name": "Latias", "moves": ["dragon-pulse", "psychic", "surf", "ice-beam"],
        "ability": "levitate", "evs": "252 SpA / 6 SpD / 252 Spe", "nature": "Timid"
    },
    {
        "name": "Gyarados", "moves": ["waterfall", "stone-edge", "earthquake", "iron-head"],
        "ability": "intimidate", "evs": "252 Atk / 6 Def / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Swampert", "moves": ["earthquake", "waterfall", "ice-punch", "stone-edge"],
        "ability": "torrent", "evs": "252 HP / 252 Atk / 6 Def", "nature": "Adamant"
    },
    {
        "name": "Zapdos", "moves": ["thunderbolt", "ice-beam", "dragon-pulse", "shadow-ball"],
        "ability": "pressure", "evs": "252 SpA / 6 SpD / 252 Spe", "nature": "Timid"
    },
    {
        "name": "Breloom", "moves": ["close-combat", "stone-edge", "facade", "giga-drain"],
        "ability": "effect-spore", "evs": "252 Atk / 6 Def / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Snorlax", "moves": ["return", "earthquake", "crunch", "fire-punch"],
        "ability": "thick-fat", "evs": "252 HP / 252 Atk / 6 SpD", "nature": "Adamant"
    },
    {
        "name": "Jirachi", "moves": ["iron-head", "ice-punch", "fire-punch", "thunder-punch"],
        "ability": "serene-grace", "evs": "252 Atk / 6 Def / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Starmie", "moves": ["surf", "ice-beam", "thunderbolt", "psychic"],
        "ability": "natural-cure", "evs": "252 SpA / 6 SpD / 252 Spe", "nature": "Timid"
    },
    {
        "name": "Gliscor", "moves": ["earthquake", "stone-edge", "u-turn", "crunch"],
        "ability": "hyper-cutter", "evs": "252 Atk / 6 Def / 252 Spe", "nature": "Jolly"
    },
    {
        "name": "Infernape", "moves": ["fire-blast", "focus-blast", "grass-knot", "dark-pulse"],
        "ability": "blaze", "evs": "252 SpA / 6 SpD / 252 Spe", "nature": "Timid"
    }
])