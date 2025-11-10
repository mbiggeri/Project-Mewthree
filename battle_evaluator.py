# battle_evaluator.py
import asyncio
import random
import poke_battle_sim as pb
import copy
from poke_battle_sim.conf import global_data as gd
from poke_battle_sim.conf import global_settings as gs
from poke_battle_sim.core.move import Move

from pokemon_genome import PokemonGenome

CUSTOM_POKEMON_NICKNAME = "MEWTHREE" 

def _genome_to_sim_pokemon(genome: PokemonGenome) -> pb.Pokemon:
    ivs = [31, 31, 31, 31, 31, 31]
    ev_map = genome.evs
    ev_list = [
        ev_map.get('hp', 0), ev_map.get('atk', 0), ev_map.get('def', 0),
        ev_map.get('spa', 0), ev_map.get('spd', 0), ev_map.get('spe', 0)
    ]
    if genome.is_custom:
        sim_poke = pb.Pokemon(
            name_or_id="Arceus", level=100, moves=genome.moves,
            gender="genderless", ability=genome.ability, nature=genome.nature,
            ivs=ivs, evs=ev_list, item=None
        )
        sim_poke.name = genome.name
        sim_poke.nickname = CUSTOM_POKEMON_NICKNAME # Use the variable defined above
        sim_poke.types = tuple(genome.types)
        if len(sim_poke.types) == 1:
            sim_poke.types = (sim_poke.types[0], None)
        g_stats = genome.stats
        sim_poke.base = [
            g_stats.get('hp', 1), g_stats.get('atk', 1), g_stats.get('def', 1),
            g_stats.get('spa', 1), g_stats.get('spd', 1), g_stats.get('spe', 1)
        ]
        sim_poke.calculate_stats_actual()
        sim_poke.max_hp = sim_poke.stats_actual[gs.HP]
        sim_poke.cur_hp = sim_poke.stats_actual[gs.HP]
        return sim_poke
    else:
        sim_poke = pb.Pokemon(
            name_or_id=genome.name, level=100, moves=genome.moves,
            gender="genderless", ability=genome.ability, nature=genome.nature,
            ivs=ivs, evs=ev_list, item=None
        )
        return sim_poke

def _gauntlet_to_sim_pokemon(opponent_info: dict) -> pb.Pokemon:
    ev_list = [0, 0, 0, 0, 0, 0]
    ev_str_map = {'hp': 0, 'atk': 1, 'def': 2, 'spa': 3, 'spd': 4, 'spe': 5}
    if opponent_info.get("evs"):
        parts = opponent_info["evs"].lower().split(' / ')
        for part in parts:
            num, stat = part.split(' ')
            if stat in ev_str_map:
                ev_list[ev_str_map[stat]] = int(num)
    ivs = [31, 31, 31, 31, 31, 31] 
    opp_poke = pb.Pokemon(
        name_or_id=opponent_info["name"], level=100, moves=opponent_info["moves"],
        gender="genderless", ability=opponent_info["ability"], nature=opponent_info["nature"],
        ivs=ivs, evs=ev_list, item=None
    )
    return opp_poke

def get_max_base_power_move(battle: pb.Battle, player_trainer: pb.Trainer, opponent_trainer: pb.Trainer) -> list:
    """ Selects the move with the highest base power available to the player's current Pokemon. 
    This is a simple heuristic-based AI for a fast evaluation."""
    player_pokemon = player_trainer.current_poke
    available_moves = player_pokemon.get_available_moves()
    if not available_moves: return gd.STRUGGLE 
    best_move = None
    best_power = -1
    for move in available_moves:
        try:
            current_move_power = int(move.power)
        except (ValueError, TypeError):
            current_move_power = 0
        if current_move_power > best_power:
            best_power = current_move_power
            best_move = move.name
    if best_move is None:
        best_move = random.choice(available_moves).name
    return ['move', best_move]

