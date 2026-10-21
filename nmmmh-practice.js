/* NMMMH-only extensions. Canonical option IDs and source questions are immutable.
   Session v1 is separate from the existing cross-course localStorage history. */
const NMMMH_SESSION_KEY = "nmmmh-active-session-v1";
let nmmmhStorageWarning = false;

function nmmmhWriteStorage(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); return true; }
  catch { nmmmhStorageWarning = true; return false; }
}

function nmmmhSignature(q) {
  return JSON.stringify([q.question, ...LETTERS.map(l => q[l]), q.correct_answer, q.verification_revision || null]);
}

function saveNmmmhSession() {
  const quiz = state.quiz;
  if (state.subject !== "nmmmh" || !quiz?.context || quiz.context.subject_id !== "nmmmh") return;
  const { questions, ...session } = quiz;
  nmmmhWriteStorage(NMMMH_SESSION_KEY, {
    version: 1, hash: location.hash, session,
    questions: questions.map(q => ({ id: q.id, signature: nmmmhSignature(q) })),
  });
}

function readNmmmhSession() {
  try {
    const saved = JSON.parse(localStorage.getItem(NMMMH_SESSION_KEY) || "null");
    if (saved?.version !== 1 || !Array.isArray(saved.questions) || !saved.questions.length || !saved.session || typeof saved.hash !== "string") return null;
    const ids = new Set();
    const questions = saved.questions.map(item => {
      const q = nmmmh.questions.find(row => row.id === item.id);
      if (!q || ids.has(q.id) || nmmmhSignature(q) !== item.signature) throw new Error("Dataset changed");
      ids.add(q.id); return q;
    });
    const s = saved.session;
    if (!Number.isInteger(s.index) || s.index < 0 || s.index >= questions.length || !["study", "exam"].includes(s.mode)) return null;
    if (s.context?.subject_id !== "nmmmh" || !s.answers || !s.feedback || !s.countedAnswers || !s.optionOrders || typeof s.answers !== "object") return null;
    for (const [id, answer] of Object.entries(s.answers)) if (!ids.has(id) || !LETTERS.includes(answer)) return null;
    for (const q of questions) {
      const order = s.optionOrders[q.id];
      if (!Array.isArray(order) || order.length !== 4 || new Set(order).size !== 4 || !order.every(l => LETTERS.includes(l))) return null;
    }
    return { ...saved, session: { ...s, questions } };
  } catch { return null; }
}

function resumeNmmmhSession(exactHash = true) {
  const saved = readNmmmhSession();
  if (!saved || (exactHash && saved.hash !== location.hash)) return false;
  history.replaceState(null, "", saved.hash);
  nmmmh.route = Object.fromEntries(new URLSearchParams(saved.hash.slice(1)));
  state.quiz = saved.session;
  if (state.quiz.finished) renderResults(); else renderQuiz();
  return true;
}

function nmmmhCanShuffleOptions(q) {
  // "All above" and references to A/B/etc are order-dependent. Keep them
  // unchanged rather than rewriting original content or silently misgrading.
  if (q.source_option_labels_in_figure) return false;
  const options = LETTERS.map(l => q[l]?.text || "").join(" ");
  return !/tất cả|cả (?:ba|bốn|3|4)|đáp án trên|phương án trên|\b[A-D]\s*(?:và|hoặc|,|\/|đều)|(?:đáp án|phương án)\s+[A-D]\b/i.test(options);
}

