const STORAGE_KEY = "ktmt-quiz-lab-v1";
const LETTERS = ["A", "B", "C", "D"];

const app = document.querySelector("#app");
const state = {
  questions: [],
  chapters: [],
  quiz: null,
  persisted: loadPersisted(),
};

function loadPersisted() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    return {
      bookmarks: new Set(raw.bookmarks || []),
      mistakes: new Set(raw.mistakes || []),
      progress: raw.progress || {},
      history: raw.history || [],
    };
  } catch {
    return { bookmarks: new Set(), mistakes: new Set(), progress: {}, history: [] };
  }
}

function savePersisted() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    bookmarks: [...state.persisted.bookmarks],
    mistakes: [...state.persisted.mistakes],
    progress: state.persisted.progress,
    history: state.persisted.history.slice(-40),
  }));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function shuffle(items) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function getQuestion(id) {
  return state.questions.find((question) => question.id === id);
}

function chapterCounts() {
  return state.chapters.map((chapter) => ({
    chapter,
    count: state.questions.filter((question) => question.chapter === chapter).length,
    completed: state.questions.filter((question) => question.chapter === chapter && state.persisted.progress[question.id]?.answered).length,
  }));
}

function updateProgress(question, answer, isCorrect) {
  const current = state.persisted.progress[question.id] || { seen: 0, answered: 0, correct: 0 };
  current.seen += 1;
  if (answer) {
    current.answered += 1;
    current.lastAnswer = answer;
  }
  if (isCorrect) current.correct += 1;
  current.lastSeen = new Date().toISOString();
  state.persisted.progress[question.id] = current;

  if (question.correct_answer && answer) {
    if (isCorrect) state.persisted.mistakes.delete(question.id);
    else state.persisted.mistakes.add(question.id);
  }
  savePersisted();
}

function renderStats() {
  const answered = Object.values(state.persisted.progress).reduce((sum, item) => sum + (item.answered || 0), 0);
  const correct = Object.values(state.persisted.progress).reduce((sum, item) => sum + (item.correct || 0), 0);
  const accuracy = answered ? `${Math.round(correct / answered * 100)}%` : "—";
  return `
    <div class="stats-grid">
      <div class="stat-card"><span class="stat-icon">◎</span><div><span class="stat-value">${state.questions.length}</span><span class="stat-label">Tổng câu hỏi</span></div></div>
      <div class="stat-card"><span class="stat-icon">⌘</span><div><span class="stat-value">${state.chapters.length}</span><span class="stat-label">Chương học</span></div></div>
      <div class="stat-card"><span class="stat-icon">☆</span><div><span class="stat-value">${state.persisted.bookmarks.size}</span><span class="stat-label">Câu đã đánh dấu</span></div></div>
      <div class="stat-card"><span class="stat-icon">↗</span><div><span class="stat-value">${accuracy}</span><span class="stat-label">Độ chính xác</span></div></div>
    </div>`;
}

