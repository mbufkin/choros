/**
 * student.js — Phren Student lesson consumption + quiz submission.
 *
 * Three screens: list → lesson → results
 * Student ID is extracted from the URL path (/student/01/).
 */

(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // ---- Extract student ID from URL ----
  const studentId = (() => {
    const m = location.pathname.match(/^\/student\/(\d+)/);
    return m ? m[1] : "01";
  })();

  document.getElementById("student-label").textContent = `Student ${studentId}`;

  // ---- State ----
  const state = {
    lessons: [],
    currentLesson: null,
    currentStepIdx: 0,
    answers: {},  // { questionId: chosenText }
    submitted: false,
  };

  // ---- DOM screens ----
  const screens = {
    list: $("#screen-list"),
    lesson: $("#screen-lesson"),
    results: $("#screen-results"),
  };

  function show(screenName) {
    Object.values(screens).forEach((el) => el.classList.add("hidden"));
    const target = screens[screenName];
    target.classList.remove("hidden");
    target.classList.remove("screen");
    void target.offsetWidth;
    target.classList.add("screen");
  }

  // ---- Init ----
  async function init() {
    await loadLessons();
  }

  async function loadLessons() {
    try {
      const resp = await fetch(`/api/student/${studentId}/lessons`);
      const data = await resp.json();
      if (data.ok) {
        state.lessons = data.lessons;
        renderLessonList();
      }
    } catch (e) {
      console.error("Failed to load lessons:", e);
    }
  }

  function renderLessonList() {
    const listEl = $("#lesson-list");
    const emptyEl = $("#list-empty");

    if (state.lessons.length === 0) {
      listEl.innerHTML = "";
      emptyEl.classList.remove("hidden");
      return;
    }

    emptyEl.classList.add("hidden");
    listEl.innerHTML = state.lessons
      .map(
        (l) => `
        <button class="w-full text-left bg-slate-800/50 border border-slate-700 rounded-lg p-3 hover:border-brand-500 transition"
                data-lesson-id="${l.id}">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-sm">${esc(l.title)}</div>
              <div class="text-xs text-slate-500 mt-0.5">Week ${l.week}, Day ${l.day} · ${l.step_count} steps</div>
            </div>
            <span class="text-brand-400 text-sm">Start →</span>
          </div>
        </button>`
      )
      .join("");

    // Wire click handlers
    listEl.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => startLesson(btn.dataset.lessonId));
    });
  }

  // ---- Lesson playback ----
  async function startLesson(lessonId) {
    try {
      const resp = await fetch(`/api/student/${studentId}/lesson/${lessonId.replace("week-", "").replace("-day-", "/")}`);
      const data = await resp.json();
      if (data.ok) {
        state.currentLesson = data.lesson;
        state.currentStepIdx = 0;
        state.answers = {};
        state.submitted = false;
        renderLesson();
        show("lesson");
      }
    } catch (e) {
      alert("Failed to load lesson: " + e.message);
    }
  }

  function renderLesson() {
    const lesson = state.currentLesson;
    if (!lesson) return;

    $("#lesson-title").textContent = lesson.title;
    $("#lesson-meta").textContent = `Week ${lesson.week}, Day ${lesson.day} · ${lesson.domain || "algebra"}`;

    const steps = lesson.steps || [];
    renderStep(steps[state.currentStepIdx], state.currentStepIdx, steps.length);
    updateProgress();
  }

  function renderStep(step, idx, total) {
    const area = $("#step-area");
    const controls = $("#step-controls");

    if (!step) {
      area.innerHTML = "<p class='text-slate-400'>No more steps.</p>";
      controls.innerHTML = "";
      return;
    }

    switch (step.type) {
      case "precheck":
        renderQuiz(step, area, controls, idx, total, "precheck");
        break;
      case "teach":
        renderTeach(step, area, controls, idx, total);
        break;
      case "practice":
        renderQuiz(step, area, controls, idx, total, "practice");
        break;
      default:
        area.innerHTML = `<p class="text-slate-400">Unknown step type: ${step.type}</p>`;
    }
  }

  function renderTeach(step, area, controls, idx, total) {
    area.innerHTML = `
      <div class="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
        <div class="text-xs text-brand-400 font-semibold uppercase mb-1">📖 Learn</div>
        <h3 class="text-md font-semibold mb-3">${esc(step.title)}</h3>
        <div class="text-sm text-slate-300 leading-relaxed whitespace-pre-line">${esc(step.body)}</div>
      </div>
    `;

    controls.innerHTML = `
      <button id="next-btn" class="px-4 py-2 bg-brand-500 hover:bg-brand-400 text-white text-sm font-semibold rounded-lg transition ml-auto">
        ${idx < total - 1 ? "Next →" : "Finish"}
      </button>
    `;

    $("#next-btn").addEventListener("click", () => {
      if (idx < total - 1) {
        state.currentStepIdx++;
        renderLesson();
      } else {
        submitLesson();
      }
    });
  }

  function renderQuiz(step, area, controls, idx, total) {
    const isPrecheck = step.type === "precheck";
    const label = isPrecheck ? "🔍 Quick Check" : "✏️ Practice";

    let html = `
      <div class="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
        <div class="text-xs text-brand-400 font-semibold uppercase mb-1">${label}</div>
        <h3 class="text-md font-semibold mb-4">${esc(step.concept || "Questions")}</h3>
    `;

    (step.questions || []).forEach((q, qi) => {
      html += `
        <div class="mb-4 pb-4 border-b border-slate-700 last:border-0 last:mb-0 last:pb-0">
          <p class="text-sm font-medium mb-2">${qi + 1}. ${esc(q.text)}</p>
          <div class="space-y-1.5">
      `;
      (q.options || []).forEach((opt) => {
        const selected = state.answers[q.id] === opt.text;
        const cls = state.submitted
          ? opt.correct ? "correct" : selected ? "wrong" : ""
          : selected ? "selected" : "";
        html += `
          <button class="option-btn ${cls} w-full text-left px-3 py-2 border border-slate-600 rounded-lg text-sm hover:border-slate-400 transition"
                  data-qid="${q.id}" data-text="${escAttr(opt.text)}"
                  ${state.submitted ? "disabled" : ""}>
            ${esc(opt.text)}
            ${state.submitted && opt.correct ? ' <span class="text-green-400 text-xs">✓</span>' : ""}
            ${state.submitted && selected && !opt.correct ? ' <span class="text-red-400 text-xs">✗</span>' : ""}
          </button>
        `;
      });
      html += `</div>`;

      // Show feedback if submitted
      if (state.submitted && state.answers[q.id] !== undefined) {
        const chosen = q.options.find((o) => o.text === state.answers[q.id]);
        if (chosen) {
          html += `
            <div class="mt-2 text-xs ${chosen.correct ? 'text-green-400' : 'text-red-400'}">
              ${esc(chosen.insight || "")}
            </div>`;
        }
      }

      html += `</div>`;
    });

    html += `</div>`;
    area.innerHTML = html;

    // Wire option clicks
    if (!state.submitted) {
      area.querySelectorAll(".option-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const qid = btn.dataset.qid;
          const text = btn.dataset.text;
          state.answers[qid] = text;
          // Re-render to update selected state
          renderStep(step, area, controls, idx, total);
        });
      });
    }

    // Controls
    const allAnswered = (step.questions || []).every((q) => state.answers[q.id] !== undefined);
    controls.innerHTML = `
      ${isPrecheck && idx < total - 1 ? `
        <button id="skip-btn" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm rounded-lg transition">
          Skip
        </button>` : ""}
      ${idx < total - 1 ? `
        <button id="next-btn" class="px-4 py-2 bg-brand-500 hover:bg-brand-400 text-white text-sm font-semibold rounded-lg transition ml-auto"
                ${!allAnswered ? "disabled" : ""}>
          Next →
        </button>` : `
        <button id="submit-btn" class="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-semibold rounded-lg transition ml-auto"
                ${!allAnswered ? "disabled" : ""}>
          Submit Answers
        </button>
      `}
    `;

    const nextBtn = $("#next-btn");
    const skipBtn = $("#skip-btn");
    const submitBtn = $("#submit-btn");

    if (nextBtn) nextBtn.addEventListener("click", () => { state.currentStepIdx++; renderLesson(); });
    if (skipBtn) skipBtn.addEventListener("click", () => { state.currentStepIdx++; renderLesson(); });
    if (submitBtn) submitBtn.addEventListener("click", submitLesson);
  }

  function updateProgress() {
    const steps = state.currentLesson?.steps || [];
    const pct = steps.length > 0 ? ((state.currentStepIdx) / steps.length) * 100 : 0;
    $("#progress-fill").style.width = `${Math.min(pct, 100)}%`;
  }

  // ---- Submission ----
  async function submitLesson() {
    const lesson = state.currentLesson;
    if (!lesson) return;

    const lessonId = `week-${String(lesson.week).padStart(2, "0")}-day-${String(lesson.day).padStart(2, "0")}`;

    try {
      const resp = await fetch(`/api/student/${studentId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lesson_id: lessonId, answers: state.answers }),
      });
      const data = await resp.json();
      if (data.ok) {
        state.submitted = true;
        renderResults(data);
        show("results");
      } else {
        alert("Submission failed: " + (data.error || "unknown"));
      }
    } catch (e) {
      alert("Submission error: " + e.message);
    }
  }

  function renderResults(data) {
    const pct = data.score;
    const color = pct >= 80 ? "text-green-400" : pct >= 60 ? "text-amber-400" : "text-red-400";

    $("#results-score").innerHTML = `
      <div class="text-4xl font-extrabold ${color}">${pct}%</div>
      <div class="text-sm text-slate-400 mt-1">${data.correct} of ${data.total} correct</div>
    `;

    let breakdown = "";
    (data.results || []).forEach((r) => {
      const icon = r.correct ? "✓" : "✗";
      const iconColor = r.correct ? "text-green-400" : "text-red-400";
      breakdown += `
        <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-3">
          <div class="flex items-start gap-2">
            <span class="${iconColor} font-bold">${icon}</span>
            <div>
              <div class="text-sm">${esc(r.chosen || "(no answer)")}</div>
              ${!r.correct ? `<div class="text-xs text-slate-400 mt-0.5">Correct: ${esc(r.correctAnswer)}</div>` : ""}
              ${r.insight ? `<div class="text-xs text-brand-400 mt-1">${esc(r.insight)}</div>` : ""}
            </div>
          </div>
        </div>`;
    });
    $("#results-breakdown").innerHTML = breakdown;

    $("#results-back-btn").onclick = () => {
      state.submitted = false;
      state.answers = {};
      state.currentLesson = null;
      show("list");
    };
  }

  // ---- Navigation ----
  $("#back-btn").addEventListener("click", () => {
    state.submitted = false;
    state.answers = {};
    state.currentLesson = null;
    show("list");
  });

  // ---- Utilities ----
  function esc(s) {
    if (!s) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function escAttr(s) {
    if (!s) return "";
    return String(s).replace(/"/g, "&quot;").replace(/&/g, "&amp;");
  }

  // ---- Boot ----
  init();
})();
