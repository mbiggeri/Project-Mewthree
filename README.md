# Project Mewthree

![Mewthree](/sprites/normal.png)

## Overview

This project uses a genetic algorithm to evolve an "optimal" Pokémon, code-named "Mewthree." The algorithm can either start from scratch to design a new Pokémon's base stats, types, ability, moveset, and nature, or it can optimize the build (moves, nature, EVs) for an existing Pokémon from Generations 1-4.

The "fitness" of each Pokémon is determined by its performance in simulated battles against a "gauntlet" of strong, predefined opponents.

> The ultimate goal is to leverage evolutionary computation to discover a competitively viable Pokémon build that can defeat this gauntlet.

## How it Works: File Breakdown

The project is divided into several key Python files that work together to run the application.

### `main.py`

> **High-Level:** This is the main entry point of the application. Its sole responsibility is to initialize and launch the tkinter graphical user interface (GUI). It also applies a patch (`nest_asyncio`) to allow the asyncio event loop (used for battles) to run within the tkinter event loop.

### `ui.py`

> Defines the entire GUI for the application using tkinter. This is the user's control panel for running experiments. It separates concerns into different tabs. Designed and written entirely by Gemini because it's the less interesting part and I didn't want to spend time on it.

### `config.py`

> **High-Level:** A central configuration file containing all the tunable parameters for the simulation. This file defines the "hyperparameters" for the genetic algorithm as well as the "domain data" for the Pokémon battles.

This file contains no code, only global constants.

**Key Parameter Groups:**

  * **NEAT Parameters:** `COMPATIBILITY_THRESHOLD`, `STAGNATION_LIMIT`, etc., which control how species are formed and culled.
  * **Evolution Parameters:** `POPULATION_SIZE`, `GENERATIONS`, `MUTATION_RATE`, etc.
  * **Pokémon Data Pools:** `MOVE_POOL`, `POKEMON_TYPES`, `NATURES`.
  * **Opponent Gauntlets:** `GAUNTLET` (for "Advanced Mode") and `SIMPLE_GAUNTLET` (for "Simple Mode") define the list of opponents our Pokémon must fight.

### `pokemon_genome.py`

> **High-Level:** Defines the "chromosome" of a single Pokémon. An object of this class represents one individual in the population and holds all the traits that the genetic algorithm can modify.

**Key Objects/Functions:**

  * `PokemonGenome` (class):
      * `__init__()`: Initializes a new genome. It can operate in two modes: "custom" (for "Mewthree"), where stats and types are evolvable, or "standard," where it uses the base stats/types of an existing Pokémon.
      * `_randomize_stats()` / `_randomize_evs()`: Helper functions to create valid, random spreads for stats and EVs that adhere to the limits in `config.py`.
      * `mutate()`: Applies a small, random change to one of the genome's evolvable traits (e.g., swaps a move, changes an EV, adjusts a base stat). This is the primary driver of genetic diversity.

### `evolutionary_algorithm.py`

> **High-Level:** This is the core engine of the project. It implements a genetic algorithm inspired by NEAT (NeuroEvolution of Augmenting Topologies), which uses "speciation" to protect novel solutions and evolve them in parallel.

**Key Objects/Functions:**

  * `Species` (class): A container that groups genetically similar `PokemonGenome` objects together. This allows, for example, a "fast special attacker" species and a "bulky physical attacker" species to evolve separately without one immediately out-competing the other.
  * `EvolutionaryAlgorithm` (class):
      * `run()`: The main asynchronous loop that runs for `GENERATIONS` count. In each generation, it manages the entire evolutionary process:
          * Calls `evaluate_fitness` for every genome.
          * Calls `_speciate_population` to group genomes.
          * Calculates shared fitness and culls stagnant or weak species.
          * Performs `_crossover` (breeding) and `mutate` to create the next generation.
      * `_get_compatibility_distance()`: A function that compares two genomes to see how "different" they are. This determines if they belong in the same `Species`.
      * `_crossover()`: Takes two parent genomes and "breeds" them to create a child genome, mixing their traits.

### `battle_evaluator.py`

> **High-Level:** This file acts as the "fitness function." Its job is to take a genome, run it through a series of simulated battles using the `poke-battle-sim` library, and return a score representing its combat performance.

