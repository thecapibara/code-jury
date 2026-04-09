#!/usr/bin/env python3
"""
Головний скрипт скіла /vote
Запускає систему журі для оцінки змін коду.

Використання:
  python3 vote.py                     # Оцінити незакомічені зміни
  python3 vote.py --branch feature    # Зміни гілки відносно main/master
  python3 vote.py --commit abc123     # Оцінити конкретний коміт
  python3 vote.py --last 3            # Останні 3 коміти разом
  python3 vote.py --file script.py    # Оцінити один файл
  python3 vote.py --staged            # Оцінити staged зміни
  python3 vote.py --diff file.diff    # Оцінити diff з файлу
  python3 vote.py --history           # Показати історію голосувань
  python3 vote.py --session <id>      # Показати результати сесії
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Додаємо директорію скриптів до шляху
sys.path.insert(0, str(Path(__file__).parent))

from judge_coordinator import VoteCoordinator, get_cached_votes
from branch_tracker import BranchTracker, get_branch_tracker


def run_git_command(cmd: list, timeout: int = 10) -> tuple[str, str]:
    """Запускає git команду і повертає (stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", f"Таймаут команди git {' '.join(cmd)}"
    except Exception as e:
        return "", f"Помилка git: {e}"


def check_git_repo() -> bool:
    """Перевіряє, чи ми в git репозиторії."""
    stdout, stderr = run_git_command(['git', 'rev-parse', '--is-inside-work-tree'])
    return stdout.strip() == 'true'


def get_current_branch() -> str:
    """Повертає поточну гілку."""
    stdout, _ = run_git_command(['git', 'branch', '--show-current'])
    return stdout.strip() or 'HEAD'


def is_branch_merged(branch: str, base: str = None) -> bool:
    """Перевіряє чи гілка вже змержена в base."""
    if base is None:
        base = find_default_branch()
    
    stdout, _ = run_git_command(['git', 'merge-base', '--is-ancestor', branch, base])
    return stdout == ''


def find_default_branch():
    """Знаходить основну гілку (main/master/develop)."""
    # Спроба знайти main або master
    for branch in ['main', 'master', 'develop']:
        stdout, _ = run_git_command(['git', 'rev-parse', '--verify', branch])
        if stdout.strip():
            return branch
    
    # Якщо не знайдено, беремо поточну гітку мінус 10 комітів
    stdout, _ = run_git_command(['git', 'branch', '--show-current'])
    if stdout.strip():
        return f"{stdout.strip()}~10"
    
    return "HEAD~10"


def get_unstaged_diff() -> tuple[str, str]:
    """Отримує незакомічені зміни."""
    stdout, stderr = run_git_command(['git', 'diff', 'HEAD'])
    if stdout.strip():
        return stdout, None
    return None, "Немає незакомічених змін"


def get_staged_diff() -> tuple[str, str]:
    """Отримує staged зміни."""
    stdout, stderr = run_git_command(['git', 'diff', '--staged'])
    if stdout.strip():
        return stdout, None
    return None, "Немає staged змін"


def get_branch_diff(branch: str, base: str = None) -> tuple[str, str]:
    """Отримує зміни гілки відносно base."""
    if base is None:
        base = find_default_branch()
    
    # 3-way diff (тільки зміни цієї гілки)
    stdout, stderr = run_git_command(['git', 'diff', f'{branch}...{base}'])
    if stdout.strip():
        return stdout, None
    
    # 2-way diff
    stdout, stderr = run_git_command(['git', 'diff', f'{base}..{branch}'])
    if stdout.strip():
        return stdout, None
    
    return None, f"Не вдалось отримати зміни гілки {branch} відносно {base}"


def get_commit_diff(commit: str) -> tuple[str, str]:
    """Отримує зміни конкретного коміту."""
    # Один коміт
    if '^' not in commit and '~' not in commit:
        stdout, stderr = run_git_command(['git', 'show', commit])
        if stdout.strip():
            return stdout, None
    
    # Діапазон комітів (напр. HEAD~3..HEAD)
    stdout, stderr = run_git_command(['git', 'diff', commit])
    if stdout.strip():
        return stdout, None
    
    return None, f"Не вдалось знайти коміт {commit}"


def get_last_n_commits(n: int) -> tuple[str, str]:
    """Отримує зміни останніх n комітів."""
    stdout, stderr = run_git_command(['git', 'diff', f'HEAD~{n}..HEAD'])
    if stdout.strip():
        return stdout, None
    
    # Якщо менше ніж n комітів, беремо від початку
    stdout, stderr = run_git_command(['git', 'log', '--oneline', '-1'])
    if not stdout.strip():
        return None, "Немає комітів"
    
    # Беремо всі доступні коміти
    stdout, _ = run_git_command(['git', 'rev-list', '--count', 'HEAD'])
    count = int(stdout.strip()) if stdout.strip() else 1
    n = min(n, count)
    
    stdout, _ = run_git_command(['git', 'diff', f'HEAD~{n}..HEAD'])
    if stdout.strip():
        return stdout, None
    
    return None, f"Не вдалось отримати останні {n} комітів"


def get_file_diff(file_path: str) -> tuple[str, str]:
    """Отримує diff конкретного файлу (останній коміт)."""
    stdout, stderr = run_git_command(['git', 'diff', 'HEAD', '--', file_path])
    if stdout.strip():
        return stdout, None
    
    # Спроба з останнім комітом
    stdout, stderr = run_git_command(['git', 'show', 'HEAD', '--', file_path])
    if stdout.strip():
        return stdout, None
    
    return None, f"Не вдалось отримати зміни файлу {file_path}"


def get_diff(args) -> tuple[str, str]:
    """Головна функція отримання diff з різних джерел."""
    
    # Перевірка git репозиторію (крім --diff файлу)
    if not args.diff and not args.file:
        if not check_git_repo():
            return None, "❌ Не знайдено git репозиторій"
    
    # 1. Diff з файлу
    if args.diff:
        try:
            with open(args.diff, 'r', encoding='utf-8') as f:
                diff = f.read()
            if diff.strip():
                return diff, None
            return None, "📭 Файл diff порожній"
        except Exception as e:
            return None, f"❌ Помилка читання файлу: {e}"
    
    # 2. Один файл
    if args.file:
        return get_file_diff(args.file)
    
    # 3. Staged зміни
    if args.staged:
        return get_staged_diff()
    
    # 4. Зміни гілки
    if args.branch:
        return get_branch_diff(args.branch, args.base)
    
    # 5. Конкретний коміт
    if args.commit:
        return get_commit_diff(args.commit)
    
    # 6. Останні n комітів
    if args.last:
        return get_last_n_commits(args.last)
    
    # 7. Незакомічені зміни (за замовчуванням)
    diff, error = get_unstaged_diff()
    if diff:
        return diff, None
    
    # Якщо немає незакомічених, беремо останній коміт
    return get_commit_diff('HEAD~1..HEAD')


def detect_context():
    """Визначає контекст з оточення або файлу."""
    # Спроба з файлу контексту (якщо є)
    context_file = Path(__file__).parent.parent / "context.txt"
    if context_file.exists():
        with open(context_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Спроба зі змінної оточення
    context = os.environ.get("VOTE_CONTEXT", "")
    if context:
        return context
    
    # Порожній контекст - мова визначиться з оточення
    return ""


def format_session_info(data: dict) -> str:
    """Форматує інформацію про сесію."""
    output = []
    output.append(f"🆔 Сесія: {data['session_id']}")
    output.append(f"📅 Дата: {data['timestamp']}")
    output.append(f"📊 Мова: {data['language']}")
    output.append(f"🎯 Середній бал: {data['average_score']}/10")
    output.append(f"{'='*60}\n")
    
    for r in data['results']:
        output.append(f"{r['emoji']} {r['name']} ({r['personality']})")
        output.append(f"  📊 {r['score']}/10 | {r['verdict']}")
        if r['likes']:
            output.append(f"  ✅ {', '.join(r['likes'][:1])}")
        if r['dislikes']:
            output.append(f"  ❌ {', '.join(r['dislikes'][:1])}")
        output.append("")
    
    verdict = "✅ Пройшов" if data['overall_passed'] else "❌ Не пройшов"
    output.append(f"🎯 Вердикт: {verdict}")
    
    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(
        description="🎭 Система журі для оцінки змін коду",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Приклади:
  python3 vote.py                      Оцінити незакомічені зміни
  python3 vote.py --staged             Оцінити staged зміни
  python3 vote.py --branch feature     Зміни гілки відносно main
  python3 vote.py --branch feat --base develop  Гілка відносно develop
  python3 vote.py --commit abc123      Оцінити конкретний коміт
  python3 vote.py --last 3             Останні 3 коміти разом
  python3 vote.py --file script.py     Оцінити один файл
  python3 vote.py --diff changes.diff  Оцінити diff з файлу
  python3 vote.py --history            Історія голосувань
  python3 vote.py --session abc123     Результати сесії
        """
    )
    
    parser.add_argument(
        '--diff',
        type=str,
        help='Шлях до файлу з diff'
    )
    
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Оцінити зміни конкретного файлу'
    )
    
    parser.add_argument(
        '--branch', '-b',
        type=str,
        help='Оцінити зміни гілки відносно main/master'
    )
    
    parser.add_argument(
        '--base',
        type=str,
        help='Базова гілка для порівняння (за замовчуванням main/master)'
    )
    
    parser.add_argument(
        '--commit', '-c',
        type=str,
        help='Оцінити конкретний коміт або діапазон (HEAD~3..HEAD)'
    )
    
    parser.add_argument(
        '--last', '-l',
        type=int,
        help='Оцінити останні N комітів'
    )
    
    parser.add_argument(
        '--staged', '-s',
        action='store_true',
        help='Оцінити staged зміни'
    )
    
    parser.add_argument(
        '--history',
        action='store_true',
        help='Показати історію голосувань'
    )
    
    parser.add_argument(
        '--session',
        type=str,
        help='ID сесії для перегляду результатів'
    )
    
    parser.add_argument(
        '--context',
        type=str,
        help='Контекст для визначення мови'
    )
    
    args = parser.parse_args()
    
    # Режим історії
    if args.history:
        get_cached_votes()
        return
    
    # Режим перегляду сесії
    if args.session:
        cache_dir = Path(__file__).parent.parent / "sessions"
        cache_file = cache_dir / f"{args.session}.json"
        
        if cache_file.exists():
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(format_session_info(data))
        else:
            print(f"❌ Сесію {args.session} не знайдено")
        return
    
    # Режим голосування
    print("🎭 Vote Skill - Система журі для оцінки коду")
    print(f"{'='*60}\n")
    
    # Визначаємо source для diff
    source_type = "unknown"
    source_value = ""
    branch_for_tracker = None
    base_branch = None
    
    if args.branch:
        source_type = "branch"
        source_value = args.branch
        branch_for_tracker = args.branch
        base_branch = args.base
    elif args.commit:
        source_type = "commit"
        source_value = args.commit
    elif args.last:
        source_type = "last_commits"
        source_value = str(args.last)
    elif args.file:
        source_type = "file"
        source_value = args.file
    elif args.staged:
        source_type = "staged"
        source_value = "staged"
    elif args.diff:
        source_type = "file_diff"
        source_value = args.diff
    else:
        # Авто-детект: якщо на гілці ≠ main/master, беремо зміни гілки
        if check_git_repo():
            current_branch = get_current_branch()
            if current_branch not in ['main', 'master', 'develop', 'HEAD']:
                source_type = "auto_branch"
                source_value = current_branch
                branch_for_tracker = current_branch
            else:
                source_type = "unstaged"
                source_value = "unstaged"
        else:
            source_type = "unstaged"
            source_value = "unstaged"
    
    # Показуємо що оцінюємо
    source_labels = {
        'branch': f"🔀 Гілка: {source_value}",
        'auto_branch': f"🔀 Авто: гілка {source_value} (відносно main/master)",
        'commit': f"📝 Коміт: {source_value}",
        'last_commits': f"📚 Останні коміти: {source_value}",
        'file': f"📄 Файл: {source_value}",
        'staged': f"📌 Staged зміни",
        'file_diff': f"📋 Diff з файлу: {source_value}",
        'unstaged': f"✏️  Незакомічені зміни"
    }
    print(source_labels.get(source_type, source_value))
    
    # Якщо base не вказано для auto_branch, знаходимо
    if source_type == 'auto_branch' and not base_branch:
        base_branch = find_default_branch()
    
    # Отримуємо diff
    if args.diff:
        diff, error = get_diff(args)
    elif args.file:
        diff, error = get_diff(args)
    elif args.staged:
        diff, error = get_diff(args)
    elif args.branch:
        diff, error = get_branch_diff(args.branch, args.base)
    elif args.commit:
        diff, error = get_diff(args)
    elif args.last:
        diff, error = get_diff(args)
    elif source_type == 'auto_branch':
        diff, error = get_branch_diff(branch_for_tracker, base_branch)
    else:
        diff, error = get_diff(args)
    
    if error:
        print(f"❌ {error}")
        return
    
    if not diff or not diff.strip():
        print("📭 Немає змін для оцінки")
        return
    
    # Рахуємо статистику
    diff_lines = diff.split('\n')
    additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
    files_changed = sum(1 for line in diff_lines if line.startswith('diff --git'))
    
    print(f"📊 Статистика: +{additions} -{deletions} | Файлів: {files_changed}\n")
    print(f"{'='*60}\n")
    
    # Перевіряємо історію гілки
    branch_tracker = None
    if branch_for_tracker and base_branch:
        branch_tracker = get_branch_tracker(branch_for_tracker, base_branch)
        
        if branch_tracker.has_history():
            print(branch_tracker.format_progress())
            print(f"\n{'='*60}\n")
            print("🔄 Запускаю нову спробу голосування...\n")
    
    # Визначаємо контекст
    context = args.context or detect_context()
    
    # Створюємо координатора
    coordinator = VoteCoordinator(diff, context)
    
    # Перевіряємо кеш
    cached = coordinator.load_cached_result()
    if cached:
        print("💾 Знайдено кешовані результати для цієї сесії:\n")
        print(coordinator.format_output(cached))
        
        # Зберігаємо в трекер гілки
        if branch_tracker:
            branch_tracker.add_session(cached)
        
        print("\n💡 Використовуйте інший diff або очистіть sessions для повторного голосування")
        return
    
    # Запускаємо голосування
    result = coordinator.run_vote()
    
    # Виводимо результат
    print("\n" + coordinator.format_output(result))
    
    # Зберігаємо в трекер гілки
    if branch_tracker:
        branch_tracker.add_session(result)
        print(branch_tracker.format_progress())
    
    # Виводимо результат
    print("\n" + coordinator.format_output(result))


if __name__ == "__main__":
    main()
