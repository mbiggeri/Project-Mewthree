import asyncio
import random
import math
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
        sim_poke.nickname = CUSTOM_POKEMON_NICKNAME 
        
        # 1. Make a COPY of the stats_base so we don't modify the global Arceus definition
        sim_poke.stats_base = list(sim_poke.stats_base)

        # 2. Update the "base" types to match the genome. 
        # This ensures that when reset_stats() is called at battle start, 
        # it reverts to THESE types instead of Normal/Normal.
        sim_poke.stats_base[gs.TYPE1] = genome.types[0]
        if len(genome.types) > 1:
            sim_poke.stats_base[gs.TYPE2] = genome.types[1]
        else:
            sim_poke.stats_base[gs.TYPE2] = None
            
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
    opp_poke.calculate_stats_actual() 
    opp_poke.max_hp = opp_poke.stats_actual[gs.HP]
    opp_poke.cur_hp = opp_poke.stats_actual[gs.HP]
    return opp_poke

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

def get_max_damage_move(battle: pb.Battle, player_trainer: pb.Trainer, opponent_trainer: pb.Trainer) -> list:
    """ 
    Selects the move that deals the highest calculated damage to the opponent.
    Used as a fallback or for simple gauntlets.
    """
    player_poke = player_trainer.current_poke
    opponent_poke = opponent_trainer.current_poke
    available_moves = player_poke.get_available_moves()
    
    if not available_moves: 
        return gd.STRUGGLE 
         
    best_move = available_moves[0].name
    max_damage = -1
    best_prio_kill_move = None
    best_prio_kill_prio = -999
    
    for move in available_moves:
        try:
            p1 = _clone_pokemon_state(player_poke)
            p2 = _clone_pokemon_state(opponent_poke)
        except Exception:
            continue

        base_id_p2 = "Arceus" if p2.nickname == CUSTOM_POKEMON_NICKNAME else p2.name

        p2_dummy = pb.Pokemon(
            name_or_id=base_id_p2, level=p2.level, moves=["splash"], 
            gender=p2.gender, ability=p2.ability, nature=p2.nature,
            ivs=p2.ivs, evs=p2.evs, item=getattr(p2, 'item', None)
        )
        
        p2_dummy.base = p2.base 
        p2_dummy.calculate_stats_actual()
        p2_dummy.cur_hp = p2.cur_hp
        p2_dummy.max_hp = p2.max_hp
        p2_dummy.types = p2.types
        p2_dummy.stat_stages = list(p2.stat_stages)
        p2_dummy.evasion_stage = p2.evasion_stage
        p2_dummy.nv_status = p2.nv_status
        
        t1 = pb.Trainer("p1", [p1])
        t2 = pb.Trainer("p2", [p2_dummy])
        sim_battle = pb.Battle(t1, t2)
        sim_battle.start()
        
        hp_before = p2_dummy.cur_hp
        
        try:
            sim_battle.turn(['move', move.name], ['move', 'splash'])
        except Exception:
            continue
            
        damage = hp_before - p2_dummy.cur_hp

        if damage >= hp_before and move.prio > 0:
            if best_prio_kill_move is None or move.prio > best_prio_kill_prio:
                best_prio_kill_move = move.name
                best_prio_kill_prio = move.prio
        
        if damage > max_damage:
            max_damage = damage
            best_move = move.name
            
    if best_prio_kill_move:
        return ['move', best_prio_kill_move]

    return ['move', best_move]

# --- IMPROVED MINIMAX IMPLEMENTATION ---

def _evaluate_state_enhanced(battle: pb.Battle, my_trainer: pb.Trainer) -> float:
    """
    Enhanced evaluation function. Returns a score from the perspective of 'my_trainer'.
    Score is derived from HP % diff, Status penalties, Stat boosts, and Speed advantage.
    """
    if battle.winner == my_trainer:
        return 1000000.0
    if battle.winner: # Winner is opponent
        return -1000000.0
        
    opp_trainer = battle.t2 if battle.t1 == my_trainer else battle.t1
    
    p1 = my_trainer.current_poke
    p2 = opp_trainer.current_poke
    
    if not p1.is_alive: return -500000.0 
    if not p2.is_alive: return 500000.0

    # HP Score (Percentage diff)
    score = ((p1.cur_hp / p1.max_hp) - (p2.cur_hp / p2.max_hp)) * 100.0
    
    # Stat boosts
    p1_boosts = sum(p1.stat_stages) + p1.accuracy_stage + p1.evasion_stage
    p2_boosts = sum(p2.stat_stages) + p2.accuracy_stage + p2.evasion_stage
    score += (p1_boosts - p2_boosts) * 10.0
    
    # Status penalties (Weighted by severity)
    status_weights = {
        gs.BURNED: 10, gs.POISONED: 10, gs.BADLY_POISONED: 15,
        gs.PARALYZED: 25, gs.ASLEEP: 40, gs.FROZEN: 40
    }
    if p1.nv_status in status_weights: score -= status_weights[p1.nv_status]
    if p2.nv_status in status_weights: score += status_weights[p2.nv_status]
    
    # Speed Advantage (Critical in Pokemon)
    if p1.stats_effective[gs.SPD] > p2.stats_effective[gs.SPD]:
        score += 15.0
    elif p1.stats_effective[gs.SPD] < p2.stats_effective[gs.SPD]:
        score -= 15.0
        
    return score

