#!/usr/bin/env python3
"""
Code Jury Judge Selector
Chooses 4 random judges from judges.json with localized names.

Usage:
  python3 select_judges.py                                  # Balanced mode (2 sonnet + 2 haiku)
  python3 select_judges.py --mode lightning                 # All haiku (4x Haiku / Flash-Lite)
  python3 select_judges.py --mode thorough                  # All sonnet (4x Sonnet / Pro)
  python3 select_judges.py --list                           # List all judges
  python3 select_judges.py --lang uk                        # Ukrainian names
  python3 select_judges.py --platform gemini                # Use Gemini model names
  python3 select_judges.py --platform gemini --mode flash   # 4x Gemini Flash
"""

import json
import random
import argparse
import sys
import copy
from collections import deque
from pathlib import Path

# Resolve path relative to this script's location
SCRIPT_DIR = Path(__file__).parent.resolve()

# judge_profiles is next to this script (after install) or in .claude/skills/vote/scripts/ (in repo)
PROFILES_DIR = SCRIPT_DIR / "judge_profiles"
if not PROFILES_DIR.exists():
    PROFILES_DIR = SCRIPT_DIR / ".claude" / "skills" / "vote" / "scripts" / "judge_profiles"

# judge_review_guides is in scripts/ (shared across platforms)
GUIDES_DIR = SCRIPT_DIR / "judge_review_guides"
if not GUIDES_DIR.exists():
    GUIDES_DIR = SCRIPT_DIR / ".claude" / "skills" / "vote" / "scripts" / "judge_review_guides"

# judges.json is next to this script (after install) or in repo root
JUDGES_FILE = SCRIPT_DIR / "judges.json"
if not JUDGES_FILE.exists():
    JUDGES_FILE = SCRIPT_DIR.parent.resolve() / "judges.json"

# ─── Quality modes ───
# Claude/Qwen modes: sonnet (expert) + haiku (lightweight)
MODES_CLAUDE_QWEN = {
    "lightning": "haiku",   # All 4 haiku — cheap & fast
    "balanced": None,       # Respect defaults, enforce 2 sonnet + 2 haiku
    "thorough": "sonnet",   # All 4 sonnet — best quality
}

# Gemini modes: pro (expert), flash (balanced), flash-lite (lightweight)
MODES_GEMINI = {
    "lightning": "flash-lite",  # All 4 Flash-Lite — cheapest & fastest
    "flash": "flash",           # All 4 Flash — optimal
    "balanced": None,           # Respect defaults, enforce 2 Pro + 2 Flash
    "thorough": "pro",          # All 4 Pro — best quality
}