function renderHome() {
  const chapters = chapterCounts();
  app.innerHTML = `
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Computer Architecture · interactive study</p>
        <h1>Học KTMT theo cách<br />nhớ được lâu hơn.</h1>
        <p>Ngân hàng câu hỏi được giữ nguyên thứ tự, chia theo chương và có đáp án được đối chiếu từ vùng đánh dấu trong PDF nguồn.</p>
        <div class="hero-pills"><span>01 · Chọn chương</span><span>02 · Học hoặc thi</span><span>03 · Theo dõi tiến độ</span></div>
      </div>
      <div class="hero-stamp"><span class="stamp-label">NGÂN HÀNG KTMT</span><strong>${state.questions.length}</strong><span>câu hỏi sẵn sàng để luyện tập</span><i aria-hidden="true">↗</i></div>
    </section>
    ${renderStats()}
    <section class="setup-grid">
      <div class="panel">
        <div class="panel-header"><div><h2>Tạo một lượt học</h2><p>Chọn một chương và cách sắp xếp câu hỏi.</p></div></div>
        <form id="quiz-form" class="form-stack">
          <div class="field"><label for="scope">Chọn chương</label><select id="scope">
            ${chapters.map(({ chapter, count }) => `<option value="${escapeHtml(chapter)}">${escapeHtml(chapter)} · ${count} câu</option>`).join("")}
          </select></div>
          <label class="check-row" for="randomize"><input id="randomize" type="checkbox" /><span><strong>Trộn câu hỏi ngẫu nhiên</strong><small>Không chọn để làm theo đúng thứ tự trong PDF.</small></span></label>
          <div class="field"><label>Chế độ</label><div class="segmented"><button type="button" class="mode-btn active" data-mode="study">Học · xem ngay</button><button type="button" class="mode-btn" data-mode="exam">Thi · chấm cuối</button></div></div>
          <div class="button-row"><button class="primary-btn" type="submit">Bắt đầu lượt mới →</button><button class="ghost-btn" type="button" id="continue-btn" ${Object.keys(state.persisted.progress).length ? "" : "disabled"}>Xem tiến độ</button></div>
        </form>
        <div class="notice">Bạn sẽ làm toàn bộ câu hỏi của chương đã chọn. Các câu có đáp án được xác minh từ highlight vàng trong PDF; dữ liệu và tiến độ được lưu ngay trên trình duyệt.</div>
      </div>
      <div class="panel">
        <div class="panel-header"><div><h2>Bản đồ chương</h2><p>Đi nhanh đến phần bạn muốn củng cố.</p></div><span class="panel-kicker">${chapters.length} phần</span></div>
        <div class="chapter-list">${chapters.map(({ chapter, count, completed }) => {
          const percent = count ? Math.round(completed / count * 100) : 0;
          return `<button type="button" class="chapter-row quick-chapter" data-chapter="${escapeHtml(chapter)}"><span class="chapter-row-main"><strong>${escapeHtml(chapter)}</strong><small>${completed}/${count} câu đã luyện</small><span class="chapter-progress"><span style="width:${percent}%"></span></span></span><span class="chapter-row-side"><b>${count}</b><span>câu&nbsp; →</span></span></button>`;
        }).join("")}</div>
      </div>
    </section>`;

  let mode = "study";
  document.querySelectorAll(".mode-btn").forEach((button) => button.addEventListener("click", () => {
    mode = button.dataset.mode;
    document.querySelectorAll(".mode-btn").forEach((item) => item.classList.toggle("active", item === button));
  }));
  document.querySelectorAll(".quick-chapter").forEach((button) => button.addEventListener("click", () => {
    const scope = document.querySelector("#scope");
    scope.value = button.dataset.chapter;
    scope.focus();
    document.querySelector("#quiz-form").scrollIntoView({ behavior: "smooth", block: "center" });
  }));
  document.querySelector("#quiz-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const scope = document.querySelector("#scope").value;
    const randomize = document.querySelector("#randomize").checked;
    startQuiz(scope, randomize, mode);
  });
  document.querySelector("#continue-btn")?.addEventListener("click", () => renderProgress());
}

function getPool(scope) {
  if (scope === "bookmarked") return state.questions.filter((question) => state.persisted.bookmarks.has(question.id));
  if (scope === "mistakes") return state.questions.filter((question) => state.persisted.mistakes.has(question.id));
  if (scope === "all") return state.questions;
  return state.questions.filter((question) => question.chapter === scope);
}

function startQuiz(scope, randomize = false, mode = "study", fixedQuestions = null) {
  const pool = fixedQuestions || getPool(scope);
  if (!pool.length) {
    window.alert("Phạm vi này chưa có câu hỏi phù hợp.");
    return;
  }
  const questions = fixedQuestions ? [...fixedQuestions] : (randomize ? shuffle(pool) : [...pool]);
  state.quiz = {
    questions,
    index: 0,
    answers: {},
    mode,
    feedback: {},
    scope,
    randomize: Boolean(randomize),
    startedAt: new Date().toISOString(),
  };
  renderQuiz();
}

function optionHtml(question, letter) {
  const option = question[letter] || { text: "", image: null };
  const selected = state.quiz.answers[question.id] === letter;
  const feedback = state.quiz.feedback[question.id];
  let resultClass = selected ? "selected" : "";
  if (feedback && question.correct_answer) {
    if (letter === question.correct_answer) resultClass = "correct";
    else if (selected) resultClass = "incorrect";
  }
  return `<button type="button" class="option-btn ${resultClass}" data-option="${letter}">
    <span class="option-key">${letter}</span><span class="option-text">${escapeHtml(option.text)}${option.image ? `<img class="option-img" src="${escapeHtml(option.image)}" alt="Hình trong đáp án ${letter}" />` : ""}</span>
  </button>`;
}

function feedbackHtml(question) {
  const feedback = state.quiz.feedback[question.id];
  if (!feedback) return "";
  if (!question.correct_answer) return `<div class="feedback pending"><strong>Chưa có đáp án xác minh.</strong> Câu này được giữ lại để bạn rà soát nguồn.</div>`;
  if (feedback === question.correct_answer) return `<div class="feedback correct"><strong>Chính xác.</strong> Đáp án đúng là ${question.correct_answer}.</div>`;
  return `<div class="feedback incorrect"><strong>Chưa đúng.</strong> Đáp án đúng là ${question.correct_answer}.</div>`;
}

