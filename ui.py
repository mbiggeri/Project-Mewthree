import tkinter as tk
from tkinter import scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.dialogs import Messagebox

from PIL import Image, ImageTk
import threading
import asyncio
import queue
import sys
import traceback

# Keep your original logic imports
from pokemon_genome import PokemonGenome
from evolutionary_algorithm import EvolutionaryAlgorithm
from battle_evaluator import run_final_tournament
import config as defaultConfig

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# --- Configuration for the Plotting Style ---
plt.style.use('dark_background') 

class TextRedirector:
    def __init__(self, queue: queue.Queue):
        self.queue = queue
    def write(self, text):
        self.queue.put(text)
    def flush(self):
        pass

class ChampionViewerWindow(ttk.Toplevel):
    def __init__(self, master, genome: PokemonGenome):
        super().__init__(master)
        self.genome = genome
        self.title(f"Specimen Analysis: {self.genome.name.capitalize()}")
        self.geometry("450x800")
        self.resizable(False, False)
        
        # Center the window
        self.place_window_center()

        self._create_widgets()

    def _create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Header Section
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 20))
        
        lbl_title = ttk.Label(header_frame, text=self.genome.name.capitalize(), font=("Roboto", 24, "bold"), bootstyle="inverse-primary")
        lbl_title.pack(fill=X, pady=5, ipady=5)
        
        lbl_id = ttk.Label(header_frame, text=f"Genome ID: {self.genome.genome_id}", font=("Roboto", 10), bootstyle="secondary")
        lbl_id.pack()

        # Sprite Section
        img_frame = ttk.Frame(main_frame, bootstyle="secondary")
        img_frame.pack(pady=10)
        
        try:
            # 1. Identify Primary Type
            primary_type = self.genome.types[0].lower() if self.genome.types else "normal"
            
            # 2. Try to open specific type image, otherwise fallback to normal.png
            try:
                img_raw = Image.open(f"sprites/{primary_type}.png")
            except Exception:
                # Fallback to normal if specific type is missing
                img_raw = Image.open("sprites/normal.png")

            # 3. Resize and Display
            img = img_raw.resize((140, 140), Image.Resampling.LANCZOS)
            self.sprite_image = ImageTk.PhotoImage(img) 
            ttk.Label(img_frame, image=self.sprite_image, bootstyle="secondary").pack(padx=10, pady=10)
            
        except Exception as e:
            # If even normal.png is missing, show text
            print(f"Sprite Load Error: {e}")
            ttk.Label(img_frame, text="[NO DNA IMAGE]", font=("Courier", 12), bootstyle="inverse-secondary").pack(padx=20, pady=40)
            
        # Types
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(pady=10)
        for p_type in self.genome.types:
            # Create a "Badge" look for types
            lbl = ttk.Label(type_frame, text=p_type.upper(), font=("Roboto", 9, "bold"), bootstyle="primary-inverse", padding=5)
            lbl.pack(side=LEFT, padx=3)

        # Stats Section with Visual Bars
        stats_frame = ttk.Labelframe(main_frame, text="Base Statistics", padding=15, bootstyle="info")
        stats_frame.pack(fill=X, pady=10)

        for stat, value in self.genome.stats.items():
            row = ttk.Frame(stats_frame)
            row.pack(fill=X, pady=2)
            
            # Label
            ttk.Label(row, text=stat.upper(), width=4, font=("Consolas", 9, "bold")).pack(side=LEFT)
            
            # Value
            ttk.Label(row, text=f"{value:>3}", width=4, font=("Consolas", 9)).pack(side=LEFT)
            
            # Progress Bar Visual
            # Max stat usually around 255, so we normalize loosely
            pb = ttk.Progressbar(row, value=value, maximum=200, bootstyle="success-striped", length=150)
            pb.pack(side=LEFT, fill=X, expand=True, padx=5)
            
            # EV Text
            ev = self.genome.evs.get(stat, 0)
            ttk.Label(row, text=f"+{ev} EV", width=8, font=("Consolas", 8), bootstyle="secondary").pack(side=RIGHT)

        # Info Grid (Nature/Ability)
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=X, pady=10)
        
        f_nat = ttk.Frame(info_frame, borderwidth=1, relief="solid", padding=5)
        f_nat.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        ttk.Label(f_nat, text="NATURE", font=("Roboto", 8), bootstyle="secondary").pack(anchor=W)
        ttk.Label(f_nat, text=self.genome.nature, font=("Roboto", 11, "bold")).pack(anchor=W)

        f_abil = ttk.Frame(info_frame, borderwidth=1, relief="solid", padding=5)
        f_abil.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        ttk.Label(f_abil, text="ABILITY", font=("Roboto", 8), bootstyle="secondary").pack(anchor=W)
        ttk.Label(f_abil, text=self.genome.ability, font=("Roboto", 11, "bold")).pack(anchor=W)

        # Moves
        moves_frame = ttk.Labelframe(main_frame, text="Active Move Pool", padding=10, bootstyle="warning")
        moves_frame.pack(fill=BOTH, expand=True, pady=5)
        
        for i, move in enumerate(self.genome.moves):
            btn = ttk.Button(moves_frame, text=move.title(), bootstyle="outline-warning", width=20)
            # Grid layout for moves: 2x2
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
        
        moves_frame.columnconfigure(0, weight=1)
        moves_frame.columnconfigure(1, weight=1)


