#!/usr/bin/env python3
"""
Модуль для визначення мови користувача та генерації відповідних профілів журі.
Підтримує: українську, англійську, арабську, російську та інші мови.
"""

import re
import os
import json
from pathlib import Path

# Мапа мов до файлів профілів
LANGUAGE_MAP = {
    "uk": "ukrainian.json",
    "ukrainian": "ukrainian.json",
    "en": "english.json", 
    "english": "english.json",
    "ar": "arabic.json",
    "arabic": "arabic.json",
    "ru": "russian.json",
    "russian": "russian.json",
    "pl": "polish.json",
    "polish": "polish.json",
    "de": "german.json",
    "german": "german.json",
    "fr": "french.json",
    "french": "french.json",
    "es": "spanish.json",
    "spanish": "spanish.json",
    "it": "italian.json",
    "italian": "italian.json",
}

# Ключові слова для визначення мови
LANGUAGE_PATTERNS = {
    "uk": r'(що|як|це|для|на|він|вона|але|так|ні|тому|будь|привіт|оціни|код|мій|перевір|будь ласка)',
    "ru": r'(что|как|это|для|на|он|она|но|да|нет|потому|пожалуйста|привет|оцени|код|мой|проверь)',
    "en": r'\b(the|is|are|for|on|he|she|but|yes|no|because|please|code|function|check|my)\b',
    "ar": r'(هذا|هي|على|في|لكن|نعم|لا|لأن|من|إلى)',
    "pl": r'(co|jak|to|dla|na|on|ona|ale|tak|nie|dlatego|proszę|cześć|kod|mój)',
    "de": r'\b(der|die|das|für|auf|er|sie|aber|ja|nein|weil|bitte|code|mein)\b',
    "fr": r'\b(le|la|les|pour|sur|il|elle|mais|oui|non|parce|code|mon)\b',
    "es": r'\b(el|la|los|las|para|por|en|él|ella|pero|sí|no|porque|código|mi)\b',
    "it": r'\b(il|la|i|gli|per|su|lui|lei|ma|sì|no|perché|codice|mio)\b',
}


def detect_language_from_text(text: str) -> str:
    """
    Визначає мову з тексту за допомогою ключових слів.
    Повертає код мови (uk, en, ar, тощо) або 'en' за замовчуванням.
    """
    if not text:
        return "en"
    
    text_lower = text.lower()
    scores = {}
    
    for lang, pattern in LANGUAGE_PATTERNS.items():
        matches = len(re.findall(pattern, text_lower))
        if matches > 0:
            scores[lang] = matches
    
    if not scores:
        return "en"  # За замовчуванням англійська
    
    # Повертаємо мову з найбільшою кількістю збігів
    return max(scores, key=scores.get)


def detect_language_from_env() -> str:
    """
    Визначає мову з змінних оточення або локалі системи.
    """
    # Перевірка змінних оточення
    for env_var in ["USER_LANGUAGE", "LANG", "LC_ALL", "LC_MESSAGES"]:
        lang = os.environ.get(env_var, "")
        if lang:
            lang_code = lang.split("_")[0].lower()
            if lang_code in LANGUAGE_MAP:
                return lang_code
    
    # Перевірка локалі системи
    try:
        import locale
        sys_lang = locale.getdefaultlocale()[0]
        if sys_lang:
            return sys_lang.split("_")[0].lower()
    except:
        pass
    
    return "en"


def get_language_code(context: str = "") -> str:
    """
    Головний метод для визначення мови.
    Спочатку перевіряє контекст, потім змінні оточення.
    """
    # 1. Спроба з контексту
    if context:
        lang = detect_language_from_text(context)
        if lang != "en":  # Якщо не англійська, довіряємо
            return lang
    
    # 2. Спроба з оточення
    return detect_language_from_env()


def get_judge_profile_file(language_code: str) -> str:
    """
    Повертає ім'я файлу профілю журі для заданої мови.
    """
    return LANGUAGE_MAP.get(language_code, "english.json")


def load_judge_profiles(language_code: str, profiles_dir: str = None) -> list:
    """
    Завантажує профілі журі для заданої мови.
    """
    if profiles_dir is None:
        # Шлях до файлів профілів відносно цього скрипта
        profiles_dir = Path(__file__).parent / "judge_profiles"
    
    profile_file = profiles_dir / get_judge_profile_file(language_code)
    
    if not profile_file.exists():
        # Fallback на англійські профілі
        profile_file = profiles_dir / "english.json"
    
    with open(profile_file, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    # Тестування
    test_texts = [
        "Привіт, як справи?",
        "Hello, how are you?",
        "مرحبا، كيف حالك؟",
        "Привет, как дела?",
    ]
    
    print("🔍 Тестування визначення мови:")
    for text in test_texts:
        lang = detect_language_from_text(text)
        print(f"  '{text}' → {lang}")
