// Additive subject adapter. Both subjects use startQuiz/resultFor/finishQuiz
// and the existing localStorage store in app.js.
const nmmmh = { manifest: null, questions: [], loading: null, route: {}, ktmt: null, routeSequence: 0 };

function subjectLink(params = {}) {
  return `#${new URLSearchParams({ subject: "nmmmh", ...params })}`;
}

async function loadNmmmh() {
  if (nmmmh.manifest) return;
  if (nmmmh.loading) return nmmmh.loading;
  nmmmh.loading = (async () => {
    const response = await fetch("subjects/nmmmh/manifest.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Không tải được môn Mật mã học (${response.status})`);
    const manifest = await response.json();
    const questions = [];
    // Retain exam order as declared by the importer. Do not partially expose
    // the subject if one of its exam files fails to load.
    for (const exam of manifest.exams) {
      const file = await fetch(exam.question_file, { cache: "no-store" });
      if (!file.ok) throw new Error(`Không tải được đề ${exam.source_exam_code}`);
      const rows = await file.json();
      if (rows.length !== exam.question_count) throw new Error(`Sai số câu ở đề ${exam.source_exam_code}`);
      questions.push(...rows);
    }
    nmmmh.questions = questions;
    nmmmh.manifest = manifest;
  })();
  try { await nmmmh.loading; } finally { nmmmh.loading = null; }
}

function nmmmhPool(examId, chapterId = "all") {
  const rows = nmmmh.questions.filter((q) => (examId === "all" || q.source_exam_id === examId) && (chapterId === "all" || q.chapter_id === chapterId));
  if (examId !== "all") return rows;
  return deduplicateNmmmh(rows);
}

function deduplicateNmmmh(rows) {
  const seen = new Set();
  return rows.filter((q) => {
    const key = q.duplicate_status === "confirmed" ? q.duplicate_group : q.id;
    if (seen.has(key)) return false;
    seen.add(key); return true;
  });
}

function startNmmmhSavedQuiz(scope) {
  const saved = state.persisted[scope];
  const rows = deduplicateNmmmh(nmmmh.questions.filter((q) => saved.has(q.id)));
  const context = { ...nmmmhContext("all", "all"), chapter: scope === "mistakes" ? "Ôn câu sai" : "Câu đã đánh dấu", chapter_id: scope, scope_kind: scope };
  nmmmh.route = { review: scope };
  history.replaceState(null, "", subjectLink(nmmmh.route));
  startQuiz(scope, false, "study", rows, context);
}

function nmmmhProgressHtml() {
  const completed = nmmmh.questions.filter((q) => state.persisted.progress[q.id]?.answered).length;
  const marked = nmmmh.questions.filter((q) => state.persisted.bookmarks.has(q.id)).length;
  const wrong = nmmmh.questions.filter((q) => state.persisted.mistakes.has(q.id)).length;
  const gradedProgress = nmmmh.questions.filter((q) => q.correct_answer).map((q) => state.persisted.progress[q.id]).filter(Boolean);
  const answered = gradedProgress.reduce((sum, p) => sum + p.answered, 0);
  const correct = gradedProgress.reduce((sum, p) => sum + p.correct, 0);
  return `<section class="nmmmh-progress"><div class="stats-grid">
    ${[[completed, "Câu đã luyện"], [marked, "Câu đã đánh dấu"], [wrong, "Câu cần ôn lại"], [answered ? `${Math.round(correct / answered * 100)}%` : "—", "Độ chính xác · câu có đáp án"]].map(([value, label]) => `<div class="stat-card"><div><span class="stat-value">${value}</span><span class="stat-label">${label}</span></div></div>`).join("")}
    </div><div class="button-row"><button class="secondary-btn" id="nmmmh-mistakes" ${wrong ? "" : "disabled"}>Ôn câu sai</button><button class="ghost-btn" id="nmmmh-bookmarks" ${marked ? "" : "disabled"}>Làm câu đã đánh dấu</button></div></section>`;
}

function nmmmhContext(examId, chapterId) {
  const exam = nmmmh.manifest.exams.find((e) => e.id === examId);
  const chapter = nmmmh.manifest.chapters.find((c) => c.id === chapterId);
  return {
    subject_id: "nmmmh", subject: "Mật mã học", exam_id: examId,
    exam: examId === "all" ? "Tất cả đề" : exam.source_exam_code,
    exam_title: examId === "all" ? "Tất cả đề" : exam.title,
    chapter_id: chapterId, chapter: chapterId === "all" ? "Cả đề" : chapter.label,
    scope_kind: examId === "all" ? "all_exams_chapter" : chapterId === "all" ? "full_exam" : "exam_chapter",
  };
}

function startNmmmhQuiz(examId, chapterId = "all", mode = "study", randomize = false) {
  if (examId === "all" && chapterId === "all") return renderNmmmhHome();
  const pool = nmmmhPool(examId, chapterId);
  const context = nmmmhContext(examId, chapterId);
  // Whole exams always retain original source order, regardless of a stale
  // checkbox setting in a prior chapter practice session.
  const shouldShuffle = chapterId !== "all" && randomize;
  const ordered = shouldShuffle ? shuffle(pool) : pool;
  const params = { exam: examId, chapter: chapterId, action: "start", mode };
  if (shouldShuffle) params.random = "1";
  history.replaceState(null, "", subjectLink(params));
  nmmmh.route = params;
  startQuiz(chapterId === "all" ? "all" : context.chapter, shouldShuffle, mode, ordered, context);
}

function chapterOptions(examId, selectedId = "2") {
  return nmmmh.manifest.chapters.map((chapter) => {
    const count = nmmmhPool(examId, chapter.id).length;
    return `<option value="${escapeHtml(chapter.id)}" ${chapter.id === selectedId ? "selected" : ""} ${count ? "" : "disabled"}>${escapeHtml(chapter.label)} · ${count} câu</option>`;
  }).join("");
}

function sessionControls(prefix) {
  return `<div class="field"><label for="${prefix}-mode">Chế độ</label><select id="${prefix}-mode"><option value="study">Học · phản hồi ngay</option><option value="exam">Thi · chấm khi kết thúc</option></select></div>
    <label class="check-row"><input type="checkbox" id="${prefix}-random" /><span>Trộn câu hỏi trong nhóm chương</span></label>`;
}

function renderNmmmhHome() {
  const total = nmmmh.questions.length;
  const graded = nmmmh.questions.filter((q) => q.correct_answer).length;
  const current = nmmmh.route.chapter || "2";
  app.innerHTML = `<section class="results-head"><div><h1>Trắc nghiệm Mật mã học</h1><p class="muted">${nmmmh.manifest.exams.length} đề · ${total} bản ghi · ${graded} câu có đáp án kiểm chứng</p></div><a class="ghost-btn" href="${subjectLink({ view: "history" })}">Lịch sử làm bài</a></section>
    ${nmmmhProgressHtml()}
    <section class="panel aggregate-panel"><div class="panel-header"><div><h2>Làm theo chương của tất cả đề</h2><p>Gộp câu cùng chương; câu trùng có cùng đáp án được tính một lần.</p></div></div>
      <form id="aggregate-form" class="form-stack"><div class="field"><label for="aggregate-chapter">Chương</label><select id="aggregate-chapter">${chapterOptions("all", current)}</select></div>${sessionControls("aggregate")}<button class="primary-btn" type="submit">Làm nhóm chương từ tất cả đề →</button></form>
    </section>
    <div class="section-heading"><h2>Chọn một đề</h2><a href="subjects/nmmmh/REPORT.md" class="muted" target="_blank" rel="noopener">Báo cáo nạp đề</a></div>
    <section class="exam-grid nmmmh-exams">${nmmmh.manifest.exams.map((exam) => `
      <article class="panel exam-detail-card"><span class="active-set-label">${escapeHtml(exam.source_exam_code)}</span><h2>${escapeHtml(exam.title)}</h2>
        <p class="muted">${escapeHtml([exam.year, exam.attempt ? `Lần ${exam.attempt}` : null].filter(Boolean).join(" · "))}</p>
        <p>${exam.question_count} câu · ${exam.graded_count} có đáp án · ${exam.review_count} cần rà soát</p>
        <div class="chapter-counts">${nmmmh.manifest.chapters.map((c) => exam.chapter_counts[c.id] ? `<span>${c.id === "unclassified" ? "Chưa phân loại" : `Chương ${c.id}`}: ${exam.chapter_counts[c.id]}</span>` : "").join("")}</div>
        <div class="button-row"><a class="primary-btn" href="${subjectLink({ exam: exam.id, chapter: "all", action: "start" })}">Làm cả đề</a><a class="ghost-btn" href="${subjectLink({ exam: exam.id })}">Chọn chương trong đề</a></div>
      </article>`).join("")}</section>
    <p class="notice">Điểm tính trên số câu có đáp án đã kiểm chứng. Câu chưa chốt đáp án vẫn xuất hiện để rà soát và không tính điểm.</p>`;
  document.querySelector("#aggregate-form").addEventListener("submit", (event) => {
    event.preventDefault();
    startNmmmhQuiz("all", document.querySelector("#aggregate-chapter").value, document.querySelector("#aggregate-mode").value, document.querySelector("#aggregate-random").checked);
  });
  document.querySelector("#nmmmh-mistakes").addEventListener("click", () => startNmmmhSavedQuiz("mistakes"));
  document.querySelector("#nmmmh-bookmarks").addEventListener("click", () => startNmmmhSavedQuiz("bookmarks"));
}

function renderNmmmhExam(examId) {
  const exam = nmmmh.manifest.exams.find((e) => e.id === examId);
  const pool = nmmmhPool(examId);
  const available = nmmmh.manifest.chapters.filter((c) => exam.chapter_counts[c.id]);
  const chapterId = available.some((c) => c.id === nmmmh.route.chapter) ? nmmmh.route.chapter : available[0].id;
  app.innerHTML = `<section class="results-head"><div><p class="active-set-label">${escapeHtml(exam.source_exam_code)}</p><h1>${escapeHtml(exam.title)}</h1><p class="muted">${escapeHtml(exam.source_headings.slice(1, 3).join(" · "))}</p></div><a class="ghost-btn" href="${subjectLink()}">← Các đề Mật mã học</a></section>
    <section class="setup-grid"><div class="panel"><h2>Làm cả đề</h2><p>${pool.length} câu theo đúng thứ tự và số câu gốc.</p><div class="field"><label for="full-mode">Chế độ</label><select id="full-mode"><option value="study">Học</option><option value="exam">Thi</option></select></div><div class="button-row"><button type="button" id="full-start" class="primary-btn">Làm cả đề →</button></div></div>
    <div class="panel"><h2>Làm theo chương trong đề</h2><form id="exam-chapter-form" class="form-stack"><div class="field"><label for="exam-chapter">Chương</label><select id="exam-chapter">${chapterOptions(examId, chapterId)}</select></div>${sessionControls("exam")}<button class="primary-btn" type="submit">Làm nhóm chương →</button></form></div></section>
    <section class="panel question-preview"><h2 id="preview-heading"></h2><div id="preview-list"></div></section>`;
  const select = document.querySelector("#exam-chapter");
  function preview() {
    const rows = nmmmhPool(examId, select.value);
    document.querySelector("#preview-heading").textContent = `${rows.length} câu trong chương đã chọn`;
    document.querySelector("#preview-list").innerHTML = rows.map((q) => `<p><strong>Câu ${escapeHtml(q.source_question_number)}</strong> · ${escapeHtml(q.question)}${q.needs_review ? ' <span class="review-badge">Cần rà soát</span>' : ""}</p>`).join("");
  }
  select.addEventListener("change", preview); preview();
  document.querySelector("#full-start").addEventListener("click", () => startNmmmhQuiz(examId, "all", document.querySelector("#full-mode").value));
  document.querySelector("#exam-chapter-form").addEventListener("submit", (event) => {
    event.preventDefault(); startNmmmhQuiz(examId, select.value, document.querySelector("#exam-mode").value, document.querySelector("#exam-random").checked);
  });
}

function questionLabel(question) {
  return question.source_question_number ? `Câu ${question.source_question_number}` : question.id;
}

function richBlocksHtml(blocks = [], imageLinks = true) {
  return blocks.map((block) => {
    if (block.type === "image") {
      const img = `<img class="question-image" src="${escapeHtml(block.src)}" alt="${escapeHtml(block.alt || "Hình nguồn")}" />`;
      // Options are already buttons; do not nest an interactive link in them.
      return imageLinks ? `<a class="source-image-link" href="${escapeHtml(block.src)}" target="_blank" rel="noopener" title="Mở ảnh gốc">${img}</a>` : `<span class="source-image-link">${img}</span>`;
    }
    if (block.type === "table") return `<span class="table-scroll"><table class="source-table"><tbody>${block.rows.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></span>`;
    return `<span class="source-text">${escapeHtml(block.text)}</span>`;
  }).join("");
}

function nmmmhQuestionMeta(question) {
  if (question.subject_id !== "nmmmh") return "";
  const child = question.chapter_child;
  const sources = state.quiz.context?.exam_id === "all" && question.duplicate_status === "confirmed" ? question.duplicate_sources : [question];
  return `<div class="source-meta"><p><strong>Nguồn:</strong> ${sources.map((s) => `${escapeHtml(s.source_exam_code)} / câu ${escapeHtml(s.source_question_number)}`).join(" · ")}</p>
    ${child ? `<p>${escapeHtml(child.code)} · ${escapeHtml(child.name)}${question.classification_needs_review ? " (nhãn đề xuất từ file phân loại)" : ""}</p>` : ""}
    ${question.duplicate_group ? `<span class="session-chip">${question.duplicate_status === "confirmed" ? "Câu trùng đã xác minh" : "Nghi trùng · giữ riêng"}</span>` : ""}
    ${question.needs_review ? `<span class="review-badge">Cần rà soát${question.correct_answer ? " nguồn ảnh" : " · không tính điểm"}</span>` : ""}
    ${question.source_notes?.length ? `<details><summary>Ghi chú nguồn</summary><p>${question.source_notes.map(escapeHtml).join("<br />")}</p></details>` : ""}</div>`;
}

function answerExplanation(question) {
  if (!question.answer_audit || !state.quiz.feedback[question.id]) return "";
  return `<div class="answer-explanation"><strong>Căn cứ:</strong> ${escapeHtml(question.answer_audit.explanation)}</div>`;
}

function returnToSubjectHome() {
  if (state.subject === "nmmmh") {
    const context = state.quiz?.context;
    const params = context?.exam_id && context.exam_id !== "all" ? { exam: context.exam_id, ...(context.chapter_id !== "all" ? { chapter: context.chapter_id } : {}) } : {};
    nmmmh.route = params; history.replaceState(null, "", subjectLink(params));
  }
  renderHome();
}

function renderSessionHistory() {
  app.innerHTML = `<section class="results-head"><h1>Lịch sử làm bài</h1><a href="${subjectLink()}" class="ghost-btn">← Mật mã học</a></section><section class="panel"><div class="table-scroll"><table class="history-table"><thead><tr><th>Thời gian</th><th>Môn</th><th>Đề</th><th>Chương</th><th>Số câu</th><th>Điểm</th></tr></thead><tbody>${state.persisted.history.slice().reverse().map((h) => `<tr><td>${escapeHtml(new Date(h.date).toLocaleString("vi-VN"))}</td><td>${escapeHtml(h.subject || "Kiến trúc máy tính")}</td><td>${escapeHtml(h.exam || h.set_id || "Đề 300 câu")}</td><td>${escapeHtml(h.chapter || h.scope)}</td><td>${h.total}</td><td>${h.score == null ? (h.subject_id === "nmmmh" ? "Chưa chấm" : `${h.correct}/${h.total}`) : `${Number(h.score).toFixed(2)}/10`} ${h.ungraded ? `<small>(${h.ungraded} không tính điểm)</small>` : ""}</td></tr>`).join("") || '<tr><td colspan="6">Chưa có lượt làm bài.</td></tr>'}</tbody></table></div></section>`;
}

async function routeSubject() {
  const sequence = ++nmmmh.routeSequence;
  const params = new URLSearchParams(location.hash.slice(1));
  const isNmmmh = params.get("subject") === "nmmmh";
  document.body.classList.toggle("nmmmh-mode", isNmmmh);
  document.querySelectorAll(".subject-nav a").forEach((link) => {
    if (link.hash === (isNmmmh ? "#subject=nmmmh" : "#subject=ktmt")) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  if (params.get("subject") !== "nmmmh") {
    state.subject = "ktmt";
    if (nmmmh.ktmt) { Object.assign(state, nmmmh.ktmt); nmmmh.ktmt = null; }
    document.querySelector(".brand strong").textContent = "KTMT";
    renderHome(); return;
  }
  if (state.subject !== "nmmmh") nmmmh.ktmt = { questions: state.questions, chapters: state.chapters, activeSet: state.activeSet };
  state.subject = "nmmmh";
  app.innerHTML = '<section class="loading-card"><div class="loader"></div><p>Đang mở môn Mật mã học…</p></section>';
  try {
    await loadNmmmh();
    if (sequence !== nmmmh.routeSequence) return;
    state.questions = nmmmh.questions; state.activeSet = null;
    state.chapters = nmmmh.manifest.chapters.map((c) => c.label);
    document.querySelector(".brand strong").textContent = "NMMMH";
    nmmmh.route = Object.fromEntries(params);
    const examId = params.get("exam"); const chapterId = params.get("chapter") || "all";
    if (examId && examId !== "all" && !nmmmh.manifest.exams.some((e) => e.id === examId)) throw new Error("Mã đề không tồn tại.");
    if (chapterId !== "all" && !nmmmh.manifest.chapters.some((c) => c.id === chapterId)) throw new Error("Chương không tồn tại.");
    if (params.get("view") === "history") return renderSessionHistory();
    if (["mistakes", "bookmarks"].includes(params.get("review"))) return startNmmmhSavedQuiz(params.get("review"));
    if (examId && params.get("action") === "start") return startNmmmhQuiz(examId, chapterId, params.get("mode") === "exam" ? "exam" : "study", params.get("random") === "1");
    renderHome();
  } catch (error) {
    if (sequence !== nmmmh.routeSequence) return;
    app.innerHTML = `<section class="error-card"><h2>Không mở được Mật mã học</h2><p>${escapeHtml(error.message)}</p><a href="${subjectLink()}" class="ghost-btn">Về danh sách đề</a></section>`;
  }
}

window.addEventListener("hashchange", () => { if (state.ready) routeSubject(); });
boot();
