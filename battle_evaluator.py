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

class SimBattle(pb.Battle):
    """
    A subclass of Battle that disables text logging for performance.
    """
    def add_text(self, txt: str):
        pass 

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
        
        sim_poke.stats_base = list(sim_poke.stats_base)
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
    return poke.fast_copy()

# --- MINIMAX IMPLEMENTATION ---

def _evaluate_state_enhanced(battle: pb.Battle, my_trainer: pb.Trainer) -> float:
    if battle.winner == my_trainer: return 1000000.0
    if battle.winner: return -1000000.0
        
    opp_trainer = battle.t2 if battle.t1 == my_trainer else battle.t1
    p1 = my_trainer.current_poke
    p2 = opp_trainer.current_poke
    
    if not p1.is_alive: return -500000.0 
    if not p2.is_alive: return 500000.0

    # Priority Check: Avoid guaranteed death
    opp_moves = p2.get_available_moves()
    if opp_moves:
        for move in opp_moves:
            if move.prio > 0:
                dmg = _estimate_damage(p2, p1, move)
                if dmg >= p1.cur_hp:
                    return -400000.0 

    # Standard Scoring
    score = ((p1.cur_hp / p1.max_hp) - (p2.cur_hp / p2.max_hp)) * 100.0
    
    # Stat boosts
    p1_boosts = sum(p1.stat_stages) + p1.accuracy_stage + p1.evasion_stage
    p2_boosts = sum(p2.stat_stages) + p2.accuracy_stage + p2.evasion_stage
    score += (p1_boosts - p2_boosts) * 10.0
    
    # Status penalties
    status_weights = {
        gs.BURNED: 10, gs.POISONED: 10, gs.BADLY_POISONED: 15,
        gs.PARALYZED: 25, gs.ASLEEP: 40, gs.FROZEN: 40
    }
    if p1.nv_status in status_weights: score -= status_weights[p1.nv_status]
    if p2.nv_status in status_weights: score += status_weights[p2.nv_status]
    
    # Speed Advantage
    if p1.stats_effective[gs.SPD] > p2.stats_effective[gs.SPD]:
        score += 15.0
    elif p1.stats_effective[gs.SPD] < p2.stats_effective[gs.SPD]:
        score -= 15.0
        
    return score

def _get_ordered_moves(pokemon: pb.Pokemon, opponent: pb.Pokemon) -> list:
    moves = pokemon.get_available_moves()
    if not moves:
        return [Move(pb.PokeSim.get_single_move("struggle"))]
        
    def move_heuristic(move):
        if move.category == gs.STATUS:
            return 0 
        
        estimated_dmg = _estimate_damage(pokemon, opponent, move)
        score = estimated_dmg
        
        if estimated_dmg >= opponent.cur_hp:
            score += 10000 
            if move.prio > 0:
                score += 5000 
        
        if move.prio > 0:
            score += 100
            
        return score

    moves.sort(key=move_heuristic, reverse=True)
    return moves

def _minimax_ab(battle: pb.Battle, depth: int, alpha: float, beta: float, is_maximizing: bool, my_trainer: pb.Trainer, opp_trainer: pb.Trainer, my_move_choice=None) -> float:
    if depth == 0 or battle.is_finished():
        return _evaluate_state_enhanced(battle, my_trainer)

    if is_maximizing:
        best_val = -math.inf
        my_moves = _get_ordered_moves(my_trainer.current_poke, opp_trainer.current_poke)
        
        for move in my_moves:
            val = _minimax_ab(battle, depth, alpha, beta, False, my_trainer, opp_trainer, my_move_choice=move)
            best_val = max(best_val, val)
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
        return best_val
        
    else:
        best_val = math.inf
        opp_moves = _get_ordered_moves(opp_trainer.current_poke, my_trainer.current_poke)
        
        for move in opp_moves:
            try:
                sim_poke_t1 = _clone_pokemon_state(battle.t1.current_poke)
                sim_poke_t2 = _clone_pokemon_state(battle.t2.current_poke)
                sim_t1 = pb.Trainer("SimT1", [sim_poke_t1])
                sim_t2 = pb.Trainer("SimT2", [sim_poke_t2])
                
                if my_trainer == battle.t1:
                    sim_my, sim_opp = sim_t1, sim_t2
                    move_t1, move_t2 = ['move', my_move_choice.name], ['move', move.name]
                else:
                    sim_my, sim_opp = sim_t2, sim_t1
                    move_t1, move_t2 = ['move', move.name], ['move', my_move_choice.name]
                
                sim_battle = SimBattle(sim_t1, sim_t2)
                sim_battle.start()
                sim_battle.turn(move_t1, move_t2)
                
                val = _minimax_ab(sim_battle, depth - 1, alpha, beta, True, sim_my, sim_opp)
                
                best_val = min(best_val, val)
                beta = min(beta, best_val)
                if beta <= alpha:
                    break
            except Exception:
                continue 

        return best_val