def load_judges():
    """Load judges from JSON file. Exits with clear message on failure."""
    try:
        with open(JUDGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: judges.json not found at {JUDGES_FILE}.", file=sys.stderr)
        print("Run install.sh first, or ensure you're in the project directory.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: judges.json is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def load_name_pool(lang='en'):
    """Load names and localized personalities from language profile."""
    profile_map = {
        'uk': 'ukrainian', 'en': 'english', 'ar': 'arabic', 'ru': 'russian',
        'pl': 'polish', 'es': 'spanish', 'de': 'german', 'fr': 'french', 'it': 'italian'
    }
    profile_name = profile_map.get(lang, 'english')
    profile_file = PROFILES_DIR / f"{profile_name}.json"
    if profile_file.exists():
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('name_pool', []), data.get('personalities', [])
        except (json.JSONDecodeError, PermissionError) as e:
            print(f"Warning: Failed to read {profile_file}: {e}", file=sys.stderr)
            print(f"Falling back to English names.", file=sys.stderr)
            return [], []
    elif lang != 'en':
        print(f"Warning: Language profile '{profile_name}' not found at {profile_file}.", file=sys.stderr)
        print(f"Falling back to English names.", file=sys.stderr)
    return [], []


def apply_localization(judges, lang='en'):
    """Apply localized names, titles, and emojis from language pool.
    
    Returns a new list — does NOT mutate the input.
    """
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

    result = []
    for i, judge in enumerate(judges):
        j = dict(judge)  # shallow copy to avoid mutating original
        judge_type = j['type']
        localized = personality_lookup.get(judge_type, {})

        # Override with localized data if available
        if localized:
            j['title_male'] = localized.get('title_male', j.get('title_male', ''))
            j['title_female'] = localized.get('title_female', j.get('title_female', ''))
            j['emoji_male'] = localized.get('emoji_male', j.get('emoji_male', ''))
            j['emoji_female'] = localized.get('emoji_female', j.get('emoji_female', ''))
            j['focus'] = localized.get('focus', j.get('focus', []))

        # Assign name
        if i < len(names):
            name_entry = names[i]
            j['assigned_name'] = name_entry['name']
            j['assigned_gender'] = name_entry['gender']
        else:
            j['assigned_name'] = j['name']  # fallback to judge type name
            j['assigned_gender'] = 'male'
        
        result.append(j)

    return result


def apply_mode_claude_qwen(judges, mode='balanced'):
    """Force model based on quality mode for Claude/Qwen (sonnet/haiku).
    
    Returns a new list — does NOT mutate the input.
    """
    result = copy.deepcopy(judges)
    forced_model = MODES_CLAUDE_QWEN.get(mode)

    if forced_model:
        for judge in result:
            judge['model'] = forced_model
    elif mode == 'balanced':
        sonnet_idx = deque(i for i, j in enumerate(result) if j.get('model') == 'sonnet')
        haiku_idx = deque(i for i, j in enumerate(result) if j.get('model') != 'sonnet')

        while len(sonnet_idx) < 2 and haiku_idx:
            idx = haiku_idx.popleft()
            result[idx]['model'] = 'sonnet'
            sonnet_idx.append(idx)

        while len(haiku_idx) < 2 and sonnet_idx:
            idx = sonnet_idx.popleft()
            result[idx]['model'] = 'haiku'
            haiku_idx.append(idx)

        result = [result[i] for i in list(sonnet_idx)[:2] + list(haiku_idx)[:2]]

    return result


def apply_mode_gemini(judges, mode='balanced'):
    """Force model based on quality mode for Gemini (pro/flash/flash-lite).
    
    Returns a new list — does NOT mutate the input.
    Uses gemini_model as source of truth.
    """
    result = copy.deepcopy(judges)
    forced_model = MODES_GEMINI.get(mode)

    if forced_model:
        for judge in result:
            judge['model'] = forced_model
            judge['gemini_model'] = forced_model
    elif mode == 'balanced':
        # Enforce 2 Pro + 2 Flash split based on gemini_model
        pro_idx = deque(i for i, j in enumerate(result) if j.get('gemini_model') == 'pro')
        flash_idx = deque(i for i, j in enumerate(result) if j.get('gemini_model') in ('flash', 'flash-lite'))

        while len(pro_idx) < 2 and flash_idx:
            idx = flash_idx.popleft()
            result[idx]['gemini_model'] = 'pro'
            result[idx]['model'] = 'pro'
            pro_idx.append(idx)

        while len(flash_idx) < 2 and pro_idx:
            idx = pro_idx.popleft()
            result[idx]['gemini_model'] = 'flash'
            result[idx]['model'] = 'flash'
            flash_idx.append(idx)

        result = [result[i] for i in list(pro_idx)[:2] + list(flash_idx)[:2]]

    # Sync model field with gemini_model
    for j in result:
        j['model'] = j['gemini_model']

    return result


def apply_mode(judges, mode='balanced', platform='claude'):
    """Apply quality mode for the given platform."""
    if platform == 'gemini':
        return apply_mode_gemini(judges, mode)
    return apply_mode_claude_qwen(judges, mode)


def get_gemini_model_name(model_key):
    """Convert model key to full Gemini model name."""
    mapping = {
        'pro': 'gemini-3.1-pro',
        'flash': 'gemini-3.1-flash',
        'flash-lite': 'gemini-3.1-flash-lite',
    }
    return mapping.get(model_key, model_key)


def select_judges(count=4, lang='en', mode='balanced', platform='claude'):
    """Select judges with localization, mode, and platform."""
    all_judges = load_judges()
    selected = random.sample(all_judges, min(count, len(all_judges)))
    selected = apply_mode(selected, mode, platform)
    selected = apply_localization(selected, lang)

    # For Gemini, add full model name
    if platform == 'gemini':
        for j in selected:
            model_key = j.get('gemini_model', j.get('model', 'flash'))
            j['gemini_model_full'] = get_gemini_model_name(model_key)

    return selected


def list_judges(platform='claude'):
    """List all available judges with their model info."""
    all_judges = load_judges()
    print(f"\n🎭 All available judges ({len(all_judges)}):\n")
    for j in all_judges:
        if platform == 'gemini':
            model_name = get_gemini_model_name(j.get('gemini_model', 'flash'))
            model_icon = "🟢 Pro" if j.get('gemini_model') == 'pro' else \
                         "🔵 Flash" if j.get('gemini_model') == 'flash' else "⚡ Flash-Lite"
        else:
            model_name = j.get('model', 'haiku')
            model_icon = "🟡 Sonnet" if model_name == 'sonnet' else "🔵 Haiku"
        print(f"  {j['emoji_male']} {j['name']} — weight: {j['vote_weight']}x — {model_icon}")
        print(f"     Focus: {', '.join(j['focus'][:3])}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Select Code Jury judges')
    parser.add_argument('--count', '-n', type=int, default=4)
    parser.add_argument('--list', '-l', action='store_true')
    parser.add_argument('--lang', type=str, default='en')
    parser.add_argument('--platform', '-p', type=str, default='claude',
                       choices=['claude', 'qwen', 'gemini'],
                       help='Target platform for model names')
    parser.add_argument('--mode', '-m', type=str, default='balanced',
                       choices=['lightning', 'flash', 'balanced', 'thorough'],
                       help='Quality mode. Flash is Gemini-only.')
    args = parser.parse_args()

    if args.list:
        list_judges(args.platform)
        return

    judges = select_judges(args.count, args.lang, args.mode, args.platform)
    print(json.dumps(judges, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
