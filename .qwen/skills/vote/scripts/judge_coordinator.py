#!/usr/bin/env python3
"""
Координатор журі - динамічно генерує 4 суддів з унікальними іменами та характерами.
Кожен раз інша комбінація імен з пулу + 4 базові типи особистостей.
"""

import json
import os
import sys
import random
import hashlib
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

# Додаємо батьківську директорію до шляху
sys.path.insert(0, str(Path(__file__).parent))

from language_detector import get_language_code, load_judge_profiles


class DynamicJudgeAgent:
    """Динамічно згенерований агент-суддя."""
    
    def __init__(self, name: str, gender: str, personality: dict, language: str, 
                 code_diff: str, session_id: str, index: int):
        self.name = name
        self.gender = gender
        self.personality = personality
        self.language = language
        self.code_diff = code_diff
        self.session_id = session_id
        self.index = index
        self.judge_id = f"{self.personality['type']}_{self.name}"
        
        # Обираємо емодзі та титул за гендером
        if gender == "female":
            self.emoji = personality.get('emoji_female', personality.get('emoji_male', '👤'))
            self.title = personality.get('title_female', personality.get('title_male', 'Judge'))
        else:
            self.emoji = personality.get('emoji_male', '👨‍💼')
            self.title = personality.get('title_male', 'Judge')
        
        self.result = None
    
    def _build_system_prompt(self) -> str:
        """Будує системний промпт для судді."""
        return f"""Ти {self.name} ({self.title}).
Фокус: {', '.join(self.personality['focus'][:3])}.
Оціни код 1-10. Дай ✅/❌. Знайди ВСІ проблеми (навіть дрібні).
Будь детальним у висновках - не економ токени на аналізі."""
    
    def evaluate(self) -> dict:
        """
        Симулює оцінку судді (в реальному використанні тут буде виклик LLM).
        Повертає результат оцінки.
        """
        # Аналіз дифу (проста евристика для демо)
        diff_lines = self.code_diff.split('\n')
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        
        # Генерація оцінки на основі стилю судді
        score_range = self.personality.get('score_range', [5, 8])
        base_score = random.randint(score_range[0], score_range[1])
        
        # Перевірка якості коду
        has_comments = any('//' in line or '#' in line for line in diff_lines[:50])
        has_error_handling = any('try' in line or 'except' in line or 'catch' in line for line in diff_lines)
        has_tests = any('test' in line.lower() or 'assert' in line for line in diff_lines)
        has_types = any('def ' in line or 'function ' in line or 'class ' in line for line in diff_lines)
        
        # Бонус за якість
        quality_bonus = 0
        if has_comments:
            quality_bonus += 1
        if has_error_handling:
            quality_bonus += 1
        if has_tests:
            quality_bonus += 1
        if has_types:
            quality_bonus += 0.5
        
        final_score = min(10, base_score + quality_bonus)
        final_score = round(final_score, 1)
        
        # Визначення вердикту (поріг 7.0)
        passed = final_score >= 7.0
        
        # Генерація коментарів
        likes, dislikes = self._generate_feedback(
            additions, deletions, has_comments, has_error_handling, has_tests, has_types
        )
        
        self.result = {
            "judge_id": self.judge_id,
            "name": self.name,
            "gender": self.gender,
            "emoji": self.emoji,
            "personality": self.title,
            "personality_type": self.personality['type'],
            "score": final_score,
            "passed": passed,
            "likes": likes,
            "dislikes": dislikes,
            "focus_areas": self.personality['focus'],
            "vote_weight": self.personality.get('vote_weight', 1.0),
            "verdict": "✅ Так" if passed else "❌ Ні",
            "evaluated_at": datetime.now().isoformat()
        }
        
        return self.result
    
    def _generate_feedback(self, additions: int, deletions: int, 
                          has_comments: bool, has_error_handling: bool, 
                          has_tests: bool, has_types: bool) -> Tuple[List[str], List[str]]:
        """Генерує позитивні та негативні коментарі на основі фокусу судді."""
        
        likes = []
        dislikes = []
        
        focus = self.personality['focus']
        
        # Позитивні коментарі на основі фокусу
        if has_comments and "Документація" in focus or "Documentation" in focus:
            likes.append("Наявність коментарів в коді" if self.language in ['uk', 'ru'] else "Good code commenting")
        
        if has_error_handling and ("Обробка помилок" in focus or "Error Handling" in focus):
            likes.append("Обробка помилок присутня" if self.language in ['uk', 'ru'] else "Error handling present")
        
        if has_tests and ("Тести" in focus or "Tests" in focus):
            likes.append("Є тести для нового коду" if self.language in ['uk', 'ru'] else "Tests included for new code")
        
        if additions > 0 and ("Архітектура" in focus or "Architecture" in focus):
            likes.append("Додано новий функціонал" if self.language in ['uk', 'ru'] else "New functionality added")
        
        if has_types and ("Якість коду" in focus or "Code Quality" in focus):
            likes.append("Чіткі типи/функції" if self.language in ['uk', 'ru'] else "Clear types/functions defined")
        
        # Якщо немає позитивних, додаємо загальні
        if not likes:
            likes.append("Код компілюється без помилок" if self.language in ['uk', 'ru'] else "Code compiles without errors")
        
        # Негативні коментарі на основі фокусу
        if not has_error_handling and ("Обробка помилок" in focus or "Error Handling" in focus):
            dislikes.append("Відсутня обробка помилок" if self.language in ['uk', 'ru'] else "Missing error handling")
        
        if not has_comments and ("Документація" in focus or "Documentation" in focus):
            dislikes.append("Недостатня документація" if self.language in ['uk', 'ru'] else "Insufficient documentation")
        
        if not has_tests and ("Тести" in focus or "Tests" in focus):
            dislikes.append("Відсутні тести" if self.language in ['uk', 'ru'] else "No tests present")
        
        if "Стиль коду" in focus or "Code Style" in focus:
            dislikes.append("Можна покращити стиль коду" if self.language in ['uk', 'ru'] else "Code style could be improved")
        
        # Якщо немає негативних, додаємо загальні
        if not dislikes:
            dislikes.append("Можливо покращити архітектуру" if self.language in ['uk', 'ru'] else "Architecture could be improved")
        
        return likes, dislikes  # Повертаємо ВСЕ, без обмежень