# --- Main Application Window ---
class EvolutionApp(ttk.Window):
    def __init__(self, pokemon_db):
        # THEMENAME: 'cyborg', 'superhero', 'darkly' are good for games/tech
        super().__init__(themename="superhero") 
        self.title("PROJECT MEWTHREE // GENETIC LAB")
        self.geometry("1100x800")
        
        self.pokemon_db = pokemon_db
        self.champions_data = {}
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.stdout_redirector = TextRedirector(self.log_queue)
        self.param_vars = {}
        
        # Set the icon if you have one, otherwise skip
        # self.iconbitmap('icon.ico') 

        self._create_widgets()
        self.after(100, self._process_log_queue)
        self.after(100, self._process_progress_queue)

    def _create_widgets(self):
        # 1. Sidebar (Control Panel)
        # Using a darker background styling for contrast
        sidebar = ttk.Frame(self, padding=15, bootstyle="secondary")
        sidebar.pack(side=LEFT, fill=Y)
        
        # App Branding
        ttk.Label(sidebar, text="MEWTHREE", font=("Impact", 28), bootstyle="inverse-secondary").pack(anchor=W)
        ttk.Label(sidebar, text="GENETIC ALGORITHM", font=("Roboto", 10), bootstyle="inverse-secondary").pack(anchor=W, pady=(0, 20))
        
        ttk.Separator(sidebar, bootstyle="light").pack(fill=X, pady=10)

        # Setup Controls
        ttk.Label(sidebar, text="BASE ORGANISM", font=("Roboto", 10, "bold"), bootstyle="inverse-secondary").pack(anchor=W, pady=(10, 5))
        
        pokemon_list = ["Mewthree (From Scratch)"] + [name.capitalize() for name in self.pokemon_db.keys()]
        self.pokemon_var = tk.StringVar(value=pokemon_list[0])
        self.pokemon_combo = ttk.Combobox(sidebar, textvariable=self.pokemon_var, values=pokemon_list, state="readonly", bootstyle="light")
        self.pokemon_combo.pack(fill=X, pady=5)

        ttk.Label(sidebar, text="SIMULATION ENGINE", font=("Roboto", 10, "bold"), bootstyle="inverse-secondary").pack(anchor=W, pady=(20, 5))
        self.mode_var = tk.StringVar(value="simple")
        
        # Custom styled radio buttons
        ttk.Radiobutton(sidebar, text="Simple (Max-Dmg)", variable=self.mode_var, value="simple", bootstyle="light-toolbutton").pack(fill=X, pady=2)
        ttk.Radiobutton(sidebar, text="Advanced (Minimax)", variable=self.mode_var, value="advanced", bootstyle="light-toolbutton").pack(fill=X, pady=2)

        # Big Action Button
        self.start_button = ttk.Button(
            sidebar, 
            text="INITIATE EVOLUTION", 
            command=self.start_experiment, 
            bootstyle="success", 
            width=20
        )
        self.start_button.pack(pady=40, ipady=10)

        # Footer in sidebar
        ttk.Label(sidebar, text="v0.999 Unstable", font=("Consolas", 8), bootstyle="inverse-secondary").pack(side=BOTTOM, anchor=W)

        # 2. Main Content Area
        content_area = ttk.Frame(self, padding=10)
        content_area.pack(side=RIGHT, fill=BOTH, expand=True)

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(content_area, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True)

        # --- Tab 1: Real-time Logs ---
        log_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_tab, text="  SYSTEM LOGS  ")
        
        # Modern terminal look
        self.log_text = ScrolledText(log_tab, wrap=tk.WORD, font=("Consolas", 10), bootstyle="dark-round")
        self.log_text.pack(fill=BOTH, expand=True)
        
        # Progress Section
        p_frame = ttk.Frame(log_tab, padding=(0, 10, 0, 0))
        p_frame.pack(fill=X)
        
        lbl_prog = ttk.Label(p_frame, text="GENERATION PROGRESS:", font=("Roboto", 9, "bold"))
        lbl_prog.pack(side=LEFT)
        
        self.progress_label = ttk.Label(p_frame, text="0%", font=("Roboto", 9))
        self.progress_label.pack(side=RIGHT)
        
        self.progress_bar = ttk.Progressbar(p_frame, orient=HORIZONTAL, mode='determinate', bootstyle="success-striped")
        self.progress_bar.pack(side=LEFT, fill=X, expand=True, padx=10)

        # --- Tab 2: Visual Analysis (Graph) ---
        self.graph_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.graph_tab, text="  CONVERGENCE DATA  ")
        
        self.graph_figure = Figure(figsize=(5, 4), dpi=100)
        # Match Matplotlib background to the theme (dark gray usually #2b3e50 in superhero)
        self.graph_figure.patch.set_facecolor('#2b3e50') 
        self.graph_canvas = FigureCanvasTkAgg(self.graph_figure, self.graph_tab)
        self.graph_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
        self.plot_evolution_graph(None)

        # --- Tab 3: Champions ---
        champions_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(champions_tab, text="  HALL OF FAME  ")
        
        cols = ("id", "name", "fitness") 
        self.champion_tree = ttk.Treeview(champions_tab, columns=cols, show="headings", bootstyle="info")
        self.champion_tree.pack(fill=BOTH, expand=True)
        
        self.champion_tree.heading("id", text="ID")
        self.champion_tree.heading("name", text="Designation")
        self.champion_tree.heading("fitness", text="Fitness Score")
        
        self.champion_tree.column("id", width=80, anchor="center")
        self.champion_tree.column("name", width=300)
        self.champion_tree.column("fitness", width=100, anchor="e")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(champions_tab, orient=VERTICAL, command=self.champion_tree.yview)
        self.champion_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.champion_tree.bind("<Double-1>", self.on_champion_double_click)
        ttk.Label(champions_tab, text="ℹ Double-click a specimen to inspect genome.", bootstyle="secondary").pack(pady=5)

        # --- Tab 4: Parameters ---
        self.build_hyperparameter_tab()

    def build_hyperparameter_tab(self):
        param_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(param_tab, text="  CONFIGURATION  ")
        
        # Scrolled Frame for settings
        canvas = tk.Canvas(param_tab, highlightthickness=0) # Remove white border
        scrollbar = ttk.Scrollbar(param_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=10)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        param_groups = {
            "NEAT Algorithm Settings": ["COMPATIBILITY_THRESHOLD", "STAGNATION_LIMIT", "SURVIVAL_THRESHOLD", "C1_STATS", "C2_TYPES", "C3_MOVES", "C4_EVS", "C5_NATURE", "C6_ABILITY"],
            "Evolution Control": ["MINIMAX_DEPTH", "POPULATION_SIZE", "GENERATIONS", "MUTATION_RATE", "ELITISM_COUNT", "MAX_CONCURRENT_EVALUATIONS", "GAUNTLET_SIZE"],
            "Biological Constraints": ["MAX_BASE_STATS", "MAX_EVS"]
        }
        
        self.param_vars.clear()
        
        for group_name, param_list in param_groups.items():
            # Styled Group Box
            group_frame = ttk.Labelframe(scrollable_frame, text=group_name, padding=15, bootstyle="primary")
            group_frame.pack(fill="x", expand=True, pady=10)
            
            # Grid Layout for params (2 columns)
            for i, param_name in enumerate(param_list):
                row = i // 2
                col = i % 2
                
                p_frame = ttk.Frame(group_frame)
                p_frame.grid(row=row, column=col, sticky="ew", padx=10, pady=5)
                group_frame.columnconfigure(col, weight=1)
                
                default_value = getattr(defaultConfig, param_name, "")
                ttk.Label(p_frame, text=param_name.replace("_", " ").title(), font=("Roboto", 8)).pack(anchor=W)
                
                var = tk.StringVar(value=str(default_value))
                entry = ttk.Entry(p_frame, textvariable=var, bootstyle="secondary")
                entry.pack(fill=X)
                self.param_vars[param_name] = var

        reset_button = ttk.Button(scrollable_frame, text="Reset to Factory Defaults", command=self.reset_hyperparameters, bootstyle="warning-outline")
        reset_button.pack(pady=30)

    def plot_evolution_graph(self, history_data):
        self.graph_figure.clear()
        ax1 = self.graph_figure.add_subplot(111)
        
        # Styling plot for Dark Mode
        ax1.set_facecolor('#2b3e50') # Match figure background
        ax1.grid(True, color='#4e5d6c', linestyle='--')
        
        if not history_data:
            ax1.text(0.5, 0.5, 'AWAITING DATA...',
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax1.transAxes, fontsize=14, color='white')
        else:
            try:
                gens = [d['gen'] for d in history_data]
                best_fitness = [d['best_fitness'] for d in history_data]
                avg_fitness = [d['avg_fitness'] for d in history_data]
                num_species = [d['num_species'] for d in history_data]
                
                # Colors: Green for Best, Cyan for Avg, Red for Species
                p1, = ax1.plot(gens, best_fitness, '#62c462', label='Best Fitness', linewidth=2)
                p2, = ax1.plot(gens, avg_fitness, '#5bc0de', label='Avg. Fitness', linestyle='--')
                
                ax1.set_xlabel('Generation', color='white')
                ax1.set_ylabel('Fitness Score', color='white')
                ax1.tick_params(colors='white')
                
                # Secondary Axis
                ax2 = ax1.twinx()
                p3, = ax2.plot(gens, num_species, '#d9534f', label='Num. Species', linestyle=':')
                ax2.set_ylabel('Species Count', color='#d9534f')
                ax2.tick_params(axis='y', labelcolor='#d9534f')
                
                # Legend
                lines = [p1, p2, p3]
                ax1.legend(lines, [l.get_label() for l in lines], loc='upper left', facecolor='#2b3e50', edgecolor='white', labelcolor='white')
                
            except Exception as e:
                ax1.text(0.5, 0.5, f'Plotting Error: {e}', color='red')

        self.graph_figure.tight_layout()
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
        current_config["ABILITY_POOL"] = defaultConfig.ABILITY_POOL
        current_config["GAUNTLET"] = defaultConfig.GAUNTLET
        current_config["SIMPLE_GAUNTLET"] = defaultConfig.SIMPLE_GAUNTLET
        return current_config

    def start_experiment(self):
        self.start_button.config(state=DISABLED, text="SIMULATION RUNNING...")
        self.log_text.delete('1.0', tk.END)
        self.champion_tree.delete(*self.champion_tree.get_children())
        self.champions_data.clear()
        self.notebook.select(0) # Go to Logs
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
            
        self.log_text.insert(tk.END, ">>> INITIALIZING EXPERIMENT THREAD...\n")
        
        def progress_callback(completed, total):
            self.progress_queue.put((completed, total))
            
        self.worker_thread = threading.Thread(
            target=self.run_experiment_thread,
            args=(self.base_pokemon, self.evolution_mode, self.current_config_data, progress_callback),
            daemon=True
        )
        self.worker_thread.start()

    def run_experiment_thread(self, base_pokemon_data, mode, config_data, progress_cb):
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = self.stdout_redirector
        sys.stderr = self.stdout_redirector
        tournament_winner = None
        species_champions = []
        history_data = []
        try:
            print(f">>> TARGET: {base_pokemon_data['name'].upper()}")
            print(f">>> MODE: {mode.upper()}")
            print(">>> LOADING GENETIC PARAMETERS...")
            ea = EvolutionaryAlgorithm(base_pokemon_data, mode, config_data)
            species_champions, history_data = asyncio.run(ea.run(progress_cb))
            if species_champions:
                print("\n>>> EVOLUTION COMPLETE.")
                print(">>> INITIATING FINAL TOURNAMENT BRACKET...")
                tournament_winner = run_final_tournament(species_champions, config_data)
                if tournament_winner:
                    print(f"\n>>> ULTIMATE CHAMPION IDENTIFIED: ID {tournament_winner.genome_id}")
                else:
                    print(">>> RESULT: DRAW.")
            else:
                print(">>> FAILURE: NO VIABLE OFFSPRING.")
        except Exception as e:
            print("\n>>> CRITICAL SYSTEM ERROR <<<")
            print(f"Error: {e}")
            print(traceback.format_exc())
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            self.after(0, self.finish_experiment, species_champions, tournament_winner, history_data)

    def _process_progress_queue(self):
        try:
            while True:
                completed, total = self.progress_queue.get_nowait()
                self.progress_bar['maximum'] = total
                self.progress_bar['value'] = completed
                pct = int((completed / total) * 100) if total > 0 else 0
                self.progress_label['text'] = f"{pct}% ({completed}/{total})"
        except queue.Empty:
            pass
        self.after(100, self._process_progress_queue)
        
    def finish_experiment(self, champions, winner, history_data):
        print(">>> UPDATE: UI SYNC COMPLETE.")
        self.start_button.config(state=NORMAL, text="INITIATE EVOLUTION")

        # Populate champions list
        for champ in champions:
            self.champions_data[champ.genome_id] = champ
            self.champion_tree.insert(
                '', 
                'end', 
                iid=champ.genome_id, 
                values=(champ.genome_id, champ.name.capitalize(), f"{champ.fitness:.0f}")
            )

        # Plot the data
        self.plot_evolution_graph(history_data)
        self.notebook.select(self.graph_tab) 
        
        if winner:
            Messagebox.show_info(message=f"New Champion Found: ID {winner.genome_id}", title="Evolution Success")
            ChampionViewerWindow(self, winner)
        elif champions:
            ChampionViewerWindow(self, champions[0])

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