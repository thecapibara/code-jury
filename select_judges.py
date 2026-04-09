#!/usr/bin/env python3
"""
Code Jury Judge Selector
Chooses 4 random judges from judges.json and outputs their configs.
Used by both Qwen and Claude to know which judges to spawn.

Usage:
  python3 select_judges.py           # Output 4 random judges as JSON
  python3 select_judges.py --list    # List all 10 judges
  python3 select_judges --lang uk    # Use names from language profile
"""

import json
import random
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

def load_judges():
    judges_file = SCRIPT_DIR / "judges.json"
    with open(judges_file, 'r') as f:
        return json.load(f)

def load_name_pool(lang='en'):
    """Load names from language profile."""
    profile_map = {
        'uk': 'ukrainian', 'en': 'english', 'ar': 'arabic', 'ru': 'russian',
        'pl': 'polish', 'es': 'spanish', 'de': 'german', 'fr': 'french', 'it': 'italian'
    }
    profile_name = profile_map.get(lang, 'english')
    profile_file = SCRIPT_DIR / "scripts" / "judge_profiles" / f"{profile_name}.json"
    if profile_file.exists():
        with open(profile_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('name_pool', [])
    return []

def assign_names(judges, lang='en'):
    """Assign names from language pool to judges."""
    names = load_name_pool(lang)
    random.shuffle(names)
    for i, judge in enumerate(judges):
        if i < len(names):
            name_entry = names[i]
            judge['assigned_name'] = name_entry['name']
            judge['assigned_gender'] = name_entry['gender']
    return judges

def select_judges(count=4, lang='en'):
    """Select 4 random judges with names."""
    all_judges = load_judges()
    selected = random.sample(all_judges, min(count, len(all_judges)))
    return assign_names(selected, lang)

def main():
    parser = argparse.ArgumentParser(description='Select Code Jury judges')
    parser.add_argument('--count', '-n', type=int, default=4, help='Number of judges (default: 4)')
    parser.add_argument('--list', '-l', action='store_true', help='List all judges')
    parser.add_argument('--lang', type=str, default='en', help='Language for names (default: en)')
    args = parser.parse_args()

    if args.list:
        all_judges = load_judges()
        print(f"\n🎭 All available judges ({len(all_judges)}):\n")
        for j in all_judges:
            model = "🔵 Haiku" if j['model'] == 'haiku' else "🟡 Sonnet"
            print(f"  {j['emoji_male']} {j['type']} — weight: {j['vote_weight']}x — {model}")
            print(f"     Focus: {', '.join(j['focus'][:3])}")
        print()
        return

    judges = select_judges(args.count, args.lang)
    print(json.dumps(judges, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
