// Browser-side mirror of app/domain/codes.py (parse only; generation stays on the server).
const ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
const CITY_CHECK_INDEX = { PR: 1, BE: 2, PA: 3, ME: 4, MA: 5, TO: 6, MO: 7 };
const ALIASES = { O: "0", I: "1", L: "1" };
const EASTERN_DIGITS = /[۰-۹٠-٩]/g;
const SEPARATORS = /[\p{Zs}\p{Pd}\p{Cf}\t\r\n_.]/gu;

function toAsciiDigit(character) {
  const code = character.charCodeAt(0);
  return String(code >= 0x06f0 ? code - 0x06f0 : code - 0x0660);
}

export function normalizeCode(raw) {
  return raw
    .normalize("NFKC")
    .replace(EASTERN_DIGITS, toAsciiDigit)
    .replace(SEPARATORS, "")
    .toUpperCase();
}

function luhnMod32Sum(values, startFactor) {
  let factor = startFactor;
  let total = 0;
  for (let i = values.length - 1; i >= 0; i -= 1) {
    const addend = factor * values[i];
    total += Math.floor(addend / 32) + (addend % 32);
    factor = factor === 2 ? 1 : 2;
  }
  return total;
}

// Returns {ok: true, city, canonical} or {ok: false, problem: "malformed" | "mistyped"}.
export function parseCode(raw) {
  const text = normalizeCode(raw);
  if (text.length !== 13 || !/^[\x00-\x7F]*$/.test(text)) return { ok: false, problem: "malformed" };
  const prefix = text.slice(0, 2).replaceAll("0", "O");
  if (!(prefix in CITY_CHECK_INDEX)) return { ok: false, problem: "malformed" };
  const tail = [...text.slice(2)].map((c) => ALIASES[c] ?? c).join("");
  if ([...tail].some((c) => !ALPHABET.includes(c))) return { ok: false, problem: "malformed" };
  const values = [CITY_CHECK_INDEX[prefix], ...[...tail].map((c) => ALPHABET.indexOf(c))];
  if (luhnMod32Sum(values, 1) % 32 !== 0) return { ok: false, problem: "mistyped" };
  return { ok: true, city: prefix, canonical: prefix + tail };
}

// "TO7KQ2M9XH4R6" -> "TO-7KQ2-M9XH-4R6" (also useful while the user types).
export function formatPrinted(canonical) {
  const rest = canonical.slice(2);
  return [canonical.slice(0, 2), rest.slice(0, 4), rest.slice(4, 8), rest.slice(8)]
    .filter(Boolean)
    .join("-");
}