class VoteCoordinator:
    """Координує процес голосування з 4 динамічними суддями."""
    
    JUDGES_COUNT = 4  # Завжди 4 судді (як в America's Got Talent)
    MAX_DIFF_LINES = 200  # Ліміт довжини diff для економії токенів
    MAX_CONTEXT_LINES = 3  # Контекст навколо кожної зміни
    
    def __init__(self, code_diff: str, context: str = ""):
        self.code_diff = self._optimize_diff(code_diff)
        self.context = context
        
        # Визначення мови
        self.language_code = get_language_code(context)
        
        # Завантаження профілів мови
        self.profiles = self._load_language_profiles()
        
        # Генерація session ID
        self.session_id = self._generate_session_id()
        
        # Шлях до кешу в .qwen (не комітиться в git)
        self.cache_dir = self._get_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_dir(self) -> Path:
        """Повертає директорію кешу (.qwen якщо є, інакше sessions)."""
        # Спроба знайти .qwen в корені проекту
        current = Path(__file__).parent.parent
        for _ in range(5):  # До 5 рівнів вгору
            qwen_dir = current / ".qwen" / "skills" / "vote" / "sessions"
            if qwen_dir.parent.parent.exists():
                return qwen_dir
            current = current.parent
        
        # Fallback на локальну sessions
        return Path(__file__).parent.parent / "sessions"
    
    def _load_language_profiles(self) -> dict:
        """Завантажує профілі для поточної мови."""
        from language_detector import get_judge_profile_file
        
        profiles_dir = Path(__file__).parent / "judge_profiles"
        profile_file = profiles_dir / get_judge_profile_file(self.language_code)
        
        if not profile_file.exists():
            profile_file = profiles_dir / "english.json"
        
        with open(profile_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _optimize_diff(self, diff: str) -> str:
        """
        Оптимізує diff для економії токенів.
        - Обрізає занадто великі diff
        - Залишає тільки важливі зміни (+/- рядки)
        - Зберігає контекст для розуміння
        """
        if not diff:
            return diff
        
        lines = diff.split('\n')
        
        # Якщо diff малий, повертаємо як є
        if len(lines) <= self.MAX_DIFF_LINES:
            return diff
        
        # Інакше оптимізуємо
        optimized = []
        change_indices = []
        
        # Знаходимо індекси змін
        for i, line in enumerate(lines):
            if line.startswith('+') or line.startswith('-'):
                if not line.startswith('+++') and not line.startswith('---'):
                    change_indices.append(i)
        
        # Якщо змін мало, беремо контекст навколо них
        if len(change_indices) <= 50:
            included = set()
            for idx in change_indices:
                # Додаємо контекст +/- N ліній
                start = max(0, idx - self.MAX_CONTEXT_LINES)
                end = min(len(lines), idx + self.MAX_CONTEXT_LINES + 1)
                included.update(range(start, end))
            
            # Збираємо фінальний diff
            last_i = -1
            for i in sorted(included):
                if i - last_i > 1:
                    optimized.append('...')  # Показуємо що щось пропущено
                optimized.append(lines[i])
                last_i = i
        else:
            # Занадто багато змін - беремо перші і останні N ліній
            optimized = lines[:self.MAX_DIFF_LINES // 2]
            optimized.append(f'\n... (ще {len(lines) - self.MAX_DIFF_LINES} ліній) ...')
            optimized.extend(lines[-(self.MAX_DIFF_LINES // 2):])
        
        result = '\n'.join(optimized)
        
        # Попередження якщо diff скорочено
        if len(result) < len(diff):
            saved = len(diff) - len(result)
            result = f"# Diff оптимізовано (заощаджено {saved} символів)\n" + result
        
        return result
    
    def _generate_session_id(self) -> str:
        """Генерує унікальний ID сесії на основі дифу."""
        return hashlib.md5(self.code_diff[:100].encode()).hexdigest()[:8]
    
    def generate_judges(self) -> List[DynamicJudgeAgent]:
        """Генерує 4 унікальних суддів з динамічними іменами."""
        
        name_pool = self.profiles['name_pool'].copy()
        personalities = self.profiles['personalities']
        
        # Перемішуємо імена
        random.shuffle(name_pool)
        
        # Випадково обираємо 4 з 10 personality (якщо доступно більше 4)
        if len(personalities) > self.JUDGES_COUNT:
            selected_personalities = random.sample(personalities, self.JUDGES_COUNT)
        else:
            selected_personalities = personalities
        
        # Завжди 4 судді
        judges = []
        for i, personality in enumerate(selected_personalities):
            # Беремо унікальне ім'я для кожного судді
            name_entry = name_pool[i % len(name_pool)]
            name = name_entry['name']
            gender = name_entry['gender']
            
            judge = DynamicJudgeAgent(
                name=name,
                gender=gender,
                personality=personality,
                language=self.language_code,
                code_diff=self.code_diff,
                session_id=self.session_id,
                index=i
            )
            judges.append(judge)
        
        return judges
    
    def run_vote(self) -> dict:
        """
        Запускає процес голосування з 4 суддями.
        Повертає агреговані результати.
        """
        print(f"\n🎭 Запуск голосування журі...")
        print(f"📊 Мова: {self.language_code}")
        print(f"👥 Судді: {self.JUDGES_COUNT} (як в America's Got Talent)")
        print(f"🆔 Сесія: {self.session_id}\n")
        
        # Генерація суддів
        judges = self.generate_judges()
        
        # Показуємо суддів
        print("🎪 Представлення журі:")
        for judge in judges:
            print(f"  {judge.emoji} {judge.name} - {judge.title}")
        print("")
        
        # Паралельне виконання (в реальному використанні - паралельні LLM запити)
        results = []
        with ThreadPoolExecutor(max_workers=self.JUDGES_COUNT) as executor:
            futures = [executor.submit(judge.evaluate) for judge in judges]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"⚠️  Помилка оцінки: {e}")
        
        # Сортуємо за індексом
        results.sort(key=lambda r: r['judge_id'])
        
        # Агрегація результатів
        aggregated = self._aggregate_results(results)
        
        # Збереження в кеш
        self._save_to_cache(aggregated)
        
        return aggregated
    
    def _aggregate_results(self, results: List[dict]) -> dict:
        """Агрегує результати голосування з урахуванням ваги голосів."""
        
        # Рахуємо зважену суму
        total_weighted_score = 0
        total_weight = 0
        
        weighted_yes = 0
        weighted_no = 0
        
        for r in results:
            # Отримуємо вагу голосу судді
            vote_weight = r.get('vote_weight', 1.0)
            
            total_weighted_score += r['score'] * vote_weight
            total_weight += vote_weight
            
            if r['passed']:
                weighted_yes += vote_weight
            else:
                weighted_no += vote_weight
        
        avg_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # Для проходження потрібно щоб зважена сума "Так" була > зваженої суми "Ні"
        # І мінімальний поріг 60% від загальної ваги
        pass_threshold = total_weight * 0.6
        passed = weighted_yes >= pass_threshold
        
        # Збір усіх порад
        all_likes = []
        all_dislikes = []
        for r in results:
            all_likes.extend(r['likes'])
            all_dislikes.extend(r['dislikes'])
        
        return {
            "session_id": self.session_id,
            "language": self.language_code,
            "timestamp": datetime.now().isoformat(),
            "judges_count": len(results),
            "average_score": round(avg_score, 1),
            "weighted_yes": round(weighted_yes, 1),
            "weighted_no": round(weighted_no, 1),
            "passed_count": sum(1 for r in results if r['passed']),
            "failed_count": sum(1 for r in results if not r['passed']),
            "overall_passed": passed,
            "results": results,
            "summary": {
                "common_likes": list(set(all_likes)),
                "common_dislikes": list(set(all_dislikes)),
                "verdict_emoji": "✅" if passed else "❌",
                "verdict_text": self._get_verdict_text(passed, avg_score)
            }
        }
    
    def _get_verdict_text(self, passed: bool, avg_score: float) -> str:
        """Генерує текст вердикту."""
        if passed:
            return f"Чудово! Код пройшов голосування з середнім балом {avg_score}/10 🎉"
        else:
            return f"На жаль, код не пройшов голосування. Середній бал: {avg_score}/10. Потрібно виправити недоліки."
    
    def _save_to_cache(self, result: dict):
        """Зберігає результат в кеш."""
        cache_file = self.cache_dir / f"{self.session_id}.json"
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Результати збережено в кеш: {cache_file}")
    
    def load_cached_result(self) -> dict:
        """Завантажує кешований результат для цієї сесії."""
        cache_file = self.cache_dir / f"{self.session_id}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def format_output(self, result: dict) -> str:
        """Форматує результат для виводу."""
        
        output = []
        output.append(f"🎭 Результати голосування журі:")
        output.append(f"{'='*60}\n")
        
        # Результати кожного судді
        for r in result['results']:
            vote_weight = r.get('vote_weight', 1.0)
            weight_str = f" (вага: {vote_weight}x)" if vote_weight != 1.0 else ""
            
            output.append(f"{r['emoji']} {r['name']} ({r['personality']}){weight_str}")

            if r['likes']:
                output.append(f"  ✅ {', '.join(r['likes'])}")

            if r['dislikes']:
                output.append(f"  ❌ {', '.join(r['dislikes'])}")

            output.append(f"  📊 {r['score']}/10 | {r['verdict']}")
            output.append("")

        # Підсумок
        summary = result['summary']
        weighted_yes = result.get('weighted_yes', result['passed_count'])
        weighted_no = result.get('weighted_no', result['failed_count'])
        
        output.append(f"{'='*60}")
        output.append(f"📊 Підсумок: {weighted_yes} ✅ Так | {weighted_no} ❌ Ні (зважено)")
        output.append(f"🎯 Середній бал: {result['average_score']}/10")
        output.append(f"")
        
        if result['overall_passed']:
            output.append(f"🎉 {summary['verdict_text']}")
        else:
            output.append(f"😔 {summary['verdict_text']}")
            output.append(f"💡 Повертайся, коли виправиш недоліки!")
        
        if summary['common_dislikes']:
            output.append(f"\n💡 Поради для покращення:")
            for dislike in summary['common_dislikes'][:3]:
                output.append(f"  • {dislike}")
        
        return '\n'.join(output)


def get_cached_votes():
    """Показує всі кешовані голосування."""
    cache_dir = Path(__file__).parent.parent / "sessions"
    
    if not cache_dir.exists():
        print("📭 Немає кешованих голосувань")
        return
    
    cache_files = list(cache_dir.glob("*.json"))
    
    if not cache_files:
        print("📭 Немає кешованих голосувань")
        return
    
    print(f"\n📚 Історія голосувань:")
    print(f"{'='*60}\n")
    
    for cache_file in sorted(cache_files, key=lambda f: f.stat().st_mtime, reverse=True):
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"🆔 Сесія: {data['session_id']}")
        print(f"📅 Дата: {data['timestamp']}")
        print(f"👥 Судді: {data['judges_count']}")
        print(f"📊 Середній бал: {data['average_score']}/10")
        verdict = "✅ Пройшов" if data['overall_passed'] else "❌ Не пройшов"
        print(f"{verdict} ({data['passed_count']}/{data['failed_count']})")
        print(f"")


if __name__ == "__main__":
    # Тестування
    sample_diff = """
diff --git a/example.py b/example.py
+ def calculate_sum(a, b):
+     # Simple addition
+     return a + b
+
+ def divide(a, b):
+     try:
+         return a / b
+     except ZeroDivisionError:
+         return None
    """
    
    coordinator = VoteCoordinator(sample_diff, context="Привіт, перевір мій код")
    result = coordinator.run_vote()
    print("\n" + coordinator.format_output(result))
