import asyncio
import sys
import nest_asyncio

from ui import EvolutionApp
from pokemon_data import POKEMON_DATABASE

# Apply nest_asyncio once at the start
nest_asyncio.apply()

if __name__ == "__main__":
    # The application is driven entirely by the UI.
    # We pass the database to the UI so it can populate
    # the "Choose Pokemon" dropdown.
    try:
        app = EvolutionApp(POKEMON_DATABASE)
        app.mainloop()
    except Exception as e:
        print(f"Fatal application error: {e}")
        print("Please restart the application.")
        sys.exit(1)