def _get_ordered_moves(pokemon: pb.Pokemon, opponent: pb.Pokemon) -> list:
    """
    Returns available moves sorted by a heuristic (Power * Type Effectiveness) 
    to improve Alpha-Beta pruning efficiency.
    """
    moves = pokemon.get_available_moves()
    if not moves:
        # Return struggle if no moves (Move object wrapper)
        return [Move(pb.PokeSim.get_single_move("struggle"))]
        
    def move_heuristic(move):
        if move.category == gs.STATUS:
            return 0 # Lower priority than damage generally
        
        # Calculate rough type effectiveness
        eff = pb.PokeSim.get_type_ef(move.type, opponent.types[0])
        if opponent.types[1]:
            eff *= pb.PokeSim.get_type_ef(move.type, opponent.types[1])
            
        return (move.power or 0) * eff

    # Sort descending (Best moves first)
    moves.sort(key=move_heuristic, reverse=True)
    return moves

def _minimax_ab(battle: pb.Battle, depth: int, alpha: float, beta: float, is_maximizing: bool, my_trainer: pb.Trainer, opp_trainer: pb.Trainer, my_move_choice=None) -> float:
    """
    Minimax with Alpha-Beta Pruning.
    One 'depth' step corresponds to a full turn (Both players selecting a move).
    
    Structure:
    1. Max Layer (My Turn): Select 'my_move' -> Recurse to Min Layer.
    2. Min Layer (Opponent Turn): Select 'opp_move', Simulate Turn -> Recurse to Max Layer (depth - 1).
    """
    if depth == 0 or battle.is_finished():
        return _evaluate_state_enhanced(battle, my_trainer)

    if is_maximizing:
        # --- MAXIMIZING LAYER (We choose a move) ---
        best_val = -math.inf
        
        # Move Ordering: Try best moves first
        my_moves = _get_ordered_moves(my_trainer.current_poke, opp_trainer.current_poke)
        
        for move in my_moves:
            # Pass our chosen move to the Minimizing layer
            val = _minimax_ab(battle, depth, alpha, beta, False, my_trainer, opp_trainer, my_move_choice=move)
            best_val = max(best_val, val)
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break # Beta Cutoff
        return best_val
        
    else:
        # --- MINIMIZING LAYER (Opponent chooses a move & Simulation happens) ---
        best_val = math.inf
        
        # Move Ordering: Opponent tries their best moves first
        opp_moves = _get_ordered_moves(opp_trainer.current_poke, my_trainer.current_poke)
        
        for move in opp_moves:
            # CLONE STATE for simulation
            try:
                sim_poke_t1 = _clone_pokemon_state(battle.t1.current_poke)
                sim_poke_t2 = _clone_pokemon_state(battle.t2.current_poke)
                sim_t1 = pb.Trainer("SimT1", [sim_poke_t1])
                sim_t2 = pb.Trainer("SimT2", [sim_poke_t2])
                
                # Identify who is who in the sim
                if my_trainer == battle.t1:
                    sim_my, sim_opp = sim_t1, sim_t2
                    move_t1, move_t2 = ['move', my_move_choice.name], ['move', move.name]
                else:
                    sim_my, sim_opp = sim_t2, sim_t1
                    move_t1, move_t2 = ['move', move.name], ['move', my_move_choice.name]
                
                sim_battle = pb.Battle(sim_t1, sim_t2)
                sim_battle.start()
                
                # SIMULATE TURN
                sim_battle.turn(move_t1, move_t2)
                
                # Recurse to next depth
                val = _minimax_ab(sim_battle, depth - 1, alpha, beta, True, sim_my, sim_opp)
                
                best_val = min(best_val, val)
                beta = min(beta, best_val)
                if beta <= alpha:
                    break # Alpha Cutoff
            except Exception:
                continue 

        return best_val

_MINIMAX_CONFIG_HACK = {}

def get_best_move_minimax(battle: pb.Battle, player_trainer: pb.Trainer, opponent_trainer: pb.Trainer) -> list:
    """ 
    Root function for the Minimax search.
    """
    global _MINIMAX_CONFIG_HACK
    config_data = _MINIMAX_CONFIG_HACK
    # Default depth can be slightly higher now due to pruning
    depth = config_data.get('MINIMAX_DEPTH', 2) 
    
    best_move = None
    best_val = -math.inf
    alpha = -math.inf
    beta = math.inf
    
    # Get ordered moves for root level
    my_moves = _get_ordered_moves(player_trainer.current_poke, opponent_trainer.current_poke)
    
    # Optimization: If only 1 move (Choice locked or Struggle), just return it
    if len(my_moves) == 1:
        return ['move', my_moves[0].name]

    for move in my_moves:
        # Call Minimax starting at the Minimizing layer (since we just picked our move)
        val = _minimax_ab(battle, depth, alpha, beta, False, player_trainer, opponent_trainer, my_move_choice=move)
        
        if val > best_val:
            best_val = val
            best_move = move
        
        # Update Alpha at root
        alpha = max(alpha, best_val)
        
    if best_move:
        return ['move', best_move.name]
    
    return ['move', 'struggle'] # Fallback

async def evaluate_fitness(genome: PokemonGenome, mode: str, config_data: dict):
    """ Evaluates the fitness of a given PokemonGenome by running it against a gauntlet of opponents. """
    await asyncio.sleep(0) 
    pb.PokeSim.start()
    total_wins = 0
    
    global _MINIMAX_CONFIG_HACK
    _MINIMAX_CONFIG_HACK = config_data
    
    if mode == "simple":
        current_gauntlet = config_data['SIMPLE_GAUNTLET']
        t1_ai = get_max_damage_move
        t2_ai = get_max_damage_move
    else: # "advanced"
        current_gauntlet = config_data['GAUNTLET']
        t1_ai = get_best_move_minimax
        t2_ai = get_best_move_minimax
    
    gauntlet_limit = config_data.get('GAUNTLET_SIZE')
    if gauntlet_limit and gauntlet_limit > 0:
        current_gauntlet = current_gauntlet[:gauntlet_limit]

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
    """ Runs a round-robin tournament among the provided champions. """
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