import random
import itertools

genome_counter = itertools.count()

class PokemonGenome:
    def __init__(self, base_pokemon_data, config_data: dict, random_init=True):
        self.genome_id = next(genome_counter)   # Unique genome identifier
        self.fitness = 0    # Overall fitness score
        self.shared_fitness = 0 # Fitness adjusted for species sharing
        
        self.config_data = config_data
        
        # Determine if this is a custom Pokemon
        self.is_custom = (base_pokemon_data.get('name') == "custom_god_pokemon")

        if self.is_custom:
            # create a custom Pokemon with random attributes, and use "Mewthree" name
            self.name = "Mewthree" 
            self.ability = None
            # Get data pools from config
            self.learnset = self.config_data['MOVE_POOL'] 
            
            self.stats = {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
            self.types = [] 
            self.moves = [] 
            
            if random_init:
                self._randomize_stats()
                self.types = random.sample(self.config_data['POKEMON_TYPES'], random.randint(1, 2))
                self.moves = random.sample(self.learnset, 4)
                self._randomize_evs()
                self.nature = random.choice(list(self.config_data['NATURES'].keys()))
                self.ability = random.choice(self.config_data['ABILITY_POOL'])
        else:
            self.name = base_pokemon_data['name']
            self.stats = base_pokemon_data['base_stats']
            self.types = base_pokemon_data['types']
            self.ability = base_pokemon_data['ability']
            self.learnset = base_pokemon_data['learnset']
            self.moves = [] 
            
            if random_init:
                self.moves = random.sample(self.learnset, min(4, len(self.learnset)))
                self._randomize_evs()
                self.nature = random.choice(list(self.config_data['NATURES'].keys()))
        
        # Ensure moves and types are sorted for consistency
        self.moves.sort()
        self.types.sort()


    def _normalize_dict(self, data_dict, max_sum):
        """Normalizes the values in data_dict so that they sum to max_sum"""
        current_sum = sum(data_dict.values())
        if current_sum == 0: 
            for key in data_dict:
                data_dict[key] = max_sum // len(data_dict)
            data_dict[random.choice(list(data_dict.keys()))] += max_sum % len(data_dict)
            return

        factor = max_sum / current_sum
        total_normalized_sum = 0
        for key in data_dict:
            data_dict[key] = max(1, int(data_dict[key] * factor))
            total_normalized_sum += data_dict[key]
        
        diff = max_sum - total_normalized_sum
        if diff > 0:
            for _ in range(diff):
                key_to_adjust = random.choice(list(data_dict.keys()))
                data_dict[key_to_adjust] += 1
        elif diff < 0:
            for _ in range(abs(diff)):
                possible_keys = [k for k, v in data_dict.items() if v > 1]
                if not possible_keys: break 
                key_to_adjust = random.choice(possible_keys)
                data_dict[key_to_adjust] -= 1

    def _randomize_stats(self):
        """Randomizes base stats to sum to MAX_BASE_STATS."""
        self.stats = {k: random.randint(1, 100) for k in self.stats.keys()}
        # Use config value
        self._normalize_dict(self.stats, self.config_data['MAX_BASE_STATS'])

    def _randomize_evs(self):
        """Creates a legal EV spread."""
        self.evs = {k: 0 for k in self.stats.keys()}
        keys = list(self.evs.keys())
        stat1, stat2 = random.sample(keys, 2)
        
        self.evs[stat1] = 252
        self.evs[stat2] = 252
        remaining_keys = [k for k in keys if k not in [stat1, stat2]]
        self.evs[random.choice(remaining_keys)] = 6

    def mutate(self):
        """Applies a random mutation to the evolvable parts of the genome."""
        evolvable_parts = ['evs', 'moves', 'nature']
        if self.is_custom:
            evolvable_parts.extend(['stats', 'types', 'ability'])
            
        mutation_type = random.choice(evolvable_parts)

        if mutation_type == 'stats':
            stat1, stat2 = random.sample(list(self.stats.keys()), 2)
            max_change = self.config_data.get('MUTATION_STAT_CHANGE_MAX', 20)
            change = random.randint(1, max_change)
            if self.stats[stat1] > change:
                self.stats[stat1] -= change
                self.stats[stat2] += change
        
        elif mutation_type == 'types':
            # Replace one type with a new random type
            if self.types:
                idx_to_replace = random.randint(0, len(self.types) - 1)
                new_type = random.choice([t for t in self.config_data['POKEMON_TYPES'] if t not in self.types])
                self.types[idx_to_replace] = new_type
            self.types.sort()

        elif mutation_type == 'evs':
            self._randomize_evs()

        elif mutation_type == 'moves':
            # Replace one move with a new move from the learnset
            if len(self.learnset) > 4:
                idx_to_replace = random.randint(0, 3)
                possible_new_moves = [m for m in self.learnset if m not in self.moves]
                if possible_new_moves:
                    self.moves[idx_to_replace] = random.choice(possible_new_moves)
            self.moves.sort()

        elif mutation_type == 'nature':
            # Use config value
            self.nature = random.choice(list(self.config_data['NATURES'].keys()))
        
        elif mutation_type == 'ability':
            # Find a new ability that is not the current one
            possible_new_abilities = [
                a for a in self.config_data['ABILITY_POOL'] if a != self.ability
            ]
            if possible_new_abilities:
                self.ability = random.choice(possible_new_abilities)

    def __str__(self):
        """String representation of the genome for easy debugging."""
        return (f"ID: {self.genome_id} | Name: {self.name.capitalize()}\n"
                f"Types: {self.types}\n"
                f"Stats: {self.stats}\n"
                f"EVs: {self.evs}\n"
                f"Nature: {self.nature}\n"
                f"Moves: {self.moves}\n"
                f"Fitness: {self.fitness:.2f} (Shared: {self.shared_fitness:.2f})")