function renderQuiz() {
  const quiz = state.quiz;
  const question = quiz.questions[quiz.index];
  const selected = quiz.answers[question.id];
  const marked = state.persisted.bookmarks.has(question.id);
  const progress = Math.round((quiz.index + 1) / quiz.questions.length * 100);
  app.innerHTML = `
    <section class="quiz-shell">
      <div class="quiz-main">
        <div class="quiz-toolbar"><div class="quiz-toolbar-left"><button class="back-link" id="back-home">← Trang chủ</button><span class="muted">/ ${quiz.mode === "exam" ? "Chế độ thi" : "Chế độ học"}</span></div><div class="quiz-toolbar-right"><span class="session-chip">${quiz.randomize ? "Đã trộn" : "Theo thứ tự"}</span><span class="muted">${quiz.index + 1}/${quiz.questions.length}</span></div></div>
        <div class="progress-wrap"><div class="progress-bar" style="width:${progress}%"></div></div>
        <article class="question-card">
          <div class="question-meta"><span><span class="question-id">${escapeHtml(question.id)}</span> · ${escapeHtml(question.chapter)}</span><button id="bookmark" class="bookmark-btn ${marked ? "is-marked" : ""}" type="button">${marked ? "★ Đã đánh dấu" : "☆ Đánh dấu"}</button></div>
          <h2 class="question-text">${escapeHtml(question.question)}</h2>
          ${question.question_image ? `<img class="question-image" src="${escapeHtml(question.question_image)}" alt="Sơ đồ minh họa cho câu ${escapeHtml(question.id)}" />` : ""}
          <div class="options">${LETTERS.map((letter) => optionHtml(question, letter)).join("")}</div>
          ${feedbackHtml(question)}
          <div class="quiz-actions"><div class="left"><button class="ghost-btn" id="prev" type="button" ${quiz.index === 0 ? "disabled" : ""}>← Trước</button></div><div class="right"><button class="ghost-btn" id="next" type="button">${quiz.index === quiz.questions.length - 1 ? "Xem kết quả" : "Câu tiếp →"}</button></div></div>
        </article>
      </div>
      <aside class="side-panel"><div class="panel"><div class="side-title"><strong>Điều hướng đề</strong><span>${quiz.questions.length} câu</span></div><div class="question-map">${quiz.questions.map((item, index) => `<button type="button" class="map-dot ${index === quiz.index ? "current" : ""} ${quiz.answers[item.id] ? "answered" : ""} ${state.persisted.bookmarks.has(item.id) ? "marked" : ""}" data-index="${index}" aria-label="Mở câu ${index + 1}">${index + 1}</button>`).join("")}</div><p class="side-note">${quiz.mode === "exam" ? "Đáp án sẽ được hiển thị sau khi bạn kết thúc đề." : "Chọn đáp án để nhận phản hồi ngay."}</p></div></aside>
    </section>`;

  document.querySelector("#back-home").addEventListener("click", renderHome);
  document.querySelector("#bookmark").addEventListener("click", () => {
    if (state.persisted.bookmarks.has(question.id)) state.persisted.bookmarks.delete(question.id);
    else state.persisted.bookmarks.add(question.id);
    savePersisted(); renderQuiz();
  });
  document.querySelectorAll(".option-btn").forEach((button) => button.addEventListener("click", () => {
    const answer = button.dataset.option;
    state.quiz.answers[question.id] = answer;
    if (quiz.mode === "study") state.quiz.feedback[question.id] = answer;
    const correct = Boolean(question.correct_answer && answer === question.correct_answer);
    updateProgress(question, answer, correct);
    renderQuiz();
  }));
  document.querySelector("#prev").addEventListener("click", () => { if (quiz.index > 0) { quiz.index -= 1; renderQuiz(); } });
  document.querySelector("#next").addEventListener("click", () => {
    if (quiz.index === quiz.questions.length - 1) finishQuiz();
    else { quiz.index += 1; renderQuiz(); }
  });
  document.querySelectorAll(".map-dot").forEach((button) => button.addEventListener("click", () => { quiz.index = Number(button.dataset.index); renderQuiz(); }));
}

function resultFor(question) {
  const answer = state.quiz.answers[question.id] || null;
  if (!question.correct_answer) return "pending";
  if (!answer) return "wrong";
  return answer === question.correct_answer ? "correct" : "wrong";
}

function finishQuiz() {
  state.quiz.questions.forEach((question) => { state.quiz.feedback[question.id] = state.quiz.answers[question.id] || true; });
  const graded = state.quiz.questions.filter((question) => question.correct_answer);
  const correct = graded.filter((question) => state.quiz.answers[question.id] === question.correct_answer).length;
  const answered = state.quiz.questions.filter((question) => state.quiz.answers[question.id]).length;
  state.persisted.history.push({ date: new Date().toISOString(), mode: state.quiz.mode, total: state.quiz.questions.length, answered, correct, scope: state.quiz.scope });
  savePersisted();
  renderResults();
}

