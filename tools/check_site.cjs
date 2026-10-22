/* Static buildless validation: no framework or generated question copies. */
const fs = require("node:fs");
const path = require("node:path");
const cp = require("node:child_process");
const katex = require("../vendor/katex/katex.js");
const root = path.resolve(__dirname, "..");
const read = file => JSON.parse(fs.readFileSync(path.join(root, file), "utf8"));
for (const file of ["app.js", "nmmmh.js", "nmmmh-practice.js"]) cp.execFileSync(process.execPath, ["--check", path.join(root, file)]);
const manifest = read("subjects/nmmmh/manifest.json");
const ids = new Set(); let formulae = 0; let images = 0; let hints = 0;
const exams = [...manifest.exams, ...(manifest.collections || []).flatMap(c => c.exams)];
let legacyQuestions = 0;
for (const exam of exams) {
  const rows = read(exam.question_file);
  if (rows.length !== exam.question_count) throw new Error(`Question count: ${exam.id}`);
  if (!exam.collection_id) legacyQuestions += rows.length;
  let previous = -1;
  for (const q of rows) {
    if (ids.has(q.id) || q.source_order <= previous) throw new Error(`Duplicate ID / reordered question: ${q.id}`);
    previous = q.source_order; ids.add(q.id);
    if (q.correct_answer && !["A", "B", "C", "D"].includes(q.correct_answer)) throw new Error(`Invalid key ${q.id}`);
    if (!q.chapter_ids?.length) throw new Error(`Missing classification ${q.id}`);
    if (q.hint) hints += 1;
    for (const holder of [q, q.A, q.B, q.C, q.D]) {
      for (const block of holder.display_blocks || holder.question_blocks || holder.blocks || []) {
        if (block.type === "image") {
          if (block.src.startsWith("data:") || !fs.existsSync(path.join(root, block.src))) throw new Error(`Bad image ${q.id}: ${block.src}`);
          images += 1;
        }
        if (block.type === "text") {
          for (const match of block.text.matchAll(/\\\((.*?)\\\)/gs)) {
            katex.renderToString(match[1], { throwOnError: true, trust: false }); formulae += 1;
          }
        }
      }
    }
    for (const match of (q.hint || "").matchAll(/\\\((.*?)\\\)/gs)) {
      katex.renderToString(match[1], { throwOnError: true, trust: false }); formulae += 1;
    }
  }
}
const expected = manifest.exams.reduce((s,e)=>s+e.question_count,0) + (manifest.collections || []).flatMap(c=>c.exams).reduce((s,e)=>s+e.question_count,0);
if (legacyQuestions !== 173 || ids.size !== expected || hints !== expected) throw new Error(`Coverage: ${ids.size} questions, ${hints} hints`);
console.log(`PASS static build: ${exams.length} exams, ${ids.size} questions, ${hints} hints, ${formulae} KaTeX expressions, ${images} image references; 173 legacy questions preserved`);
