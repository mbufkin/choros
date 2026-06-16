/**
 * teacher.js — Phren Teacher Dashboard logic.
 *
 * Three sections:
 *   1. Bucket uploads (curriculum / district / teacher)
 *   2. Crystallization trigger → report display
 *   3. Student progress overview (placeholder)
 *
 * No build step, no framework. Vanilla JS with the same dark theme.
 */

(function () {
  "use strict";

  // ---- State ----
  const state = {
    buckets: { curriculum: [], district: [], teacher: [] },
    report: null,
    crystallizing: false,
  };

  // ---- DOM refs ----
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const crystallizeBtn = $("#crystallize-btn");
  const crystallizeStatus = $("#crystallize-status");
  const reportSection = $("#report-section");
  const reportContent = $("#report-content");
  const modelBadge = $("#model-badge");

  // ---- Init: check health + load bucket state ----
  async function init() {
    try {
      const resp = await fetch("/api/health");
      const health = await resp.json();
      modelBadge.textContent = health.model || "unknown";
    } catch (e) {
      modelBadge.textContent = "offline";
    }

    await refreshBuckets();
    await checkExistingReport();
  }

  // ---- Bucket file listing ----
  async function refreshBuckets() {
    try {
      const resp = await fetch("/api/teacher/buckets");
      const data = await resp.json();
      if (data.ok) {
        state.buckets = data.buckets;
        renderBucketLists();
      }
    } catch (e) {
      console.error("Failed to refresh buckets:", e);
    }
  }

  function renderBucketLists() {
    for (const bucket of ["curriculum", "district", "teacher"]) {
      const listEl = document.getElementById("list-" + bucket);
      if (!listEl) continue;
      const files = state.buckets[bucket] || [];
      if (files.length === 0) {
        listEl.innerHTML = '<span class="text-slate-600">No files yet</span>';
      } else {
        listEl.innerHTML = files
          .map((f) => `<div class="text-slate-400">📄 ${esc(f)}</div>`)
          .join("");
      }
    }
  }

  // ---- File upload ----
  function setupFileInputs() {
    for (const bucket of ["curriculum", "district", "teacher"]) {
      const input = document.getElementById("file-" + bucket);
      if (!input) continue;

      input.addEventListener("change", async () => {
        if (!input.files || input.files.length === 0) return;
        await uploadFiles(bucket, input.files);
        input.value = ""; // reset so re-uploading same file works
      });
    }

    // Drag-and-drop
    for (const zone of $$(".upload-zone")) {
      const bucket = zone.dataset.bucket;
      if (!bucket) continue;

      zone.addEventListener("dragover", (e) => {
        e.preventDefault();
        zone.classList.add("dragover");
      });
      zone.addEventListener("dragleave", () => {
        zone.classList.remove("dragover");
      });
      zone.addEventListener("drop", async (e) => {
        e.preventDefault();
        zone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
          await uploadFiles(bucket, e.dataTransfer.files);
        }
      });
    }
  }

  async function uploadFiles(bucket, fileList) {
    const formData = new FormData();
    formData.append("bucket", bucket);
    for (const file of fileList) {
      formData.append("files", file);
    }

    try {
      const resp = await fetch("/api/teacher/upload", {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();
      if (data.ok) {
        await refreshBuckets();
      } else {
        alert("Upload failed: " + (data.error || "unknown error"));
      }
    } catch (e) {
      alert("Upload error: " + e.message);
    }
  }

  // ---- Crystallization ----
  async function handleCrystallize() {
    if (state.crystallizing) return;

    // Confirm: does the teacher have files?
    const totalFiles =
      (state.buckets.curriculum?.length || 0) +
      (state.buckets.district?.length || 0) +
      (state.buckets.teacher?.length || 0);

    if (totalFiles === 0) {
      alert("Upload at least one document before crystallizing.");
      return;
    }

    state.crystallizing = true;
    crystallizeBtn.disabled = true;
    crystallizeBtn.textContent = "⏳ Crystallizing...";
    crystallizeStatus.textContent = "Analyzing documents — this may take a minute...";
    reportSection.classList.add("hidden");

    try {
      const resp = await fetch("/api/teacher/crystallize", {
        method: "POST",
      });
      const data = await resp.json();

      if (data.ok) {
        state.report = data.report;
        renderReport(data.report);
        crystallizeStatus.textContent =
          "✓ Done in " + (data.ms / 1000).toFixed(1) + "s using " + data.model;
      } else {
        crystallizeStatus.textContent = "✗ Failed: " + (data.error || "unknown");
      }
    } catch (e) {
      crystallizeStatus.textContent = "✗ Error: " + e.message;
    }

    state.crystallizing = false;
    crystallizeBtn.disabled = false;
    crystallizeBtn.textContent = "🔬 Crystallize Curriculum";
  }

  // ---- Report rendering ----
  async function checkExistingReport() {
    try {
      const resp = await fetch("/api/teacher/report");
      const data = await resp.json();
      if (data.ok && data.report) {
        state.report = data.report;
        renderReport(data.report);
        crystallizeStatus.textContent = "Report loaded from previous run.";
      }
    } catch (e) {
      // No existing report — that's fine
    }
  }

  function renderReport(report) {
    reportSection.classList.remove("hidden");
    let html = "";

    // Coverage stats
    const cov = report.coverage || {};
    html += `
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div class="bg-slate-800 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-brand-400">${report.syllabus?.length || 0}</div>
          <div class="text-xs text-slate-400">Units Mapped</div>
        </div>
        <div class="bg-slate-800 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-green-400">${cov.covered || 0}</div>
          <div class="text-xs text-slate-400">Topics Covered</div>
        </div>
        <div class="bg-slate-800 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold ${(cov.gaps || 0) > 0 ? 'text-amber-400' : 'text-green-400'}">${cov.gaps || 0}</div>
          <div class="text-xs text-slate-400">Gaps Identified</div>
        </div>
        <div class="bg-slate-800 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-slate-300">${report.pacing?.mappedWeeks || 0}</div>
          <div class="text-xs text-slate-400">Weeks Mapped</div>
        </div>
      </div>
    `;

    // Syllabus
    html += `<h3 class="text-md font-semibold mb-2">📋 Syllabus</h3>`;
    if (report.syllabus && report.syllabus.length > 0) {
      html += `<div class="space-y-2 mb-6">`;
      for (const unit of report.syllabus) {
        html += `
          <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-3">
            <div class="font-medium text-sm">Unit ${unit.unit}: ${esc(unit.title)}</div>
            <div class="text-xs text-slate-400 mt-1">
              Weeks ${(unit.weeks || []).join(", ")} · ${(unit.topics || []).join(" · ")}
            </div>
            ${unit.sourceRefs ? `<div class="text-xs text-slate-600 mt-1">Sources: ${unit.sourceRefs.map(esc).join("; ")}</div>` : ""}
          </div>`;
      }
      html += `</div>`;
    } else {
      html += `<p class="text-sm text-slate-500 mb-6">No syllabus units generated.</p>`;
    }

    // Gaps
    html += `<h3 class="text-md font-semibold mb-2">⚠️ Gaps</h3>`;
    if (report.gaps && report.gaps.length > 0) {
      html += `<div class="space-y-2 mb-6">`;
      for (const gap of report.gaps) {
        const sevColor =
          gap.severity === "high" ? "text-red-400" :
          gap.severity === "medium" ? "text-amber-400" : "text-yellow-400";
        html += `
          <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-3">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold uppercase ${sevColor}">${esc(gap.severity || "?")}</span>
              <span class="font-medium text-sm">${esc(gap.topic)}</span>
            </div>
            <div class="text-xs text-slate-400 mt-1">${esc(gap.detail)}</div>
            ${gap.recommendation ? `<div class="text-xs text-brand-400 mt-1">💡 ${esc(gap.recommendation)}</div>` : ""}
          </div>`;
      }
      html += `</div>`;
    } else {
      html += `<p class="text-sm text-green-400 mb-6">✓ No gaps identified — all topics are covered.</p>`;
    }

    // Pacing
    const pacing = report.pacing || {};
    if (pacing.notes) {
      html += `
        <h3 class="text-md font-semibold mb-2">📅 Pacing</h3>
        <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-3 mb-6">
          <div class="text-sm text-slate-300">${esc(pacing.notes)}</div>
          <div class="text-xs text-slate-500 mt-1">Flex weeks: ${pacing.flexWeeks || 0}</div>
        </div>`;
    }

    reportContent.innerHTML = html;

    // Teacher action buttons
    const actionsDiv = document.createElement("div");
    actionsDiv.className = "flex gap-3 mt-6 pt-4 border-t border-slate-700";
    actionsDiv.innerHTML = `
      <button class="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-semibold rounded-lg transition" onclick="alert('Report approved. Ready for Phase 4: Lesson Generation.')">
        ✓ Approve
      </button>
      <button class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium rounded-lg transition" onclick="alert('Upload additional materials to address gaps, then re-crystallize.')">
        📤 Request More
      </button>
      <button class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium rounded-lg transition" onclick="alert('Issue flagged for review.')">
        ⚠️ Flag Issue
      </button>
    `;
    reportContent.appendChild(actionsDiv);
  }

  // ---- Utilities ----
  function esc(s) {
    if (!s) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ---- Wire it up ----
  crystallizeBtn.addEventListener("click", handleCrystallize);
  setupFileInputs();
  init();
})();
