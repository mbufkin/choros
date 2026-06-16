#!/usr/bin/env python3
"""
student_server.py — student-facing server for Phren school mode.

Serves individual student pages at /student/<id>/, delivers lessons from the
teacher's lesson store, accepts quiz submissions, and provides misconception
feedback (Phase 6 will wire LLM feedback here).

Stdlib only. Port 8754.
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("'\"")
            os.environ.setdefault(key, value)


_load_dotenv()

BACKEND = {
    "base_url": os.environ.get("LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
    "model": os.environ.get("LLM_MODEL", "qwen2.5-coder:32b"),
    "api_key": os.environ.get("LLM_API_KEY", ""),
}
LLM_TIMEOUT_S = int(os.environ.get("LLM_TIMEOUT_S", "600"))
STUDENT_PORT = int(os.environ.get("STUDENT_PORT", "8754"))

# ---- Workspace imports ----
from workspace import MultiWorkspace, TeacherWorkspace, LessonStore

_school = MultiWorkspace()
_teacher_ws = TeacherWorkspace()
_lesson_store = LessonStore(_teacher_ws)

# Pre-create 5 students for POC
for sid in ["01", "02", "03", "04", "05"]:
    _school.create_student(sid)


# ---- In-memory quiz submissions (POC — flushes on restart) ----
_submissions = {}  # { student_id: { lesson_id: { answers, score, feedback } } }


class StudentHandler(SimpleHTTPRequestHandler):
    """Serves student pages and quiz endpoints."""

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_student_id(self) -> str | None:
        """Extract student ID from path like /student/01/... or /api/student/01/..."""
        match = re.match(r"^/(?:api/)?student/(\d+)(/.*)?$", self.path)
        if match:
            return match.group(1)
        return None

    def do_GET(self):
        # Student page
        sid = self._parse_student_id()
        if sid and self.path in (f"/student/{sid}/", f"/student/{sid}"):
            self._serve_student_page(sid)
            return

        # API: list lessons
        if sid and self.path == f"/api/student/{sid}/lessons":
            weeks = _lesson_store.list_weeks()
            lessons = []
            for w in weeks:
                for day in _lesson_store.list_days(w):
                    lesson = _lesson_store.get_lesson(w, day)
                    if lesson:
                        lessons.append({
                            "id": f"week-{w:02d}-day-{day:02d}",
                            "week": w,
                            "day": day,
                            "title": lesson.get("title", "Untitled"),
                            "domain": lesson.get("domain", "algebra"),
                            "step_count": len(lesson.get("steps", [])),
                        })
            self._send_json(200, {"ok": True, "lessons": lessons})
            return

        # API: get specific lesson
        if sid and self.path.startswith(f"/api/student/{sid}/lesson/"):
            rest = self.path[len(f"/api/student/{sid}/lesson/"):]
            parts = rest.split("/")
            try:
                week = int(parts[0])
                day = int(parts[1]) if len(parts) > 1 else 1
            except (ValueError, IndexError):
                self._send_json(400, {"ok": False, "error": "Invalid week/day"})
                return
            lesson = _lesson_store.get_lesson(week, day)
            if lesson:
                self._send_json(200, {"ok": True, "lesson": lesson})
            else:
                self._send_json(404, {"ok": False, "error": "Lesson not found"})
            return

        # API: student progress
        if sid and self.path == f"/api/student/{sid}/progress":
            submissions = _submissions.get(sid, {})
            progress = {
                "lessons_completed": len(submissions),
                "recent_scores": [
                    {"lesson_id": lid, "score": sub.get("score")}
                    for lid, sub in list(submissions.items())[-5:]
                ],
            }
            self._send_json(200, {"ok": True, **progress})
            return

        # Health
        if self.path == "/api/health":
            self._send_json(200, {
                "ok": True,
                "model": BACKEND["model"],
                "students": _school.list_students(),
                "lessons_available": _lesson_store.lesson_count(),
            })
            return

        return super().do_GET()

    def do_POST(self):
        sid = self._parse_student_id()

        # Submit quiz answers
        if sid and self.path == f"/api/student/{sid}/submit":
            self._handle_submit(sid)
            return

        self._send_json(404, {"ok": False, "error": "Unknown endpoint"})

    def _serve_student_page(self, sid):
        """Serve the student HTML page, injecting student ID."""
        student_path = Path("student.html")
        if not student_path.exists():
            self._send_json(404, {"ok": False, "error": "student.html not found"})
            return
        content = student_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _handle_submit(self, sid):
        """Accept quiz answers, score deterministically, store results."""
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, TypeError, json.JSONDecodeError):
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        lesson_id = body.get("lesson_id", "")
        answers = body.get("answers", {})  # { question_id: chosen_text }

        if not lesson_id or not answers:
            self._send_json(400, {"ok": False, "error": "lesson_id and answers required"})
            return

        # Load the lesson to get answer keys
        lesson = None
        for week in _lesson_store.list_weeks():
            for day in _lesson_store.list_days(week):
                l = _lesson_store.get_lesson(week, day)
                lid = f"week-{week:02d}-day-{day:02d}"
                if lid == lesson_id:
                    lesson = l
                    break
            if lesson:
                break

        if lesson is None:
            self._send_json(404, {"ok": False, "error": f"Lesson {lesson_id} not found"})
            return

        # Score each answer deterministically
        results = []
        correct_count = 0
        total_count = 0

        for step in lesson.get("steps", []):
            if step.get("type") not in ("precheck", "practice"):
                continue
            for q in step.get("questions", []):
                qid = q.get("id", "")
                total_count += 1
                chosen = answers.get(qid, "")

                # Find the correct option
                correct_option = None
                chosen_option = None
                for opt in q.get("options", []):
                    if opt.get("correct"):
                        correct_option = opt
                    if opt.get("text", "").strip().lower() == chosen.strip().lower():
                        chosen_option = opt

                is_correct = correct_option and chosen_option and chosen_option.get("correct", False)
                if is_correct:
                    correct_count += 1

                results.append({
                    "questionId": qid,
                    "chosen": chosen,
                    "correct": is_correct,
                    "correctAnswer": correct_option.get("text", "") if correct_option else "",
                    "reasonTag": chosen_option.get("reason", "") if chosen_option and not is_correct else "",
                    "insight": chosen_option.get("insight", "") if chosen_option else "",
                })

        score = correct_count / total_count if total_count > 0 else 0

        # Store submission
        if sid not in _submissions:
            _submissions[sid] = {}
        _submissions[sid][lesson_id] = {
            "answers": answers,
            "results": results,
            "score": round(score * 100, 1),
            "correct": correct_count,
            "total": total_count,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        # Save to student workspace
        student_ws = _school.get_student(sid)
        if student_ws:
            student_ws.record_lesson(lesson_id, {
                "score": round(score * 100, 1),
                "correct": correct_count,
                "total": total_count,
                "results": results,
            })

        self._send_json(200, {
            "ok": True,
            "lesson_id": lesson_id,
            "score": round(score * 100, 1),
            "correct": correct_count,
            "total": total_count,
            "results": results,
        })

    def log_message(self, fmt, *args):
        if "/api/" in (self.path or ""):
            super().log_message(fmt, *args)


def main():
    server = ThreadingHTTPServer(("0.0.0.0", STUDENT_PORT), StudentHandler)
    print(f"Phren Students on http://localhost:{STUDENT_PORT}")
    print(f"  Students: {', '.join(_school.list_students())}")
    print(f"  Lessons available: {_lesson_store.lesson_count()}")
    print(f"  Model: {BACKEND['model']} @ {BACKEND['base_url']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