function renderResults() {
  const graded = state.quiz.questions.filter((question) => question.correct_answer);
  const correct = graded.filter((question) => state.quiz.answers[question.id] === question.correct_answer).length;
  const pending = state.quiz.questions.filter((question) => !question.correct_answer).length;
  const wrong = graded.length - correct;
  app.innerHTML = `
    <section class="results-head"><div><p class="eyebrow">Session complete</p><h1>Kết quả của bạn</h1><p class="muted">${state.quiz.mode === "exam" ? "Đề đã được chấm sau khi kết thúc." : "Bạn có thể mở lại từng câu để xem đáp án và ôn lại."}</p></div><div class="score-card"><strong>${correct}/${graded.length || state.quiz.questions.length}</strong><span>${pending ? `${pending} câu cần rà soát nguồn` : "câu đúng"}</span></div></section>
    <div class="button-row" style="margin:0 0 20px"><button class="primary-btn" id="retry" type="button">Làm lại đề này</button><button class="secondary-btn" id="review-wrong" type="button" ${wrong ? "" : "disabled"}>Ôn ${wrong} câu sai</button><button class="ghost-btn" id="result-home" type="button">Về trang chủ</button></div>
    <section class="results-grid">${state.quiz.questions.map((question) => {
      const status = resultFor(question);
      const answer = state.quiz.answers[question.id];
      const label = status === "correct" ? "Đúng" : status === "pending" ? "Cần rà soát" : "Sai / bỏ trống";
      return `<article class="result-item is-${status}"><div class="result-item-head"><strong>${escapeHtml(question.id)}</strong><span class="result-badge">${label}</span></div><p class="result-question">${escapeHtml(question.question)}</p><p class="result-answer">Bạn chọn: <strong>${answer || "—"}</strong> · Đáp án: <strong>${question.correct_answer || "chưa xác minh"}</strong></p><button class="ghost-btn result-open" type="button" data-id="${escapeHtml(question.id)}">Mở câu hỏi</button></article>`;
    }).join("")}</section>`;
  document.querySelector("#result-home").addEventListener("click", renderHome);
  document.querySelector("#retry").addEventListener("click", () => startQuiz(state.quiz.scope, state.quiz.randomize, state.quiz.mode, state.quiz.questions));
  document.querySelector("#review-wrong").addEventListener("click", () => {
    const wrongQuestions = state.quiz.questions.filter((question) => resultFor(question) === "wrong");
    if (wrongQuestions.length) startQuiz("mistakes", false, "study", wrongQuestions);
  });
  document.querySelectorAll(".result-open").forEach((button) => button.addEventListener("click", () => {
    const index = state.quiz.questions.findIndex((question) => question.id === button.dataset.id);
    state.quiz.index = Math.max(index, 0); renderQuiz();
  }));
}

function renderProgress() {
  const rows = state.questions.filter((question) => state.persisted.progress[question.id]);
  app.innerHTML = `<section class="results-head"><div><p class="eyebrow">Local progress</p><h1>Tiến độ học</h1><p class="muted">Lịch sử chỉ được lưu trong localStorage trên trình duyệt này.</p></div><button class="ghost-btn" id="progress-home" type="button">← Trang chủ</button></section><section class="panel"><div class="results-grid">${rows.length ? rows.map((question) => { const p = state.persisted.progress[question.id]; return `<article class="result-item"><div class="result-item-head"><strong>${escapeHtml(question.id)}</strong><span class="result-badge">${p.correct || 0} đúng</span></div><p class="result-question">${escapeHtml(question.question)}</p><p class="result-answer">Đã trả lời ${p.answered || 0} lần · xem ${p.seen || 0} lần</p></article>`; }).join("") : `<div class="empty-state">Bạn chưa có tiến độ nào. Hãy bắt đầu một lượt học.</div>`}</div></section>`;
  document.querySelector("#progress-home").addEventListener("click", renderHome);
}

async function boot() {
  try {
    const response = await fetch("questions.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Không thể tải questions.json (${response.status})`);
    state.questions = await response.json();
    state.chapters = [...new Set(state.questions.map((question) => question.chapter))];
    renderHome();
  } catch (error) {
    app.innerHTML = `<section class="error-card"><h2>Không tải được ngân hàng câu hỏi</h2><p>${escapeHtml(error.message)}</p><p>Hãy chạy web qua HTTP, ví dụ <code>python3 -m http.server 8000</code>, rồi mở <code>http://localhost:8000</code>.</p></section>`;
  }
}

boot();