def _clone_pokemon_state(poke: pb.Pokemon) -> pb.Pokemon:
    is_custom_poke = (poke.nickname == CUSTOM_POKEMON_NICKNAME)
    base_id = "Arceus" if is_custom_poke else poke.name
    new_poke = pb.Pokemon(
        name_or_id=base_id, level=poke.level, moves=[m.name for m in poke.moves], 
        gender=poke.gender, ability=poke.ability, nature=poke.nature,
        ivs=poke.ivs, evs=poke.evs, item=poke.item
    )
    if is_custom_poke:
        new_poke.name = poke.name
        new_poke.nickname = poke.nickname
        new_poke.types = poke.types
        new_poke.base = poke.base 
        new_poke.calculate_stats_actual()
        new_poke.max_hp = new_poke.stats_actual[gs.HP]
    new_poke.cur_hp = poke.cur_hp
    new_poke.nv_status = poke.nv_status
    new_poke.v_status = copy.deepcopy(poke.v_status) 
    new_poke.stat_stages = copy.deepcopy(poke.stat_stages)
    new_poke.accuracy_stage = poke.accuracy_stage
    new_poke.evasion_stage = poke.evasion_stage
    for i, new_move in enumerate(new_poke.moves):
        new_move.cur_pp = poke.moves[i].cur_pp
    return new_poke

def _evaluate_state(battle: pb.Battle) -> int:
    """ Evaluates the battle state from the perspective of trainer 1. 
    A higher score indicates a better position for trainer 1. 
    It works by comparing HP, stat boosts, and status conditions. 
    (TODO: This can be improved with more factors.) """
    p1 = battle.t1.current_poke
    p2 = battle.t2.current_poke
    if not p1.is_alive: return -100000 
    if not p2.is_alive: return 100000 
    p1_hp_score = (p1.cur_hp / p1.max_hp) * 100
    p2_hp_score = (p2.cur_hp / p2.max_hp) * 100
    score = p1_hp_score - p2_hp_score
    p1_boosts = sum(p1.stat_stages) + p1.accuracy_stage + p1.evasion_stage
    p2_boosts = sum(p2.stat_stages) + p2.accuracy_stage + p2.evasion_stage
    score += (p1_boosts * 20) - (p2_boosts * 20)
    if p1.nv_status: score -= 50 
    if p2.nv_status in [gs.BADLY_POISONED, gs.POISONED, gs.BURNED, gs.PARALYZED, gs.ASLEEP]:
        score += 50
    return score

def _minimax_recursive(battle: pb.Battle, depth: int, is_maximizing_player: bool, t1: pb.Trainer, t2: pb.Trainer, minimax_depth: int):
    """ Minimax algorithm implementation for Pokemon battle state evaluation. 
    This function recursively explores possible moves up to a certain depth
    and evaluates the resulting battle states.
    (TODO: This can be optimized with alpha-beta pruning, and commented more.) """
    if depth == 0 or battle.is_finished():
        return _evaluate_state(battle)

    if is_maximizing_player:
        best_value = -float('inf')
        t1_moves = t1.current_poke.get_available_moves() or [Move(pb.PokeSim.get_single_move("struggle"))]
        t2_moves = t2.current_poke.get_available_moves() or [Move(pb.PokeSim.get_single_move("struggle"))]
        for t1_move in t1_moves:
            worst_reply_score = float('inf')
            for t2_move in t2_moves:
                sim_poke_t1 = _clone_pokemon_state(t1.current_poke)
                sim_poke_t2 = _clone_pokemon_state(t2.current_poke)
                sim_t1_trainer = pb.Trainer("SimTrainer1", [sim_poke_t1])
                sim_t2_trainer = pb.Trainer("SimTrainer2", [sim_poke_t2])
                sim_battle = pb.Battle(sim_t1_trainer, sim_t2_trainer)
                sim_battle.start()
                try:
                    sim_battle.turn(['move', t1_move.name], ['move', t2_move.name])
                except Exception: continue 
                score = _minimax_recursive(sim_battle, depth - 1, False, sim_battle.t1, sim_battle.t2, minimax_depth)
                worst_reply_score = min(worst_reply_score, score)
            best_value = max(best_value, worst_reply_score)
        return best_value
    else:
        best_value = float('inf')
        t1_moves = t1.current_poke.get_available_moves() or [Move(pb.PokeSim.get_single_move("struggle"))]
        t2_moves = t2.current_poke.get_available_moves() or [Move(pb.PokeSim.get_single_move("struggle"))]
        for t2_move in t2_moves:
            best_reply_score = -float('inf')
            for t1_move in t1_moves:
                sim_poke_t1 = _clone_pokemon_state(t1.current_poke)
                sim_poke_t2 = _clone_pokemon_state(t2.current_poke)
                sim_t1_trainer = pb.Trainer("SimTrainer1", [sim_poke_t1])
                sim_t2_trainer = pb.Trainer("SimTrainer2", [sim_poke_t2])
                sim_battle = pb.Battle(sim_t1_trainer, sim_t2_trainer)
                sim_battle.start()
                try:
                    sim_battle.turn(['move', t1_move.name], ['move', t2_move.name])
                except Exception: continue
                score = _minimax_recursive(sim_battle, depth - 1, True, sim_battle.t1, sim_battle.t2, minimax_depth)
                best_reply_score = max(best_reply_score, score)
            best_value = min(best_value, best_reply_score)
        return best_value

