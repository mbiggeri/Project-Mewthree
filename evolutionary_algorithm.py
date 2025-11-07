import random
import asyncio
import copy
import math
from pokemon_genome import PokemonGenome
from battle_evaluator import evaluate_fitness

class Species:
    def __init__(self, representative: PokemonGenome):
        self.representative = copy.deepcopy(representative)
        self.genomes = [representative]
        self.best_fitness = representative.fitness
        self.generations_stagnant = 0
        self.offspring_to_spawn = 0
    def add_genome(self, genome: PokemonGenome):
        self.genomes.append(genome)
    def get_best_genome(self) -> PokemonGenome:
        return max(self.genomes, key=lambda g: g.fitness)
    def update_stagnation(self):
        current_best_fitness = self.get_best_genome().fitness
        if current_best_fitness > self.best_fitness:
            self.best_fitness = current_best_fitness
            self.generations_stagnant = 0
        else:
            self.generations_stagnant += 1
    def calculate_shared_fitness(self):
        if not self.genomes: return
        n = len(self.genomes)
        for genome in self.genomes:
            genome.shared_fitness = genome.fitness / n
    def cull(self, survival_threshold):
        if not self.genomes: return
        self.genomes.sort(key=lambda g: g.shared_fitness, reverse=True)
        survivors_count = max(1, math.ceil(len(self.genomes) * survival_threshold))
        self.genomes = self.genomes[:survivors_count]
    def select_parent(self) -> PokemonGenome:
        if not self.genomes: return None
        k = min(3, len(self.genomes))
        tournament_entrants = random.sample(self.genomes, k)
        return max(tournament_entrants, key=lambda g: g.shared_fitness)


