#!/usr/bin/env python3
"""
Модуль для трекінгу issues між сесіями на одній гілці.
Показує прогрес: що фікснулось, що залишилось, нові баги.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Issue:
    """Представляє одну проблему в коді."""
    id: str
    type: str  # missing_tests, no_error_handling, magic_numbers, тощо
    description: str
    severity: str  # critical, warning, info
    judge_name: str
    first_seen_session: str
    status: str = "open"  # open, fixed, still_present
    sessions_seen: list = None
    
    def __post_init__(self):
        if self.sessions_seen is None:
            self.sessions_seen = [self.first_seen_session]


@dataclass
class BranchVoteHistory:
    """Історія голосувань на гілці."""
    branch: str
    base_branch: str
    sessions: List[dict]
    issues: List[dict]
    attempt_count: int = 0
    status: str = "pending"  # pending, passing, failing
    
    def get_latest_session(self) -> Optional[dict]:
        """Повертає останню сесію."""
        return self.sessions[-1] if self.sessions else None
    
    def get_latest_score(self) -> Optional[float]:
        """Повертає останній бал."""
        latest = self.get_latest_session()
        return latest.get('average_score') if latest else None
    
    def get_score_trend(self) -> List[float]:
        """Повертає тренд балів."""
        return [s.get('average_score', 0) for s in self.sessions]
    
    def get_open_issues(self) -> List[dict]:
        """Повертає відкриті проблеми."""
        return [i for i in self.issues if i.get('status') == 'open']
    
    def get_fixed_issues(self) -> List[dict]:
        """Повертає виправлені проблеми."""
        return [i for i in self.issues if i.get('status') == 'fixed']
    
    def get_issues_by_type(self, issue_type: str) -> List[dict]:
        """Повертає проблеми за типом."""
        return [i for i in self.issues if i.get('type') == issue_type]


class BranchTracker:
    """Трекер історії голосувань на гілці."""
    
    def __init__(self, branch: str, base_branch: str = "main"):
        self.branch = branch
        self.base_branch = base_branch
        
        # Шлях до файлу історії гілки в .qwen (не комітиться)
        self.tracker_dir = self._get_tracker_dir()
        self.tracker_dir.mkdir(parents=True, exist_ok=True)
        
        # Санітизуємо ім'я гілки для файлу
        safe_branch = branch.replace('/', '_').replace('..', '_')
        safe_base = base_branch.replace('/', '_').replace('..', '_')
        self.history_file = self.tracker_dir / f"{safe_branch}_vs_{safe_base}.json"
        
        self.history = self._load_history()
    
    def _get_tracker_dir(self) -> Path:
        """Повертає директорію трекера в .qwen."""
        current = Path(__file__).parent.parent
        for _ in range(5):
            qwen_dir = current / ".qwen" / "skills" / "vote" / "branches"
            if qwen_dir.parent.parent.exists():
                return qwen_dir
            current = current.parent
        
        return Path(__file__).parent.parent / "branches"
    
    def _load_history(self) -> BranchVoteHistory:
        """Завантажує історію з файлу."""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return BranchVoteHistory(**data)
        
        return BranchVoteHistory(
            branch=self.branch,
            base_branch=self.base_branch,
            sessions=[],
            issues=[],
            attempt_count=0,
            status="pending"
        )
    
    def save_history(self):
        """Зберігає історію у файл."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.history), f, ensure_ascii=False, indent=2)
    
    def add_session(self, session_result: dict):
        """Додає нову сесію голосування."""
        self.history.attempt_count += 1
        
        # Додаємо сесію
        self.history.sessions.append(session_result)
        
        # Оновлюємо issues
        self._update_issues(session_result)
        
        # Оновлюємо статус
        self.history.status = "passing" if session_result.get('overall_passed') else "failing"
        
        # Зберігаємо
        self.save_history()
    
    def _update_issues(self, session_result: dict):
        """Оновлює список issues на основі нової сесії."""
        session_id = session_result.get('session_id')
        
        # Збираємо всі проблеми з нової сесії
        new_issues = {}
        for judge_result in session_result.get('results', []):
            for dislike in judge_result.get('dislikes', []):
                issue_type = self._categorize_issue(dislike)
                issue_key = f"{issue_type}_{dislike}"
                
                new_issues[issue_key] = {
                    'id': issue_key,
                    'type': issue_type,
                    'description': dislike,
                    'severity': self._determine_severity(issue_type),
                    'judge_name': judge_result.get('name'),
                    'first_seen_session': session_id,
                    'status': 'open',
                    'sessions_seen': [session_id]
                }
        
        # Перевіряємо які проблеми залишились, а які фікснулись
        existing_issues = {i['id']: i for i in self.history.issues}
        
        for issue_id, issue in new_issues.items():
            if issue_id in existing_issues:
                # Проблема вже була - оновлюємо
                existing_issues[issue_id]['status'] = 'still_present'
                existing_issues[issue_id]['sessions_seen'].append(session_id)
            else:
                # Нова проблема
                self.history.issues.append(issue)
        
        # Перевіряємо які проблеми фікснулись (були але немає зараз)
        for issue in self.history.issues:
            if issue['id'] not in new_issues:
                if issue['status'] in ['open', 'still_present']:
                    issue['status'] = 'fixed'
    
    def _categorize_issue(self, description: str) -> str:
        """Категоризує проблему за описом."""
        desc_lower = description.lower()
        
        if 'тест' in desc_lower or 'test' in desc_lower:
            return 'missing_tests'
        elif 'помилк' in desc_lower or 'error' in desc_lower or 'exception' in desc_lower:
            return 'no_error_handling'
        elif 'документ' in desc_lower or 'documentation' in desc_lower or 'коментар' in desc_lower:
            return 'missing_documentation'
        elif 'стиль' in desc_lower or 'style' in desc_lower or 'naming' in desc_lower or "іменування" in desc_lower:
            return 'code_style'
        elif 'magic' in desc_lower or 'архітектур' in desc_lower or 'architecture' in desc_lower:
            return 'code_architecture'
        elif 'продуктивн' in desc_lower or 'performance' in desc_lower or 'оптиміз' in desc_lower:
            return 'performance'
        elif 'безпек' in desc_lower or 'security' in desc_lower:
            return 'security'
        else:
            return 'other'
    
    def _determine_severity(self, issue_type: str) -> str:
        """Визначає серйозність проблеми."""
        severity_map = {
            'security': 'critical',
            'no_error_handling': 'critical',
            'missing_tests': 'warning',
            'missing_documentation': 'info',
            'code_style': 'info',
            'code_architecture': 'warning',
            'performance': 'warning',
            'other': 'info'
        }
        return severity_map.get(issue_type, 'info')
    
    def get_progress_summary(self) -> dict:
        """Повертає підсумок прогресу."""
        open_issues = self.history.get_open_issues()
        fixed_issues = self.history.get_fixed_issues()
        
        # Рахуємо по типах
        critical_open = sum(1 for i in open_issues if i.get('severity') == 'critical')
        warning_open = sum(1 for i in open_issues if i.get('severity') == 'warning')
        info_open = sum(1 for i in open_issues if i.get('severity') == 'info')
        
        return {
            'attempt_count': self.history.attempt_count,
            'current_score': self.history.get_latest_score(),
            'score_trend': self.history.get_score_trend(),
            'status': self.history.status,
            'open_issues': len(open_issues),
            'fixed_issues': len(fixed_issues),
            'critical_open': critical_open,
            'warning_open': warning_open,
            'info_open': info_open,
            'open_issues_list': open_issues,
            'fixed_issues_list': fixed_issues
        }
    
    def format_progress(self) -> str:
        """Форматує підсумок прогресу для виводу."""
        summary = self.get_progress_summary()
        
        if summary['attempt_count'] == 0:
            return ""
        
        output = []
        output.append(f"\n📊 Історія на гілці: {self.branch}")
        output.append(f"{'='*60}")
        
        # Таблиця спроб
        output.append(f"\n📋 Спроби голосування:")
        for i, session in enumerate(self.history.sessions, 1):
            score = session.get('average_score', 0)
            passed = '✅' if session.get('overall_passed') else '❌'
            output.append(f"  Спроба #{i}: {score}/10 {passed}")
        
        # Тренд
        if len(summary['score_trend']) > 1:
            trend = summary['score_trend']
            diff = trend[-1] - trend[-2]
            if diff > 0:
                output.append(f"\n📈 Тренд: {' → '.join(str(s) for s in trend)} (+{diff})")
            elif diff < 0:
                output.append(f"\n📉 Тренд: {' → '.join(str(s) for s in trend)} ({diff})")
            else:
                output.append(f"\n➡️  Тренд: {' → '.join(str(s) for s in trend)} (без змін)")
        
        # Виправлені
        if summary['fixed_issues_list']:
            output.append(f"\n✅ Виправлені проблеми:")
            for issue in summary['fixed_issues_list']:
                output.append(f"  ✅ {issue['description']}")
        
        # Відкриті
        if summary['open_issues_list']:
            output.append(f"\n⚠️ Відкриті проблеми:")
            for issue in sorted(summary['open_issues_list'], key=lambda x: {'critical': 0, 'warning': 1, 'info': 2}.get(x.get('severity', 'info'), 3)):
                severity_emoji = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(issue.get('severity', 'info'), '⚪')
                sessions_count = len(issue.get('sessions_seen', []))
                persistence = f" ({sessions_count} спр.)" if sessions_count > 1 else ""
                output.append(f"  {severity_emoji} {issue['description']}{persistence}")
        
        # Підсумок
        output.append(f"\n{'='*60}")
        if summary['status'] == 'passing':
            output.append(f"🎉 Гілка проходить голосування!")
        else:
            output.append(f"❌ Гілка не проходить. Потрібно виправити {summary['open_issues']} проблем.")
        
        return '\n'.join(output)
    
    def has_history(self) -> bool:
        """Чи є історія голосувань?"""
        return len(self.history.sessions) > 0


def get_branch_tracker(branch: str, base_branch: str = "main") -> BranchTracker:
    """Фабрика для створення трекера."""
    return BranchTracker(branch, base_branch)


if __name__ == "__main__":
    # Тестування
    tracker = BranchTracker("feature-auth", "main")
    
    # Симуляція додавання сесій
    session1 = {
        'session_id': 'abc123',
        'average_score': 6.5,
        'overall_passed': False,
        'results': [
            {'name': 'Оксана', 'dislikes': ['Відсутні тести', 'Немає обробки помилок']},
            {'name': 'Тарас', 'dislikes': ['Magic numbers']}
        ]
    }
    
    session2 = {
        'session_id': 'def456',
        'average_score': 7.5,
        'overall_passed': False,
        'results': [
            {'name': 'Оксана', 'dislikes': ['Magic numbers']},
            {'name': 'Тарас', 'dislikes': ['Deprecated функція process()']}
        ]
    }
    
    tracker.add_session(session1)
    tracker.add_session(session2)
    
    print(tracker.format_progress())
