# ui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog
from PIL import Image, ImageTk
import threading
import asyncio
import queue
import sys
import traceback

from pokemon_genome import PokemonGenome
from evolutionary_algorithm import EvolutionaryAlgorithm
from battle_evaluator import run_final_tournament
import config as defaultConfig

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TextRedirector:
    def __init__(self, queue: queue.Queue):
        self.queue = queue
    def write(self, text):
        self.queue.put(text)
    def flush(self):
        pass

class ChampionViewerWindow(tk.Toplevel):
    def __init__(self, master, genome: PokemonGenome):
        super().__init__(master)
        self.genome = genome
        self.title(f"Evolved {self.genome.name.capitalize()} (ID: {self.genome.genome_id})")
        self.geometry("400x700")
        self.resizable(False, False)
        self.grab_set()
        self.transient(master)
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text=f"Champion: {self.genome.name.capitalize()}", 
                  font=("Helvetica", 18, "bold")).pack(pady=(0, 10))
        try:
            primary_type = self.genome.types[0] if self.genome.types else "normal"
            sprite_path = f"sprites/{primary_type}.png"
            img = Image.open(sprite_path).resize((128, 128), Image.Resampling.LANCZOS)
            self.sprite_image = ImageTk.PhotoImage(img) 
            ttk.Label(main_frame, image=self.sprite_image).pack(pady=10)
        except Exception:
            ttk.Label(main_frame, text="[Sprite not found]").pack(pady=10)
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(pady=10)
        ttk.Label(type_frame, text="Types:", font=("Helvetica", 12, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        self.type_images = []
        for p_type in self.genome.types:
            try:
                img = Image.open(f"icons/{p_type}.png").resize((64, 28))
                self.type_images.append(ImageTk.PhotoImage(img))
                ttk.Label(type_frame, image=self.type_images[-1]).pack(side=tk.LEFT, padx=5)
            except FileNotFoundError:
                ttk.Label(type_frame, text=p_type.capitalize()).pack(side=tk.LEFT, padx=5)

        details_frame = ttk.Labelframe(main_frame, text="Details", padding=10)
        details_frame.pack(fill=tk.X, expand=True, pady=10)
        
        ttk.Label(details_frame, text=f"Nature: {self.genome.nature}", font=("Helvetica", 11)).pack(anchor="w")
        ttk.Label(details_frame, text=f"Ability: {self.genome.ability}", font=("Helvetica", 11)).pack(anchor="w", pady=(5,0))
        
        # --- Display the KO score in the pop-up ---
        gauntlet_size = len(defaultConfig.GAUNTLET)
        ttk.Label(details_frame, text=f"Gauntlet KOs: {self.genome.gauntlet_kos} / {gauntlet_size}", 
                  font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(5,0))

        stats_text = "\nBase Stats (EVs)\n" + "-"*20
        for stat, value in self.genome.stats.items():
            ev = self.genome.evs.get(stat, 0)
            stats_text += f"\n{stat.upper():<4}: {value:<4} ({ev} EVs)"
        ttk.Label(details_frame, text=stats_text, font=("Courier", 10), justify=tk.LEFT).pack(anchor="w", pady=5)
        moves_frame = ttk.Labelframe(main_frame, text="Moveset", padding=10)
        moves_frame.pack(fill=tk.X, expand=True, pady=10)
        for move in self.genome.moves:
            ttk.Label(moves_frame, text=f"• {move.title()}", font=("Helvetica", 11)).pack(anchor="w")


# --- Main Application Window ---
class EvolutionApp(tk.Tk):
    def __init__(self, pokemon_db):
        super().__init__()
        self.title("Project Mewthree - Evolution Dashboard")
        self.geometry("900x700")
        self.pokemon_db = pokemon_db
        self.champions_data = {}
        self.log_queue = queue.Queue()
        self.stdout_redirector = TextRedirector(self.log_queue)
        self.param_vars = {}
        self._create_widgets()
        self.after(100, self._process_log_queue)

    def _create_widgets(self):
        control_frame = ttk.Frame(self, padding="10", width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        control_frame.pack_propagate(False)
        output_frame = ttk.Frame(self, padding="10")
        output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        ttk.Label(control_frame, text="Experiment Setup", font=("Helvetica", 16, "bold")).pack(pady=10, anchor="w")
        ttk.Label(control_frame, text="Choose Pokémon:").pack(anchor="w", pady=(10, 0))
        pokemon_list = ["Mewthree (From Scratch)"] + [name.capitalize() for name in self.pokemon_db.keys()]
        self.pokemon_var = tk.StringVar(value=pokemon_list[0])
        self.pokemon_combo = ttk.Combobox(control_frame, textvariable=self.pokemon_var, values=pokemon_list, state="readonly")
        self.pokemon_combo.pack(anchor="w", fill=tk.X, pady=5)
        ttk.Label(control_frame, text="Choose Mode:").pack(anchor="w", pady=(10, 0))
        self.mode_var = tk.StringVar(value="simple")
        ttk.Radiobutton(control_frame, text="Simple Mode (Fast, Max-Damage AI)", variable=self.mode_var, value="simple").pack(anchor="w")
        ttk.Radiobutton(control_frame, text="Advanced Mode (Slow, Minimax AI)", variable=self.mode_var, value="advanced").pack(anchor="w")
        self.start_button = ttk.Button(control_frame, text="Start Evolution", command=self.start_experiment)
        self.start_button.pack(pady=20, fill=tk.X, ipady=5)
        
        self.notebook = ttk.Notebook(output_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        log_tab = ttk.Frame(self.notebook)
        self.log_text = scrolledtext.ScrolledText(log_tab, wrap=tk.WORD, font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.notebook.add(log_tab, text="Experiment Log")

        # --- Champions Tab ---
        champions_tab = ttk.Frame(self.notebook)
        self.notebook.add(champions_tab, text="Final Champions")
        
        cols = ("id", "name", "fitness", "kos") 
        self.champion_tree = ttk.Treeview(champions_tab, columns=cols, show="headings")
        self.champion_tree.pack(fill=tk.BOTH, expand=True)
        
        self.champion_tree.heading("id", text="Genome ID")
        self.champion_tree.heading("name", text="Name")
        self.champion_tree.heading("fitness", text="Fitness")
        self.champion_tree.heading("kos", text="Gauntlet KOs") # New heading
        
        self.champion_tree.column("id", width=80, anchor="center")
        self.champion_tree.column("name", width=150)
        self.champion_tree.column("fitness", width=100, anchor="e")
        self.champion_tree.column("kos", width=100, anchor="center") # New column
        
        self.champion_tree.bind("<Double-1>", self.on_champion_double_click)
        ttk.Label(champions_tab, text="Double-click a champion to view details.").pack(pady=5)
        # --- END OF Champions Tab ---

        self.build_hyperparameter_tab()
        self.graph_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_tab, text="Convergence Graph")
        self.graph_figure = Figure(figsize=(5, 4), dpi=100)
        self.graph_canvas = FigureCanvasTkAgg(self.graph_figure, self.graph_tab)
        self.graph_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.plot_evolution_graph(None)

    def build_hyperparameter_tab(self):
        param_tab = ttk.Frame(self.notebook)
        self.notebook.add(param_tab, text="Hyperparameters")
        canvas = tk.Canvas(param_tab)
        scrollbar = ttk.Scrollbar(param_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="10")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        param_groups = {
            "NEAT Parameters": ["COMPATIBILITY_THRESHOLD", "STAGNATION_LIMIT", "SURVIVAL_THRESHOLD", "C1_STATS", "C2_TYPES", "C3_MOVES", "C4_EVS", "C5_NATURE"],
            "Evolution Parameters": ["MINIMAX_DEPTH", "POPULATION_SIZE", "GENERATIONS", "MUTATION_RATE", "ELITISM_COUNT", "MAX_CONCURRENT_EVALUATIONS"],
            "Pokémon Constraints": ["MAX_BASE_STATS", "MAX_EVS"]
        }
        self.param_vars.clear()
        for group_name, param_list in param_groups.items():
            group_frame = ttk.Labelframe(scrollable_frame, text=group_name, padding="10")
            group_frame.pack(fill="x", expand=True, pady=10, padx=5)
            for param_name in param_list:
                default_value = getattr(defaultConfig, param_name, "")
                row_frame = ttk.Frame(group_frame)
                row_frame.pack(fill="x", pady=2)
                ttk.Label(row_frame, text=f"{param_name}:").pack(side="left", padx=5)
                var = tk.StringVar(value=str(default_value))
                entry = ttk.Entry(row_frame, textvariable=var, width=15)
                entry.pack(side="right", padx=5)
                self.param_vars[param_name] = var
        reset_button = ttk.Button(scrollable_frame, text="Reset to Defaults", command=self.reset_hyperparameters)
        reset_button.pack(pady=20, padx=5)

    def plot_evolution_graph(self, history_data):
        self.graph_figure.clear()
        if not history_data:
            ax = self.graph_figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Run an experiment to see graph data.',
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, fontsize=12)
            self.graph_canvas.draw()
            return
        try:
            gens = [d['gen'] for d in history_data]
            best_fitness = [d['best_fitness'] for d in history_data]
            avg_fitness = [d['avg_fitness'] for d in history_data]
            num_species = [d['num_species'] for d in history_data]
            ax1 = self.graph_figure.add_subplot(111)
            ax1.set_xlabel('Generation')
            ax1.plot(gens, best_fitness, 'g-', label='Best Fitness', linewidth=2)
            ax1.plot(gens, avg_fitness, 'b--', label='Avg. Fitness')
            ax1.set_ylabel('Fitness', color='b')
            ax1.tick_params(axis='y', labelcolor='b')
            ax2 = ax1.twinx()
            ax2.plot(gens, num_species, 'r:', label='Num. Species')
            ax2.set_ylabel('Species Count', color='r')
            ax2.tick_params(axis='y', labelcolor='r')
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            self.graph_figure.tight_layout()
        except Exception as e:
            ax = self.graph_figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Error plotting graph:\n{e}',
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, color='red')
        self.graph_canvas.draw()

    def reset_hyperparameters(self):
        for param_name, var in self.param_vars.items():
            default_value = getattr(defaultConfig, param_name, "")
            var.set(str(default_value))

    def get_current_config(self) -> dict:
        current_config = {}
        for param_name, var in self.param_vars.items():
            value_str = var.get()
            try: value = int(value_str)
            except ValueError:
                try: value = float(value_str)
                except ValueError: value = value_str
            current_config[param_name] = value
        current_config["MOVE_POOL"] = defaultConfig.MOVE_POOL
        current_config["POKEMON_TYPES"] = defaultConfig.POKEMON_TYPES
        current_config["NATURES"] = defaultConfig.NATURES
        current_config["GAUNTLET"] = defaultConfig.GAUNTLET
        current_config["SIMPLE_GAUNTLET"] = defaultConfig.SIMPLE_GAUNTLET
        return current_config

    def start_experiment(self):
        self.start_button.config(state=tk.DISABLED, text="Evolution in Progress...")
        self.log_text.delete('1.0', tk.END)
        self.champion_tree.delete(*self.champion_tree.get_children())
        self.champions_data.clear()
        self.notebook.select(0)
        self.plot_evolution_graph(None)
        selected_pokemon_name = self.pokemon_var.get()
        self.evolution_mode = self.mode_var.get()
        self.current_config_data = self.get_current_config()
        if selected_pokemon_name == "Mewthree (From Scratch)":
            self.base_pokemon = {"name": "custom_god_pokemon", "ability": "Pressure"}
        else:
            name_key = selected_pokemon_name.lower()
            self.base_pokemon = self.pokemon_db[name_key]
            self.base_pokemon['name'] = name_key
        self.log_text.insert(tk.END, "Starting new experiment thread...\n")
        self.worker_thread = threading.Thread(
            target=self.run_experiment_thread,
            args=(self.base_pokemon, self.evolution_mode, self.current_config_data),
            daemon=True
        )
        self.worker_thread.start()

    def run_experiment_thread(self, base_pokemon_data, mode, config_data):
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = self.stdout_redirector
        sys.stderr = self.stdout_redirector
        tournament_winner = None
        species_champions = []
        history_data = []
        try:
            print(f"\nStarting {mode} evolution for {base_pokemon_data['name'].capitalize()}...")
            print("Using current Hyperparameters.")
            ea = EvolutionaryAlgorithm(base_pokemon_data, mode, config_data)
            species_champions, history_data = asyncio.run(ea.run())
            if species_champions:
                print("\n--- Evolution Complete. Starting Final Tournament ---")
                tournament_winner = run_final_tournament(species_champions, config_data)
                if tournament_winner:
                    print(f"\n--- ULTIMATE CHAMPION IS ID {tournament_winner.genome_id} ---")
                else:
                    print("Tournament did not produce a clear winner.")
            else:
                print("Evolution did not produce any champions.")
        except Exception as e:
            print("\n--- AN ERROR OCCURRED IN THE EVOLUTION THREAD ---")
            print(f"Error: {e}")
            print(traceback.format_exc())
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            self.after(0, self.finish_experiment, species_champions, tournament_winner, history_data)

    def finish_experiment(self, champions, winner, history_data):
        print("--- Experiment finished. Updating UI. ---")
        self.start_button.config(state=tk.NORMAL, text="Start Evolution")

        # Populate champions list
        for champ in champions:
            self.champions_data[champ.genome_id] = champ
            self.champion_tree.insert(
                '', 
                'end', 
                iid=champ.genome_id, 
                values=(champ.genome_id, champ.name.capitalize(), f"{champ.fitness:.0f}", champ.gauntlet_kos)
            )

        # Plot the data
        self.plot_evolution_graph(history_data)
        self.notebook.select(self.graph_tab) # Switch to graph
        
        # Open champion viewer
        if winner:
            print(f"Opening viewer for ultimate champion: ID {winner.genome_id}")
            ChampionViewerWindow(self, winner)
        elif champions:
            print("No single winner, opening viewer for the first champion.")
            ChampionViewerWindow(self, champions[0])
        else:
            print("No champions were generated.")

    def on_champion_double_click(self, event):
        selected_iid = self.champion_tree.focus()
        if selected_iid:
            genome_id = int(selected_iid)
            genome = self.champions_data.get(genome_id)
            if genome:
                ChampionViewerWindow(self, genome)

    def _process_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, msg)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        self.after(100, self._process_log_queue)