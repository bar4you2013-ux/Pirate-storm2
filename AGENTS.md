# Project instructions

- Project: «Гроза морей» / Pirate Storm. Respond to the owner in Russian.
- Main desktop entry point: `groza_morey.py`, based on v0.27 ghost ship, markets and resource icons; rendering enhanced in visual_art.py.
- Stack: Python 3.10+ and Pygame 2.6.1. Install: `python -m pip install -r requirements.txt`.
- Focus on gameplay mechanics and logic. Do not migrate to Godot or redesign graphics unless requested.
- Keep `archive/` unchanged: these are historical originals, including duplicate copies.
- `mobile/index.html` is a separate prototype, not the full desktop game.
- Preserve Russian UI, existing controls, resources, mines, colony construction, trade, ghost ship, markets, resource icons and saves (load versions 23, 26 and 27).
- Sounds are MP3 files next to the main script; sprites can be embedded in the script. Missing audio must not break gameplay.
- Verify syntax with `python -m py_compile groza_morey.py`.
- Headless checks: use SDL_VIDEODRIVER=dummy and SDL_AUDIODRIVER=dummy. Do not describe headless checks as full gameplay validation.
- For mechanic changes, run focused meaningful checks, update documentation and report actual results.
- Make future changes in a branch and prepare a pull request. Avoid merging automatically unless explicitly requested.
- Never commit runtime saves, logs, credentials or Python environments.

- `visual_art.py` contains cached procedural artwork; keep rendering separate from gameplay state and use local seeded RNG for decoration.