_MINIMAX_CONFIG_HACK = {}
def get_best_move_minimax(battle: pb.Battle, player_trainer: pb.Trainer, opponent_trainer: pb.Trainer) -> list:
    """ This function calls the minimax implementation to 
    determine the best move for the player_trainer's current Pokemon. """
    global _MINIMAX_CONFIG_HACK
    config_data = _MINIMAX_CONFIG_HACK
    minimax_depth = config_data.get('MINIMAX_DEPTH', 1) 
    
    return _get_best_move_minimax_impl(battle, player_trainer, opponent_trainer, minimax_depth)
    

def _get_best_move_minimax_impl(battle: pb.Battle, player_trainer: pb.Trainer, opponent_trainer: pb.Trainer, minimax_depth: int) -> list:
    """ This function uses the minimax algorithm to determine the best move for the player_trainer's current Pokemon.
    It simulates all possible moves for both the player and the opponent up to a specified depth
    and evaluates the resulting battle states to choose the optimal move."""
    available_moves_player = player_trainer.current_poke.get_available_moves() or [Move(pb.PokeSim.get_single_move("struggle"))]
    available_moves_opponent = opponent_trainer.current_poke.get_available_moves() or [Move(pb.PokeSim.get_single_move("struggle"))]

    best_move_so_far = None
    is_player_t1 = (player_trainer == battle.t1)
    
    if is_player_t1: best_score_so_far = -float('inf')
    else: best_score_so_far = float('inf')

    for player_move in available_moves_player:
        if is_player_t1: opp_best_score = float('inf')
        else: opp_best_score = -float('inf')
        
        for opp_move in available_moves_opponent:
            sim_poke_t1_base = _clone_pokemon_state(battle.t1.current_poke)
            sim_poke_t2_base = _clone_pokemon_state(battle.t2.current_poke)
            sim_t1 = pb.Trainer("SimTrainer1", [sim_poke_t1_base])
            sim_t2 = pb.Trainer("SimTrainer2", [sim_poke_t2_base])
            sim_battle = pb.Battle(sim_t1, sim_t2)
            sim_battle.start()
            try:
                if is_player_t1:
                    sim_battle.turn(['move', player_move.name], ['move', opp_move.name])
                else:
                    sim_battle.turn(['move', opp_move.name], ['move', player_move.name])
            except Exception: continue 
            
            current_score = _minimax_recursive(sim_battle, minimax_depth - 1, True, sim_battle.t1, sim_battle.t2, minimax_depth)
            
            if is_player_t1: opp_best_score = min(opp_best_score, current_score)
            else: opp_best_score = max(opp_best_score, current_score)
        
        if is_player_t1:
            if opp_best_score > best_score_so_far:
                best_score_so_far = opp_best_score
                best_move_so_far = player_move.name
        else:
            if opp_best_score < best_score_so_far:
                best_score_so_far = opp_best_score
                best_move_so_far = player_move.name

    if best_move_so_far is None:
        return get_max_base_power_move(battle, player_trainer, opponent_trainer)
    return ['move', best_move_so_far]