_MINIMAX_CONFIG_HACK = {}

def _estimate_damage(attacker: pb.Pokemon, defender: pb.Pokemon, move: Move) -> float:
    if not move.power: return 0.0
        
    if move.category == gs.SPECIAL:
        atk = attacker.stats_effective[gs.SP_ATK]
        defn = defender.stats_effective[gs.SP_DEF]
    else: 
        atk = attacker.stats_effective[gs.ATK]
        defn = defender.stats_effective[gs.DEF]
        
    eff = pb.PokeSim.get_type_ef(move.type, defender.types[0])
    if defender.types[1]:
        eff *= pb.PokeSim.get_type_ef(move.type, defender.types[1])
        
    if eff == 0: return 0.0

    stab = 1.5 if move.type in attacker.types else 1.0
    damage = (0.84 * move.power * (atk / defn) * stab * eff) + 2
    
    if attacker.item == 'life-orb': damage *= 1.3
    elif attacker.item == 'expert-belt' and eff > 1: damage *= 1.2
        
    return damage

def get_best_move_minimax(battle: pb.Battle, player_trainer: pb.Trainer, opponent_trainer: pb.Trainer) -> list:
    global _MINIMAX_CONFIG_HACK
    config_data = _MINIMAX_CONFIG_HACK
    depth = config_data.get('MINIMAX_DEPTH', 2) 
    
    best_move = None
    best_val = -math.inf
    alpha = -math.inf
    beta = math.inf
    
    my_moves = _get_ordered_moves(player_trainer.current_poke, opponent_trainer.current_poke)
    
    if len(my_moves) == 1:
        return ['move', my_moves[0].name]

    for move in my_moves:
        val = _minimax_ab(battle, depth, alpha, beta, False, player_trainer, opponent_trainer, my_move_choice=move)
        
        if val > best_val:
            best_val = val
            best_move = move
        
        alpha = max(alpha, best_val)
        
    if best_move:
        return ['move', best_move.name]
    
    return ['move', 'struggle']

async def evaluate_fitness(genome: PokemonGenome, config_data: dict):
    """ 
    Evaluates the fitness using Minimax.
    SCORING UPDATE: Diminishing returns for repeated wins against the same opponent.
    1st Win: 1000 pts
    2nd Win: 250 pts
    3rd Win: 100 pts
    """
    await asyncio.sleep(0) 
    pb.PokeSim.start()
    total_score = 0
    
    global _MINIMAX_CONFIG_HACK
    _MINIMAX_CONFIG_HACK = config_data
    
    # Always use the main GAUNTLET
    current_gauntlet = config_data['GAUNTLET']
    t1_ai = get_best_move_minimax
    t2_ai = get_best_move_minimax
    
    gauntlet_limit = config_data.get('GAUNTLET_SIZE')
    if gauntlet_limit and gauntlet_limit > 0:
        current_gauntlet = current_gauntlet[:gauntlet_limit]

    try:
        # Dry run to check validity
        _genome_to_sim_pokemon(genome)
    except Exception as e:
        print(f"Invalid genome {genome.genome_id}, skipping. Error: {e}")
        genome.fitness = 0
        return 0

    # Battle Loop
    for opponent_info in current_gauntlet:
        try:
            # Validate opponent data
            _gauntlet_to_sim_pokemon(opponent_info)
        except Exception as e:
            print(f"Invalid opponent data for {opponent_info['name']}, skipping.")
            continue

        wins_against_this_opponent = 0
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
                wins_against_this_opponent += 1

        # Apply Diminishing Returns Scoring
        if wins_against_this_opponent >= 1:
            total_score += 1000
        if wins_against_this_opponent >= 2:
            total_score += 250
        if wins_against_this_opponent >= 3:
            total_score += 100

    genome.fitness = total_score
    _MINIMAX_CONFIG_HACK = {}
    return total_score


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