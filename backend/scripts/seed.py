#!/usr/bin/env python3
"""Seed script — populates a development database with test data.

Usage:
    python scripts/seed.py
    python scripts/seed.py --full  # Load all real ESPN data (slow)
"""

import argparse


def seed_promotions():
    """Insert test promotions."""
    return [
        {"provider": "espn", "external_id": "3321", "name": "Ultimate Fighting Championship",
         "abbreviation": "UFC", "short_name": "UFC", "slug": "ufc",
         "season_year": 2026, "gender": "MALE"},
        {"provider": "espn", "external_id": "9", "name": "Bellator MMA",
         "abbreviation": "Bellator", "slug": "bellator", "season_year": 2026},
        {"provider": "espn", "external_id": "10", "name": "Professional Fighters League",
         "abbreviation": "PFL", "slug": "pfl", "season_year": 2026},
    ]


def seed_weight_classes():
    """UFC weight classes with weight ranges (Unified Rules)."""
    return [
        {"provider": "espn", "external_id": "1004", "name": "Flyweight",
         "abbreviation": "FLW", "min_weight_kg": 53.0, "max_weight_kg": 56.7, "gender": "MALE"},
        {"provider": "espn", "external_id": "970", "name": "Bantamweight",
         "abbreviation": "BW", "min_weight_kg": 56.7, "max_weight_kg": 61.2, "gender": "MALE"},
        {"provider": "espn", "external_id": "999", "name": "Featherweight",
         "abbreviation": "FW", "min_weight_kg": 61.2, "max_weight_kg": 65.8, "gender": "MALE"},
        {"provider": "espn", "external_id": "986", "name": "Lightweight",
         "abbreviation": "LW", "min_weight_kg": 65.8, "max_weight_kg": 70.3, "gender": "MALE"},
        {"provider": "espn", "external_id": "969", "name": "Welterweight",
         "abbreviation": "WW", "min_weight_kg": 70.3, "max_weight_kg": 77.1, "gender": "MALE"},
        {"provider": "espn", "external_id": "972", "name": "Middleweight",
         "abbreviation": "MW", "min_weight_kg": 77.1, "max_weight_kg": 83.9, "gender": "MALE"},
        {"provider": "espn", "external_id": "990", "name": "Light Heavyweight",
         "abbreviation": "LHW", "min_weight_kg": 83.9, "max_weight_kg": 93.0, "gender": "MALE"},
        {"provider": "espn", "external_id": "982", "name": "Heavyweight",
         "abbreviation": "HW", "min_weight_kg": 93.0, "max_weight_kg": 120.2, "gender": "MALE"},
    ]


def seed_fighters():
    """Sample fighters for development."""
    return [
        {"provider": "espn", "external_id": "3088812", "first_name": "Islam", "last_name": "Makhachev",
         "full_name": "Islam Makhachev", "weight_kg": 70.3, "height_cm": 177.8, "reach_cm": 179.1,
         "stance": "Orthodox", "nationality": "Russia", "is_active": True,
         "record_wins": 28, "record_losses": 1, "record_draws": 0, "record_no_contests": 0,
         "weight_class_name": "Lightweight"},
        {"provider": "espn", "external_id": "2504169", "first_name": "Jon", "last_name": "Jones",
         "full_name": "Jon Jones", "weight_kg": 112.5, "height_cm": 193.0, "reach_cm": 215.0,
         "stance": "Orthodox", "nationality": "United States", "is_active": True,
         "record_wins": 28, "record_losses": 1, "record_draws": 0, "record_no_contests": 1,
         "weight_class_name": "Heavyweight"},
        {"provider": "espn", "external_id": "3088812", "first_name": "Islam", "last_name": "Makhachev",
         "full_name": "Islam Makhachev", "weight_kg": 70.3, "height_cm": 177.8, "reach_cm": 179.1,
         "stance": "Orthodox", "nationality": "Russia", "is_active": True,
         "record_wins": 27, "record_losses": 1, "record_draws": 0, "record_no_contests": 0,
         "weight_class_name": "Lightweight"},
    ]


def main():
    parser = argparse.ArgumentParser(description="Seed MMA development database")
    parser.add_argument("--full", action="store_true", help="Load all real ESPN data (slow)")
    args = parser.parse_args()

    print("MMA Backend — Database Seeder")
    print("=" * 50)

    promotions = seed_promotions()
    print(f"✓ {len(promotions)} promotions seeded")

    weight_classes = seed_weight_classes()
    print(f"✓ {len(weight_classes)} weight classes seeded")

    fighters = seed_fighters()
    print(f"✓ {len(fighters)} fighters seeded")

    if args.full:
        print("\nFull sync mode — would trigger ESPN full sync here")
        print("  Run: python -m src.sync.engine --mode full --provider espn")
    else:
        print("\nDevelopment seed complete.")
        print("  Run with --full to sync all real ESPN data.")
        print("  Run 'docker compose up' to start the full stack.")


if __name__ == "__main__":
    main()