function initNmmmhSession(quiz) {
  quiz.countedAnswers = {};
  quiz.optionOrders = {};
  quiz.hintOpen = {};
  quiz.explanationOpen = {};
  quiz.revealed = {};
  quiz.attemptId = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`;
  for (const q of quiz.questions) quiz.optionOrders[q.id] = quiz.context.shuffle_options && nmmmhCanShuffleOptions(q) ? shuffle(LETTERS) : [...LETTERS];
}

function displayOptionLetter(q, canonical) {
  if (!canonical || !LETTERS.includes(canonical)) return canonical || "—";
  const order = state.quiz?.optionOrders?.[q.id] || LETTERS;
  return LETTERS[order.indexOf(canonical)] || canonical;
}

function recordNmmmhProgress(q, answer) {
  if (!answer) return;
  const quiz = state.quiz;
  const current = state.persisted.progress[q.id] || { seen: 0, answered: 0, correct: 0 };
  const previous = quiz.countedAnswers[q.id];
  const correct = Boolean(q.correct_answer && answer === q.correct_answer);
  if (previous === undefined) { current.seen += 1; current.answered += 1; if (correct) current.correct += 1; }
  else if (q.correct_answer) current.correct = Math.max(0, current.correct + Number(correct) - Number(previous === q.correct_answer));
  current.lastAnswer = answer;
  current.lastSeen = new Date().toISOString();
  current.subject_id = "nmmmh";
  current.lastAttemptId = quiz.attemptId;
  state.persisted.progress[q.id] = current;
  quiz.countedAnswers[q.id] = answer;
  if (q.correct_answer) {
    if (correct) state.persisted.mistakes.delete(q.id); else state.persisted.mistakes.add(q.id);
  }
  savePersisted();
}

function finalizeNmmmhProgress() {
  for (const q of state.quiz.questions) {
    recordNmmmhProgress(q, state.quiz.answers[q.id]);
    if (q.correct_answer && !state.quiz.answers[q.id]) state.persisted.mistakes.add(q.id);
  }
}

function nmmmhQuizTools(q) {
  const quiz = state.quiz;
  const allowHelp = quiz.mode !== "exam" || quiz.finished;
  const answered = quiz.questions.filter(row => quiz.answers[row.id]).length;
  const correct = quiz.questions.filter(row => row.correct_answer && quiz.answers[row.id] === row.correct_answer).length;
  const wrong = quiz.questions.filter(row => row.correct_answer && quiz.answers[row.id] && quiz.answers[row.id] !== row.correct_answer).length;
  return `<div class="practice-live" role="status">Đã làm ${answered}/${quiz.questions.length}${allowHelp ? ` · Đúng ${correct} · Sai ${wrong}` : " · Chấm khi nộp bài"}</div>
    ${quiz.context.shuffle_options ? `<p class="side-note">${nmmmhCanShuffleOptions(q) ? "Phương án được trộn; chấm bằng ID gốc, không bằng vị trí." : "Giữ thứ tự vì câu tham chiếu nhãn hoặc ảnh có A–D gốc."}</p>` : ""}
    ${allowHelp ? `<div class="button-row help-controls"><button type="button" id="show-hint" class="ghost-btn" aria-expanded="${Boolean(quiz.hintOpen[q.id])}">💡 ${quiz.hintOpen[q.id] ? "Ẩn" : "Gợi ý"} giải nhanh</button>${!quiz.finished ? '<button type="button" id="show-answer" class="ghost-btn">Xem đáp án</button>' : ""}</div>
    ${quiz.hintOpen[q.id] ? `<div class="quick-hint">${escapeHtml(q.hint || "Chưa có mẹo đã kiểm tra cho câu này. Hãy đối chiếu dữ kiện và ảnh nguồn; không suy đoán đáp án.")}</div>` : ""}` : '<p class="side-note">Chế độ thi ẩn gợi ý và đáp án đến khi nộp bài.</p>'}
    ${nmmmhStorageWarning ? '<p class="notice" role="alert">Trình duyệt không cho lưu dữ liệu. Lượt này chỉ còn trong bộ nhớ; tránh đóng hoặc tải lại trang.</p>' : ""}`;
}

function nmmmhAfterQuizRender(q) {
  document.querySelector("#show-hint")?.addEventListener("click", () => { state.quiz.hintOpen[q.id] = !state.quiz.hintOpen[q.id]; renderQuiz(); });
  document.querySelector("#show-answer")?.addEventListener("click", () => {
    state.quiz.revealed[q.id] = true;
    state.quiz.explanationOpen[q.id] = true;
    renderQuiz();
  });
  document.querySelector(".answer-explanation details")?.addEventListener("toggle", (e) => {
    state.quiz.explanationOpen[q.id] = e.target.open; saveNmmmhSession();
  });
  renderNmmmhMath();
  bindNmmmhImageZoom();
  saveNmmmhSession();
}

function renderNmmmhMath() {
  if (state.subject !== "nmmmh" || typeof renderMathInElement !== "function") return;
  renderMathInElement(app, {
    delimiters: [{ left: "\\(", right: "\\)", display: false }, { left: "\\[", right: "\\]", display: true }],
    throwOnError: false, trust: false, strict: "warn", output: "htmlAndMathml",
  });
}

function bindNmmmhImageZoom() {
  let dialog = document.querySelector("#nmmmh-image-dialog");
  if (!dialog) {
    dialog = document.createElement("dialog");
    dialog.id = "nmmmh-image-dialog";
    dialog.innerHTML = '<div class="zoom-toolbar"><button type="button" data-zoom="out" aria-label="Thu nhỏ">−</button><button type="button" data-zoom="in" aria-label="Phóng to">+</button><button type="button" data-zoom="close">Đóng ×</button></div><div class="zoom-viewport"><img alt="Ảnh nguồn phóng to" /></div>';
    document.body.append(dialog);
    dialog.addEventListener("click", e => {
      const action = e.target.closest("[data-zoom]")?.dataset.zoom;
      if (action === "close" || e.target === dialog) dialog.close();
      else if (action) {
        const image = dialog.querySelector("img");
        const width = Number(image.dataset.width) * (action === "in" ? 1.3 : 1 / 1.3);
        image.dataset.width = Math.max(20, Math.min(400, width)); image.style.width = `${image.dataset.width}%`;
      }
    });
  }
  document.querySelectorAll(".nmmmh-mode #app img").forEach(img => {
    // An image inside an option must not also select that option when zoomed.
    img.tabIndex = 0; img.setAttribute("role", "button"); img.setAttribute("aria-label", "Phóng to ảnh nguồn");
    const open = event => {
      event.preventDefault(); event.stopPropagation();
      const target = dialog.querySelector("img"); target.src = img.src; target.dataset.width = "100"; target.style.width = "100%";
      if (!dialog.open) dialog.showModal();
    };
    img.addEventListener("click", open);
    img.addEventListener("keydown", event => { if (["Enter", " "].includes(event.key)) open(event); });
  });
}

function nmmmhPracticePanel() {
  const saved = readNmmmhSession();
  return `<section class="panel practice-panel"><div class="panel-header"><div><h2>Luyện tập linh hoạt</h2><p>Một hoặc nhiều chương · cùng dữ liệu chuẩn với đề gốc · không loại trùng ngầm.</p></div></div>
    ${saved && !saved.session.finished ? '<button type="button" id="resume-nmmmh" class="secondary-btn">Tiếp tục lượt đang làm →</button>' : ""}
    <form id="practice-form" class="form-stack">
      <fieldset class="chapter-checks"><legend>Chọn chương để luyện / tổng hợp</legend>${nmmmh.manifest.chapters.filter(c => nmmmh.questions.some(q => (q.chapter_ids || [q.chapter_id]).includes(c.id))).map(c => `<label><input type="checkbox" name="practice-chapter" value="${escapeHtml(c.id)}" checked /> ${escapeHtml(c.label)}</label>`).join("")}</fieldset>
      <div class="practice-fields"><div class="field"><label for="practice-exam">Đề gốc</label><select id="practice-exam"><option value="all">Tất cả đề</option>${nmmmh.manifest.exams.map(e => `<option value="${e.id}">${escapeHtml(e.source_exam_code)}</option>`).join("")}</select></div>
      <div class="field"><label for="practice-status">Trạng thái đã học</label><select id="practice-status"><option value="all">Tất cả câu</option><option value="new">Chưa làm</option><option value="studied">Đã làm</option><option value="mistakes">Câu sai / chưa đúng</option><option value="bookmarks">Đã đánh dấu</option><option value="review">Cần rà soát nguồn/đáp án</option></select></div>
      <div class="field"><label for="practice-count">Số câu (để trống: toàn bộ)</label><input id="practice-count" type="number" min="1" step="1" placeholder="Toàn bộ" /></div>
      <div class="field"><label for="practice-mode">Chế độ</label><select id="practice-mode"><option value="study">Học</option><option value="exam">Thi</option></select></div></div>
      <label class="check-row"><input type="checkbox" id="practice-random" /> Trộn thứ tự câu</label>
      <label class="check-row"><input type="checkbox" id="practice-options" /> Trộn phương án an toàn (giữ câu có “tất cả đáp án trên”)</label>
      <p id="practice-count-preview" class="muted" role="status"></p><p id="practice-error" class="notice" hidden role="alert"></p>
      <button type="submit" class="primary-btn">Bắt đầu luyện tập →</button>
    </form></section>`;
}

function practicePool() {
  const selected = [...document.querySelectorAll('[name="practice-chapter"]:checked')].map(el => el.value);
  const exam = document.querySelector("#practice-exam").value;
  const status = document.querySelector("#practice-status").value;
  const rows = nmmmh.questions.filter(q => (exam === "all" || q.source_exam_id === exam) && (q.chapter_ids || [q.chapter_id]).some(c => selected.includes(c)));
  return rows.filter(q => status === "new" ? !state.persisted.progress[q.id]?.answered : status === "studied" ? Boolean(state.persisted.progress[q.id]?.answered) : status === "review" ? q.needs_review : ["mistakes", "bookmarks"].includes(status) ? state.persisted[status].has(q.id) && (status !== "mistakes" || q.correct_answer) : true);
}

function bindNmmmhPracticePanel() {
  const form = document.querySelector("#practice-form");
  if (!form) return;
  const preview = () => { document.querySelector("#practice-count-preview").textContent = `${practicePool().length} câu phù hợp · giữ mọi câu của từng đề nguồn`; };
  form.addEventListener("change", preview); preview();
  document.querySelector("#resume-nmmmh")?.addEventListener("click", () => resumeNmmmhSession(false));
  form.addEventListener("submit", e => {
    e.preventDefault();
    let pool = practicePool();
    const count = Number(document.querySelector("#practice-count").value) || pool.length;
    const error = document.querySelector("#practice-error");
    if (!pool.length || !Number.isInteger(count) || count < 1 || count > pool.length) {
      error.hidden = false; error.textContent = !pool.length ? "Không có câu phù hợp. Hãy chọn chương hoặc đổi bộ lọc." : `Chọn số câu từ 1 đến ${pool.length}, hoặc để trống để làm toàn bộ.`; return;
    }
    const chapters = [...form.querySelectorAll('[name="practice-chapter"]:checked')].map(el => el.value);
    const exam = document.querySelector("#practice-exam").value;
    const random = document.querySelector("#practice-random").checked;
    if (random) pool = shuffle(pool);
    pool = pool.slice(0, count);
    const chapterLabel = chapters.map(id => nmmmh.manifest.chapters.find(c => c.id === id).label).join("; ");
    const context = { ...nmmmhContext(exam, "all"), chapter: chapterLabel, chapter_id: chapters.join(","), chapter_ids: chapters, scope_kind: chapters.length > 1 ? "mixed_practice" : "chapter_practice", shuffle_options: document.querySelector("#practice-options").checked };
    nmmmh.route = { practice: "1" }; history.replaceState(null, "", subjectLink(nmmmh.route));
    startQuiz("practice", random, document.querySelector("#practice-mode").value, pool, context);
  });
}
