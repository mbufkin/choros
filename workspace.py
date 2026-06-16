#!/usr/bin/env python3
"""
workspace.py — file-system persistence for Phren.

Single-user mode: Workspace (extracted from server.py, backward compatible).
School mode: MultiWorkspace, TeacherWorkspace, LessonStore.

All data is JSON + Markdown on the filesystem. No database, no ORM.
Stdlib only.
"""

import json
import os
import re
import time
from pathlib import Path


# ============================================================================
# Workspace — single-user mode (extracted from server.py, unchanged API)
# ============================================================================

class Workspace:
    """Persistent per-student teaching workspace on the file system.

    Structure:
      .phren-workspace/
        mission.md          — why the student is learning
        learning-records/   — JSON records after each lesson
        glossary.md         — accumulated terminology
        notes.md            — agent's internal notes (preferences, watch-outs)
        cheat-sheets/       — generated reference cards
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "learning-records").mkdir(exist_ok=True)
        (self.root / "cheat-sheets").mkdir(exist_ok=True)

    # -- mission --

    @property
    def mission_path(self):
        return self.root / "mission.md"

    def get_mission(self) -> str | None:
        if self.mission_path.exists():
            return self.mission_path.read_text()
        return None

    def set_mission(self, text: str) -> None:
        self.mission_path.write_text(text)

    # -- learning records --

    def record_lesson(self, lesson_id: str, data: dict) -> None:
        """Save a learning record after completing a lesson."""
        record = {
            "lesson_id": lesson_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **data,
        }
        record_path = self.root / "learning-records" / f"{lesson_id}.json"
        record_path.write_text(json.dumps(record, indent=2))

    def get_records(self) -> list[dict]:
        """Return all learning records, most recent first."""
        records_dir = self.root / "learning-records"
        records = []
        for f in sorted(records_dir.glob("*.json"), reverse=True):
            try:
                records.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                pass
        return records

    def last_record(self) -> dict | None:
        records = self.get_records()
        return records[0] if records else None

    # -- glossary --

    @property
    def glossary_path(self):
        return self.root / "glossary.md"

    def get_glossary(self) -> str:
        if self.glossary_path.exists():
            return self.glossary_path.read_text()
        return ""

    def add_term(self, term: str, definition: str) -> None:
        """Add or update a glossary entry."""
        current = self.get_glossary()
        entry = f"- **{term}**: {definition}\n"
        if term in current:
            lines = current.split("\n")
            new_lines = []
            for line in lines:
                if line.startswith(f"- **{term}**:"):
                    new_lines.append(entry.rstrip())
                else:
                    new_lines.append(line)
            current = "\n".join(new_lines) + "\n"
        else:
            current += entry
        self.glossary_path.write_text(current)

    # -- notes --

    @property
    def notes_path(self):
        return self.root / "notes.md"

    def get_notes(self) -> str:
        if self.notes_path.exists():
            return self.notes_path.read_text()
        return ""

    def append_note(self, text: str) -> None:
        stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        with open(self.notes_path, "a") as f:
            f.write(f"\n[{stamp}] {text}\n")

    # -- cheat sheets --

    def save_cheat_sheet(self, name: str, content: str) -> None:
        safe = re.sub(r"[^\w\-]", "_", name)
        path = self.root / "cheat-sheets" / f"{safe}.md"
        path.write_text(content)

    def list_cheat_sheets(self) -> list[str]:
        return [f.stem for f in (self.root / "cheat-sheets").glob("*.md")]

    # -- summary --

    def summary(self) -> dict:
        """Full workspace state for the health endpoint."""
        records = self.get_records()
        return {
            "has_mission": self.mission_path.exists(),
            "lesson_count": len(records),
            "last_lesson": records[0]["lesson_id"] if records else None,
            "glossary_terms": self.get_glossary().count("- **"),
            "cheat_sheets": self.list_cheat_sheets(),
            "notes_size": (
                self.notes_path.stat().st_size if self.notes_path.exists() else 0
            ),
        }


# ============================================================================
# MultiWorkspace — school mode: manages multiple student workspaces
# ============================================================================

class MultiWorkspace:
    """Manages per-student workspaces under a shared data directory.

    Structure:
      .phren-data/
        students/
          01/    ← a Workspace per student
          02/
          ...

    Each student directory is a full Workspace instance, so all
    single-user methods (records, glossary, notes, etc.) work unchanged.
    """

    def __init__(self, root: str | Path = ".phren-data"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def students_dir(self) -> Path:
        d = self.root / "students"
        d.mkdir(exist_ok=True)
        return d

    def student_path(self, student_id: str) -> Path:
        """Get the path for a student's workspace directory."""
        return self.students_dir / student_id

    def create_student(self, student_id: str) -> Workspace:
        """Create (or open) a Workspace for the given student ID."""
        return Workspace(self.student_path(student_id))

    def get_student(self, student_id: str) -> Workspace | None:
        """Get an existing student workspace, or None if not found."""
        path = self.student_path(student_id)
        if path.exists():
            return Workspace(path)
        return None

    def list_students(self) -> list[str]:
        """Return sorted list of student IDs that have workspaces."""
        if not self.students_dir.exists():
            return []
        return sorted(
            d.name
            for d in self.students_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    def student_exists(self, student_id: str) -> bool:
        return self.student_path(student_id).exists()


# ============================================================================
# TeacherWorkspace — teacher state for school mode
# ============================================================================

class TeacherWorkspace:
    """Persistent teacher state for the school classroom mode.

    Structure:
      .phren-data/teacher/
        buckets/
          curriculum/   ← uploaded curriculum provider files
          district/     ← uploaded district policies, calendars
          teacher/      ← uploaded teacher exemplars (style)
        crystallization/
          report.json   ← curriculum map + gap report
        lessons/
          week-01/
            day-01.json
            day-02.json
            ...
        state.json       ← approval states, pacing tracker
    """

    BUCKET_NAMES = ["curriculum", "district", "teacher"]

    def __init__(self, root: str | Path = ".phren-data/teacher"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        for bucket in self.BUCKET_NAMES:
            (self.root / "buckets" / bucket).mkdir(parents=True, exist_ok=True)
        (self.root / "crystallization").mkdir(exist_ok=True)
        (self.root / "lessons").mkdir(exist_ok=True)

    # -- buckets --

    @property
    def buckets_dir(self) -> Path:
        return self.root / "buckets"

    def bucket_path(self, bucket_name: str) -> Path:
        """Get path to a bucket directory (creates if needed)."""
        if bucket_name not in self.BUCKET_NAMES:
            raise ValueError(
                f"Unknown bucket '{bucket_name}'. Choose: {', '.join(self.BUCKET_NAMES)}"
            )
        path = self.buckets_dir / bucket_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_bucket_files(self, bucket_name: str) -> list[str]:
        """List filenames in a bucket."""
        path = self.bucket_path(bucket_name)
        return sorted(f.name for f in path.iterdir() if f.is_file())

    def store_bucket_file(
        self, bucket_name: str, filename: str, data: bytes
    ) -> Path:
        """Save a file into a bucket. Returns the saved path."""
        path = self.bucket_path(bucket_name)
        safe_name = re.sub(r"[^\w.\-]", "_", filename)
        filepath = path / safe_name
        filepath.write_bytes(data)
        return filepath

    def get_bucket_file(self, bucket_name: str, filename: str) -> bytes | None:
        """Read a file from a bucket. Returns None if not found."""
        path = self.bucket_path(bucket_name) / filename
        if path.exists():
            return path.read_bytes()
        return None

    def get_all_bucket_texts(self) -> list[dict]:
        """Get all uploaded files from all buckets as text dicts.
        
        Returns list of {name, bucket, text} for each file.
        """
        results = []
        for bucket in self.BUCKET_NAMES:
            for filename in self.list_bucket_files(bucket):
                data = self.get_bucket_file(bucket, filename)
                if data is None:
                    continue
                try:
                    text = data.decode("utf-8", errors="replace")
                except Exception:
                    text = ""
                results.append({"name": filename, "bucket": bucket, "text": text})
        return results

    # -- crystallization --

    @property
    def report_path(self) -> Path:
        return self.root / "crystallization" / "report.json"

    def get_report(self) -> dict | None:
        """Get the crystallization report, or None."""
        if self.report_path.exists():
            return json.loads(self.report_path.read_text())
        return None

    def set_report(self, data: dict) -> None:
        """Save the crystallization report."""
        data["generated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.report_path.write_text(json.dumps(data, indent=2))

    # -- lessons --

    @property
    def lessons_dir(self) -> Path:
        return self.root / "lessons"

    def week_path(self, week: int) -> Path:
        """Get path for a week's lesson directory."""
        path = self.lessons_dir / f"week-{week:02d}"
        path.mkdir(exist_ok=True)
        return path

    def store_lesson(self, week: int, day: int, lesson_data: dict) -> Path:
        """Save a lesson JSON for a given week/day."""
        path = self.week_path(week) / f"day-{day:02d}.json"
        lesson_data["week"] = week
        lesson_data["day"] = day
        path.write_text(json.dumps(lesson_data, indent=2))
        return path

    def get_lesson(self, week: int, day: int) -> dict | None:
        """Get a lesson dict, or None."""
        path = self.week_path(week) / f"day-{day:02d}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def list_weeks(self) -> list[int]:
        """Return sorted list of week numbers that have lessons."""
        if not self.lessons_dir.exists():
            return []
        weeks = []
        for d in self.lessons_dir.iterdir():
            if d.is_dir() and d.name.startswith("week-"):
                try:
                    weeks.append(int(d.name.split("-")[1]))
                except (IndexError, ValueError):
                    pass
        return sorted(weeks)

    def list_days(self, week: int) -> list[int]:
        """Return sorted list of day numbers for a given week."""
        wp = self.week_path(week)
        if not wp.exists():
            return []
        days = []
        for f in wp.glob("day-*.json"):
            try:
                days.append(int(f.stem.split("-")[1]))
            except (IndexError, ValueError):
                pass
        return sorted(days)

    def get_week_lessons(self, week: int) -> list[dict]:
        """Get all lessons for a week, sorted by day."""
        lessons = []
        for day in self.list_days(week):
            lesson = self.get_lesson(week, day)
            if lesson:
                lessons.append(lesson)
        return lessons

    # -- teacher state --

    @property
    def state_path(self) -> Path:
        return self.root / "state.json"

    def get_state(self) -> dict:
        """Get teacher state dict (approvals, pacing). Returns empty dict if no state."""
        if self.state_path.exists():
            return json.loads(self.state_path.read_text())
        return {}

    def set_state(self, data: dict) -> None:
        """Save teacher state dict."""
        self.state_path.write_text(json.dumps(data, indent=2))

    def update_state(self, **kwargs) -> dict:
        """Merge kwargs into existing state and save. Returns new state."""
        state = self.get_state()
        state.update(kwargs)
        self.set_state(state)
        return state

    # -- summary --

    def summary(self) -> dict:
        """Summary of teacher workspace for health endpoint."""
        report = self.get_report()
        return {
            "buckets": {
                bucket: len(self.list_bucket_files(bucket))
                for bucket in self.BUCKET_NAMES
            },
            "has_crystallization_report": report is not None,
            "report_syllabus_units": len(report.get("syllabus", [])) if report else 0,
            "weeks_with_lessons": len(self.list_weeks()),
            "total_lessons": sum(
                len(self.list_days(w)) for w in self.list_weeks()
            ),
        }


# ============================================================================
# LessonStore — read-only lesson access for student pages
# ============================================================================

class LessonStore:
    """Read-only lesson access for student-facing pages.

    Wraps a TeacherWorkspace's lesson storage with convenience
    methods for the student experience.
    """

    def __init__(self, teacher_workspace: TeacherWorkspace):
        self._tw = teacher_workspace

    def get_lesson(self, week: int, day: int) -> dict | None:
        return self._tw.get_lesson(week, day)

    def list_weeks(self) -> list[int]:
        return self._tw.list_weeks()

    def list_days(self, week: int) -> list[int]:
        return self._tw.list_days(week)

    def get_week_lessons(self, week: int) -> list[dict]:
        return self._tw.get_week_lessons(week)

    def get_latest_week(self) -> int | None:
        """Get the highest week number that has lessons, or None."""
        weeks = self.list_weeks()
        return weeks[-1] if weeks else None

    def lesson_count(self) -> int:
        return sum(len(self.list_days(w)) for w in self.list_weeks())
