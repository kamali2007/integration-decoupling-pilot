import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

nb_path = Path(__file__).resolve().parent.parent / "experiments" / "integration_experiment.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Validating {len(nb['cells'])} cells in {nb_path.name}...")
global_ctx = {"__file__": str(nb_path)}
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        code = "".join(cell["source"])
        exec(code, global_ctx)

print("All Jupyter notebook code cells executed successfully without errors!")