async def evaluate_fitness(genome: PokemonGenome, mode: str, config_data: dict):
    """ Evaluates the fitness of a given PokemonGenome by running it against a gauntlet of opponents.
    The mode parameter determines whether to use the "simple" or "advanced" gauntlet and AI.
    The fitness score is calculated based on the number of wins. """
    await asyncio.sleep(0) 
    pb.PokeSim.start()
    total_wins = 0
    
    global _MINIMAX_CONFIG_HACK
    _MINIMAX_CONFIG_HACK = config_data
    
    if mode == "simple":
        current_gauntlet = config_data['SIMPLE_GAUNTLET']
        t1_ai = get_max_base_power_move
        t2_ai = get_max_base_power_move
    else: # "advanced"
        current_gauntlet = config_data['GAUNTLET']
        t1_ai = get_best_move_minimax
        t2_ai = get_best_move_minimax

    try:
        our_pokemon_base = _genome_to_sim_pokemon(genome)
    except Exception as e:
        print(f"Invalid genome {genome.genome_id}, skipping. Error: {e}")
        genome.fitness = 0
        return 0

    for opponent_info in current_gauntlet:
        try:
            opponent_pokemon_base = _gauntlet_to_sim_pokemon(opponent_info)
        except Exception as e:
            print(f"Invalid opponent data for {opponent_info['name']}, skipping. Error: {e}")
            continue

        n_battles = 3
        for _ in range(n_battles):
            our_pokemon = _genome_to_sim_pokemon(genome)
            our_trainer = pb.Trainer("GenomeTrainer", [our_pokemon])
            opponent_pokemon = _gauntlet_to_sim_pokemon(opponent_info)
            opponent_trainer = pb.Trainer(opponent_info["name"], [opponent_pokemon])
            
            battle = pb.Battle(our_trainer, opponent_trainer)
            battle.start()

            while not battle.is_finished():
                t1_move = t1_ai(battle, battle.t1, battle.t2)
                t2_move = t2_ai(battle, battle.t2, battle.t1)
                try:
                    battle.turn(t1_move, t2_move)
                except Exception:
                    break 
            if battle.get_winner() == our_trainer:
                total_wins += 1

    fitness_score = (total_wins * 1000)
    genome.fitness = fitness_score
    _MINIMAX_CONFIG_HACK = {}
    return fitness_score


def run_final_tournament(champions: list, config_data: dict) -> PokemonGenome:
    """ Runs a round-robin tournament among the provided champions.
    Each champion battles every other champion once.
    The champion with the most wins is declared the ultimate winner.
    In case of a tie, the champion with the most KOs in the advanced gauntlet wins. """
    print(f"\n--- Starting Final Tournament with {len(champions)} Champions ---")
    if not champions:
        print("No champions to run tournament with.")
        return None

    pb.PokeSim.start()
    
    global _MINIMAX_CONFIG_HACK
    _MINIMAX_CONFIG_HACK = config_data

    tournament_wins = {champ.genome_id: 0 for champ in champions}

    for i in range(len(champions)):
        for j in range(i + 1, len(champions)):
            champ1_genome = champions[i]
            champ2_genome = champions[j]

            print(f"\n--- TOURNAMENT MATCH: {champ1_genome.name} (ID {champ1_genome.genome_id}) vs. {champ2_genome.name} (ID {champ2_genome.genome_id}) ---")
            
            champ1_poke = _genome_to_sim_pokemon(champ1_genome)
            champ1_trainer = pb.Trainer(f"Champ_{champ1_genome.genome_id}", [champ1_poke])
            champ2_poke = _genome_to_sim_pokemon(champ2_genome)
            champ2_trainer = pb.Trainer(f"Champ_{champ2_genome.genome_id}", [champ2_poke])
            
            battle = pb.Battle(champ1_trainer, champ2_trainer)
            battle.start()
            for line in battle.get_cur_text(): print(line)

            turn_count = 0
            while not battle.is_finished():
                turn_count += 1
                print(f"--- Turn {turn_count} ---")
                
                t1_move = get_best_move_minimax(battle, battle.t1, battle.t2)
                t2_move = get_best_move_minimax(battle, battle.t2, battle.t1)
                
                try:
                    battle.turn(t1_move, t2_move)
                    for line in battle.get_cur_text():
                        print(line)
                except Exception as e:
                    print(f"Error during tournament turn: {e}. Ending battle.")
                    break 

            winner = battle.get_winner()
            if winner == champ1_trainer:
                print(f"--- MATCH WINNER: {champ1_genome.name} (ID {champ1_genome.genome_id}) ---")
                tournament_wins[champ1_genome.genome_id] += 1
            elif winner == champ2_trainer:
                print(f"--- MATCH WINNER: {champ2_genome.name} (ID {champ2_genome.genome_id}) ---")
                tournament_wins[champ2_genome.genome_id] += 1
            else:
                print("--- MATCH END: DRAW ---")

    print("\n--- TOURNAMENT COMPLETE ---")
    print("Final Standings (Wins):")
    
    best_genome_id = -1
    max_wins = -1
    for genome_id, wins in tournament_wins.items():
        print(f"Genome {genome_id}: {wins} wins")
        if wins > max_wins:
            max_wins = wins
            best_genome_id = genome_id
            
    ultimate_winner = next((g for g in champions if g.genome_id == best_genome_id), None)
    
    if ultimate_winner:
        print(f"\n--- ULTIMATE CHAMPION (ID {ultimate_winner.genome_id}) ---")
        print(str(ultimate_winner))
    
    _MINIMAX_CONFIG_HACK = {}
    return ultimate_winner