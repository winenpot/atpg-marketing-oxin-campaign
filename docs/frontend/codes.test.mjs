// Checks codes.js against the shared vectors and format registry.
// Run: node docs/frontend/codes.test.mjs (also run by tests/unit/test_code_vectors.py).
import { readFileSync } from "node:fs";
import { DEFAULT_FORMAT_ID, FORMATS, parseCode } from "./codes.js";

const read = (name) => JSON.parse(readFileSync(new URL(name, import.meta.url), "utf8"));
const vectors = read("./code-test-vectors.json");
const registry = read("./code-formats.json");
const failures = [];

if (registry.default_format_id !== DEFAULT_FORMAT_ID) {
  failures.push(`default format ${DEFAULT_FORMAT_ID} != ${registry.default_format_id}`);
}
const ids = (o) => Object.keys(o).sort().join(",");
if (ids(FORMATS) !== ids(registry.formats)) {
  failures.push(`formats ${ids(FORMATS)} != ${ids(registry.formats)}`);
}
for (const [id, spec] of Object.entries(registry.formats)) {
  const mine = FORMATS[id];
  if (!mine) continue;
  const same =
    mine.alphabet === spec.alphabet &&
    mine.bodyLength === spec.body_length &&
    mine.grouping.join() === spec.grouping.join() &&
    JSON.stringify(Object.entries(mine.aliases).sort()) ===
      JSON.stringify(Object.entries(spec.aliases).sort());
  if (!same) failures.push(`format ${id} differs from code-formats.json`);
}

for (const v of vectors) {
  const got = parseCode(v.input);
  const ok = v.ok
    ? got.ok && got.canonical === v.canonical && got.formatId === v.format_id
    : !got.ok && got.problem === v.problem;
  if (!ok) failures.push(`${v.note} (${JSON.stringify(v.input)}): got ${JSON.stringify(got)}`);
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log(`ok: ${vectors.length} vectors, ${ids(FORMATS)}`);