**Key Objects/Functions:**

  * `evaluate_fitness()`: The main fitness function called by the `EvolutionaryAlgorithm`. It takes a single genome, runs it against the full gauntlet (in "simple" or "advanced" mode) multiple times, and returns a fitness score based on its win rate.
  * `_genome_to_sim_pokemon()`: A critical "translator" function. It converts a `PokemonGenome` object into a `pb.Pokemon` object that the battle simulator can understand. This function correctly applies the custom stats, types, moves, and ability of the genome to the simulated Pokémon.
  * `get_max_base_power_move()`: A "simple" AI logic used in "Simple Mode." It only looks at the available moves and picks the one with the highest base power.
  * `get_best_move_minimax()`: A "smart" AI logic used in "Advanced Mode." It uses a minimax algorithm to simulate the next few turns and find the move that leads to the best possible outcome, assuming the opponent also plays optimally.
  * `_evaluate_state()`: The helper function for minimax that assigns a "score" to a given battle state (e.g., +100 for a KO, -50 for being poisoned).
  * `run_final_tournament()`: This function is called once at the very end of the evolution. It takes the "champion" of each surviving species and pits them against each other in a round-robin tournament to find the one "Ultimate Champion."

### `generate_data.py`

> A one-time utility script used to populate `pokemon_data.py`. It connects to the public PokéAPI and downloads the stats, types, abilities, and Gen 4 learnsets for all Pokémon up to \#493 (Sinnoh). **This script is not run by the main application.**

### `pokemon_data.py`

> A static data file that is the output of `generate_data.py`. It contains a single, massive dictionary, `POKEMON_DATABASE`, which maps Pokémon names to their in-game data. This file is used by the UI to populate the "Choose Pokémon" dropdown and by the `PokemonGenome` class to get the learnset and base stats for non-custom evolutions.

-----

## Setup & Running the Project

1.  **Install Dependencies**
    Make sure you have Python installed, then run the following command in your terminal to install the necessary libraries:

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application**
    Execute the main script from your terminal:

    ```bash
    python main.py
    ```

3.  **Watch the Evolution**
    The GUI will launch. Choose your Pokémon ("Mewthree" or a standard one), select your mode, and press "Start Evolution.Optionally you can change the hyperparameters before starting evaluation. " The "Experiment Log" tab will show the live progress, and the "Convergence Graph" tab will update once the experiment is complete.
-----

## Useful theory reminders for understanding the code

1.  **MiniMax**

    MiniMax is a decision-making algorithm used in two-player, zero-sum games (like chess). It works by building a "tree" of possible future moves to find the optimal move. It assumes the "Max" player tries to maximize their score, while the "Min" player (the opponent) tries to minimize that score.

2.  **Genetic Algorithms**

    A Genetic Algorithm (GA) is a search strategy inspired by Charles Darwin's theory of natural selection, used to find optimal solutions to complex problems. It works by evolving a population of candidate solutions over generations using processes like Selection (survival of the fittest), Crossover (reproduction), and Mutation (random variation).

3.  **NEAT**

    NEAT is a specific type of Genetic Algorithm. Its key innovation is speciation—it automatically groups similar individuals into different "species." These species evolve independently, which helps protect new, potentially valuable innovations from being immediately out-competed, allowing them time to be refined.

-----

## Pokèmon theory reminders
A Pokémon's success in battle is determined by a combination of several factors:

> **Types**: A Pokémon has one or two of 18 types. Type matchups dictate damage; for example, a Fire move deals double damage to a Grass Pokémon ("super-effective") but half damage to a Water Pokémon ("not very effective"). Some types are immune to others.

> **Base Stats**: The six core stats (HP, Attack, Defense, Special Attack, Special Defense, and Speed) determine a Pokémon's innate power and durability.

> **Moveset**: A Pokémon can only know four moves at a time. A well-balanced moveset is crucial for strategic options and type coverage.

> **Ability**: A passive Ability can dramatically influence the battle, such as granting an immunity or boosting stats.

> **Held Item**: A single held item can provide benefits like increasing attack power or restoring HP.

> **Nature**: A Pokémon's Nature typically boosts one stat by 10% while lowering another by 10%.

> **IVs and EVs**: These hidden mechanics customize a Pokémon's final stats.

  1. *Individual Values (IVs)* are like genes, a value from 0-31 for each stat that determines inherent potential.

  2. *Effort Values (EVs)* are training points used to manually boost stats. A Pokémon can have a maximum of 252 EVs in one stat and a total of 510 EVs across all stats.

-----

## Possible expansions

> Including items

> Including IVs in the algorithm, it's not a fact that setting them all to 31 will lead to better results (if we consider complex strategies or double battles, those who have followed competitive games a bit know that sometimes having 31 IV in speed is a disadvantage). for the simple case of the project I would say that it is irrelevant to put them all at 31.

> Implement double battles and strategic combo research to consider advanced tactics instead of just damage output (thus improving the very basic MiniMax implementation)

> You can suggest other alternatives...
-----

## How did I simulate the battles?
With this fantastic project here (actually limited to gen I-IV):
https://github.com/hiimvincent/poke-battle-sim.git