class EvolutionaryAlgorithm:
    def __init__(self, base_pokemon_data, mode: str, config_data: dict):
        self.base_pokemon_data = base_pokemon_data
        self.mode = mode
        self.config_data = config_data
        self.population = [PokemonGenome(self.base_pokemon_data, self.config_data) for _ in range(self.config_data['POPULATION_SIZE'])]
        self.species = []
        self.best_genome_so_far = None
        self.generation = 0
        self.history = []

    async def run(self):
        print(f"--- Starting {self.mode.capitalize()} Mode Evolution for {self.base_pokemon_data['name'].capitalize()} ---")
        
        semaphore = asyncio.Semaphore(self.config_data['MAX_CONCURRENT_EVALUATIONS'])
        generations = self.config_data['GENERATIONS']
        population_size = self.config_data['POPULATION_SIZE']
        stagnation_limit = self.config_data['STAGNATION_LIMIT']
        survival_threshold = self.config_data['SURVIVAL_THRESHOLD']

        async def limited_evaluator(genome):
            async with semaphore:
                await evaluate_fitness(genome, self.mode, self.config_data)

        for gen in range(generations):
            self.generation = gen + 1
            print(f"\n--- Generation {self.generation}/{generations} ---")

            # 1. Evaluate fitness
            print(f"Evaluating population fitness ({self.config_data['MAX_CONCURRENT_EVALUATIONS']} at a time)...")
            tasks = [limited_evaluator(genome) for genome in self.population]
            await asyncio.gather(*tasks)
            
            # 2. Speciate
            self._speciate_population()
            
            # 3. Calculate shared fitness and check for stagnation
            total_avg_shared_fitness = 0
            surviving_species = []
            for s in self.species:
                if not s.genomes: continue
                s.calculate_shared_fitness()
                s.update_stagnation()
                if s.generations_stagnant > stagnation_limit and len(self.species) > 1:
                    print(f"Species {s.representative.genome_id} is stagnant. Removing.")
                    continue
                surviving_species.append(s)
                total_avg_shared_fitness += sum(g.shared_fitness for g in s.genomes) / len(s.genomes)
            self.species = surviving_species
            if not self.species:
                print("All species died! Ending evolution.")
                break
            
            # 4. Calculate offspring
            total_offspring = 0
            for s in self.species:
                if total_avg_shared_fitness > 0:
                    species_avg_shared_fitness = sum(g.shared_fitness for g in s.genomes) / len(s.genomes)
                    share = species_avg_shared_fitness / total_avg_shared_fitness
                    s.offspring_to_spawn = math.floor(share * population_size)
                else:
                    s.offspring_to_spawn = population_size // len(self.species)
                total_offspring += s.offspring_to_spawn
            remainder = population_size - total_offspring
            for i in range(remainder):
                self.species[i % len(self.species)].offspring_to_spawn += 1

            # 5. Cull and Reproduce
            next_generation = []
            current_best_genome = max(self.population, key=lambda g: g.fitness)
            if not self.best_genome_so_far or current_best_genome.fitness > self.best_genome_so_far.fitness:
                self.best_genome_so_far = copy.deepcopy(current_best_genome)

            print(f"Best fitness in gen: {current_best_genome.fitness:.2f} (Species {self._find_species_id(current_best_genome)})")
            print(f"Best genome so far (Fitness: {self.best_genome_so_far.fitness:.2f}):\n{self.best_genome_so_far}")
            print(f"Active Species: {len(self.species)}")
            
            # --- Record stats for this generation ---
            if self.population: # Avoid division by zero if population crashes
                avg_fitness = sum(g.fitness for g in self.population) / len(self.population)
                self.history.append({
                    'gen': self.generation,
                    'best_fitness': current_best_genome.fitness,
                    'avg_fitness': avg_fitness,
                    'num_species': len(self.species)
                })
            
            for s in self.species:
                s.cull(survival_threshold)
                if s.offspring_to_spawn > 0 and s.genomes:
                    next_generation.append(copy.deepcopy(s.get_best_genome()))
                for _ in range(s.offspring_to_spawn - 1):
                    p1 = s.select_parent()
                    p2 = s.select_parent()
                    if not p1 or not p2: continue
                    child = self._crossover(p1, p2)
                    if random.random() < self.config_data['MUTATION_RATE']:
                        child.mutate()
                    next_generation.append(child)

            self.population = next_generation

        print("\n--- Evolution Finished ---")
        champions = []
        for s in self.species:
            if s.genomes:
                champions.append(s.get_best_genome())
        print(f"Found {len(champions)} champions for the final tournament.")
        
        # --- Return history along with champions ---
        return champions, self.history


    def _speciate_population(self):
        for s in self.species:
            s.genomes = [] 
        for genome in self.population:
            found_species = False
            for s in self.species:
                dist = self._get_compatibility_distance(genome, s.representative)
                if dist < self.config_data['COMPATIBILITY_THRESHOLD']:
                    s.add_genome(genome)
                    found_species = True
                    break
            if not found_species:
                new_species = Species(genome)
                self.species.append(new_species)
                
    def _find_species_id(self, genome: PokemonGenome):
        for s in self.species:
            if genome.genome_id in [g.genome_id for g in s.genomes]:
                return s.representative.genome_id
        return "N/A"

    def _get_compatibility_distance(self, g1: PokemonGenome, g2: PokemonGenome) -> float:
        distance = 0.0
        c1 = self.config_data['C1_STATS']
        c2 = self.config_data['C2_TYPES']
        c3 = self.config_data['C3_MOVES']
        c4 = self.config_data['C4_EVS']
        c5 = self.config_data['C5_NATURE']
        
        if g1.is_custom:
            stat_diff = 0
            for stat in g1.stats.keys():
                stat_diff += abs(g1.stats[stat] - g2.stats[stat])
            distance += c1 * (stat_diff / (self.config_data['MAX_BASE_STATS'] * 1.5)) 
            types_g1 = set(g1.types)
            types_g2 = set(g2.types)
            disjoint_types = len(types_g1.symmetric_difference(types_g2))
            distance += c2 * (disjoint_types / 2.0)
        moves_g1 = set(g1.moves)
        moves_g2 = set(g2.moves)
        disjoint_moves = len(moves_g1.symmetric_difference(moves_g2))
        distance += c3 * (disjoint_moves / 4.0)
        ev_diff = 0
        for stat in g1.evs.keys():
            ev_diff += abs(g1.evs.get(stat, 0) - g2.evs.get(stat, 0))
        distance += c4 * (ev_diff / (self.config_data['MAX_EVS'] * 2))
        if g1.nature != g2.nature:
            distance += c5
        return distance

    def _crossover(self, p1: PokemonGenome, p2: PokemonGenome):
        child = PokemonGenome(self.base_pokemon_data, self.config_data, random_init=False)
        child.nature = random.choice([p1.nature, p2.nature])
        combined_moves = list(set(p1.moves + p2.moves))
        if len(combined_moves) < 4:
            possible_adds = [m for m in child.learnset if m not in combined_moves]
            needed = 4 - len(combined_moves)
            if possible_adds:
                combined_moves.extend(random.sample(possible_adds, min(len(possible_adds), needed)))
        child.moves = random.sample(combined_moves, min(4, len(combined_moves)))
        child.moves.sort()
        child.evs = {}
        total_evs = 0
        stats_keys = p1.evs.keys()
        for stat in stats_keys:
            avg_ev = (p1.evs.get(stat, 0) + p2.evs.get(stat, 0)) // 2
            capped_ev = min(avg_ev, 252) 
            child.evs[stat] = capped_ev
            total_evs += capped_ev
        max_evs = self.config_data['MAX_EVS']
        while total_evs > max_evs:
            possible_stats = [k for k, v in child.evs.items() if v > 0]
            if not possible_stats: break 
            stat_to_reduce = random.choice(possible_stats)
            reduction = min(total_evs - max_evs, child.evs[stat_to_reduce])
            child.evs[stat_to_reduce] -= reduction
            total_evs -= reduction
        if child.is_custom:
            child.ability = p1.ability 
            child.stats = {}
            total_stats = 0
            for stat in p1.stats:
                child.stats[stat] = (p1.stats[stat] + p2.stats[stat]) // 2
                total_stats += child.stats[stat]
            max_base_stats = self.config_data['MAX_BASE_STATS']
            diff = max_base_stats - total_stats
            if diff > 0:
                for _ in range(diff): child.stats[random.choice(list(child.stats.keys()))] += 1
            elif diff < 0:
                for _ in range(abs(diff)):
                    possible_stats = [k for k, v in child.stats.items() if v > 1]
                    if not possible_stats: break
                    stat_to_reduce = random.choice(possible_stats)
                    child.stats[stat_to_reduce] -= 1
            combined_types = list(set(p1.types + p2.types))
            num_types = random.choice([1, 2])
            if len(combined_types) >= num_types:
                child.types = random.sample(combined_types, num_types)
            else:
                child.types = combined_types
                while len(child.types) < num_types:
                    new_type = random.choice([t for t in self.config_data['POKEMON_TYPES'] if t not in child.types])
                    child.types.append(new_type)
            child.types.sort()
        else:
            child.stats = copy.deepcopy(p1.stats)
            child.types = copy.deepcopy(p1.types)
            child.ability = copy.deepcopy(p1.ability)
        return child