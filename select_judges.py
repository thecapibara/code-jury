#!/usr/bin/env python3
"""
Code Jury Judge Selector
Chooses 4 random judges from judges.json with localized names.

Usage:
  python3 select_judges.py                            # Balanced mode (2 sonnet + 2 haiku)
  python3 select_judges.py --mode lightning           # All haiku (4x Haiku — cheap & fast)
  python3 select_judges.py --mode thorough            # All sonnet (4x Sonnet — best quality)
  python3 select_judges.py --list                     # List all judges
  python3 select_judges.py --lang uk                  # Ukrainian names
"""

import json
import random
import argparse
from pathlib import Path

# Resolve path relative to this script's location
SCRIPT_DIR = Path(__file__).parent.resolve()

# judge_profiles is next to this script (after install) or in .claude/skills/vote/scripts/ (in repo)
PROFILES_DIR = SCRIPT_DIR / "judge_profiles"
if not PROFILES_DIR.exists():
    PROFILES_DIR = SCRIPT_DIR / ".claude" / "skills" / "vote" / "scripts" / "judge_profiles"

# judges.json is next to this script (after install) or in repo root
JUDGES_FILE = SCRIPT_DIR / "judges.json"
if not JUDGES_FILE.exists():
    JUDGES_FILE = SCRIPT_DIR.parent.resolve() / "judges.json"

MODES = {
    "lightning": "haiku",   # All 4 haiku — cheap & fast
    "balanced": None,       # Respect defaults, enforce 2 sonnet + 2 haiku
    "thorough": "sonnet",   # All 4 sonnet — best quality
}


def load_judges():
    with open(JUDGES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_name_pool(lang='en'):
    """Load names and localized personalities from language profile."""
    profile_map = {
        'uk': 'ukrainian', 'en': 'english', 'ar': 'arabic', 'ru': 'russian',
        'pl': 'polish', 'es': 'spanish', 'de': 'german', 'fr': 'french', 'it': 'italian'
    }
    profile_name = profile_map.get(lang, 'english')
    profile_file = PROFILES_DIR / f"{profile_name}.json"
    if profile_file.exists():
        with open(profile_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('name_pool', []), data.get('personalities', [])
    return [], []


def apply_localization(judges, lang='en'):
    """Apply localized names, titles, and emojis from language pool."""
    names, localized_personalities = load_name_pool(lang)
    # Ensure unique names for selected judges
    random.shuffle(names)
    assigned_names = set()
    unique_names = []
    for name_entry in names:
        if name_entry['name'] not in assigned_names:
            unique_names.append(name_entry)
            assigned_names.add(name_entry['name'])
        if len(unique_names) >= len(judges):
            break
    names = unique_names

    # Build lookup: type -> localized personality
    personality_lookup = {}
    for p in localized_personalities:
        personality_lookup[p['type']] = p

    for i, judge in enumerate(judges):
        judge_type = judge['type']
        localized = personality_lookup.get(judge_type, {})

        # Override with localized data if available
        if localized:
            judge['title_male'] = localized.get('title_male', judge.get('title_male', ''))
            judge['title_female'] = localized.get('title_female', judge.get('title_female', ''))
            judge['emoji_male'] = localized.get('emoji_male', judge.get('emoji_male', ''))
            judge['emoji_female'] = localized.get('emoji_female', judge.get('emoji_female', ''))
            judge['focus'] = localized.get('focus', judge.get('focus', []))
            # Localized profiles may have different weights — keep judges.json as source of truth for weights
            # judge['vote_weight'] = localized.get('vote_weight', judge.get('vote_weight', 1.0))

        # Assign name
        if i < len(names):
            name_entry = names[i]
            judge['assigned_name'] = name_entry['name']
            judge['assigned_gender'] = name_entry['gender']
        else:
            judge['assigned_name'] = judge['name']  # fallback to judge type name
            judge['assigned_gender'] = 'male'

    return judges


def apply_mode(judges, mode='balanced'):
    """Force model based on quality mode, with balanced enforcing 2+2 split."""
    forced_model = MODES.get(mode)

    if forced_model:
        # lightning or thorough — override all
        for judge in judges:
            judge['model'] = forced_model
    elif mode == 'balanced':
        # Enforce 2 sonnet + 2 haiku split
        sonnet_idx = [i for i, j in enumerate(judges) if j.get('model') == 'sonnet']
        haiku_idx = [i for i, j in enumerate(judges) if j.get('model') != 'sonnet']

        # Need exactly 2 sonnet and 2 haiku from our 4 judges
        # Convert judges to reach 2+2 split (no duplicates — same judge objects)
        while len(sonnet_idx) < 2:
            # Need more sonnet: convert a haiku judge (pick first available)
            idx = haiku_idx.pop(0)
            judges[idx]['model'] = 'sonnet'
            sonnet_idx.append(idx)

        while len(haiku_idx) < 2:
            # Need more haiku: convert a sonnet judge (pick first available)
            idx = sonnet_idx.pop(0)
            judges[idx]['model'] = 'haiku'
            haiku_idx.append(idx)

        # Reorder: sonnet first, then haiku
        judges = [judges[i] for i in sonnet_idx[:2] + haiku_idx[:2]]

    return judges


def select_judges(count=4, lang='en', mode='balanced'):
    """Select judges with localization and mode."""
    all_judges = load_judges()
    selected = random.sample(all_judges, min(count, len(all_judges)))
    selected = apply_mode(selected, mode)
    return apply_localization(selected, lang)


def main():
    parser = argparse.ArgumentParser(description='Select Code Jury judges')
    parser.add_argument('--count', '-n', type=int, default=4)
    parser.add_argument('--list', '-l', action='store_true')
    parser.add_argument('--lang', type=str, default='en')
    parser.add_argument('--mode', '-m', type=str, default='balanced',
                       choices=['lightning', 'balanced', 'thorough'],
                       help='lightning=4xHaiku, balanced=2xSonnet+2xHaiku, thorough=4xSonnet')
    args = parser.parse_args()

    if args.list:
        all_judges = load_judges()
        print(f"\n🎭 All available judges ({len(all_judges)}):\n")
        for j in all_judges:
            model = "🔵 Haiku" if j['model'] == 'haiku' else "🟡 Sonnet"
            print(f"  {j['emoji_male']} {j['name']} — weight: {j['vote_weight']}x — {model}")
            print(f"     Focus: {', '.join(j['focus'][:3])}")
        print()
        return

    judges = select_judges(args.count, args.lang, args.mode)
    print(json.dumps(judges, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
