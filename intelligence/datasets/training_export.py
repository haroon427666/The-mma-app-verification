"""Training Export — exports datasets to Parquet/NumPy for ML consumption.

Usage:
    python -m intelligence.datasets.training_export --format parquet
"""

import argparse
import numpy as np
import json
from typing import Optional

from intelligence.datasets.fighter_dataset import FighterDatasetBuilder, FightDatasetBuilder
from intelligence.feature_store.serializer import save_dataset, save_json


def export_fighter_dataset(
    fighters: list[dict],
    output_path: str,
    feature_list: list[str] | None = None,
) -> dict:
    """Export fighter feature matrix to disk. Returns metadata."""
    builder = FighterDatasetBuilder()
    features = builder.build_with_embeddings(fighters)

    ids = [f.get("id", str(i)) for i, f in enumerate(fighters)]
    save_dataset(features, np.zeros(len(fighters)), ids,
                 [f"dim_{i}" for i in range(features.shape[1])], output_path)

    metadata = {
        "rows": len(fighters),
        "cols": features.shape[1],
        "dtype": str(features.dtype),
        "path": output_path,
    }
    save_json(metadata, output_path.replace(".npz", "_meta.json"))
    return metadata


def export_fight_dataset(
    fights: list[dict],
    fighter_lookup: dict[str, dict],
    output_path: str,
) -> dict:
    """Export fight matchup dataset with win/loss labels."""
    builder = FightDatasetBuilder()
    features, labels = builder.build(fights, fighter_lookup)

    ids = [f.get("id", str(i)) for i, f in enumerate(fights)]
    save_dataset(features, labels, ids,
                 [f"matchup_{i}" for i in range(features.shape[1])], output_path)

    metadata = {
        "rows": len(fights),
        "cols": features.shape[1],
        "label_distribution": {
            "a_wins": int(np.sum(labels)),
            "b_wins": int(len(labels) - np.sum(labels)),
        },
        "path": output_path,
    }
    save_json(metadata, output_path.replace(".npz", "_meta.json"))
    return metadata


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Export training datasets")
    parser.add_argument("--input", required=True, help="JSON file with fighters/fights")
    parser.add_argument("--type", choices=["fighters", "fights"], required=True)
    parser.add_argument("--output", required=True, help="Output .npz path")
    args = parser.parse_args()

    data = json.load(open(args.input))

    if args.type == "fighters":
        export_fighter_dataset(data.get("fighters", []), args.output)
    else:
        lookup = {f["id"]: f for f in data.get("fighters", [])}
        export_fight_dataset(data.get("fights", []), lookup, args.output)

    print(f"Exported → {args.output}")


if __name__ == "__main__":
    main()
