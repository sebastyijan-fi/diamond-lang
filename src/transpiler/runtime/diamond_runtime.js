export const WILD = Symbol("dm_wild");
export const RERAISE = Symbol("dm_reraise");
export const CONTROL_TOOLS = ["c", "t", "b", "e"];

class CapturePattern {
  constructor(name) {
    this.name = name;
  }
}

const CAP_POLICY_MODE = (globalThis?.process?.env?.DIAMOND_CAP_MODE ?? "allow_all");
const CAP_GRANTED = new Set(
  (globalThis?.process?.env?.DIAMOND_CAP_GRANTED ?? "")
    .split(",")
    .map((t) => t.trim())
    .filter((t) => t),
);

export const TRACE_LOG = [];
export const RESOURCE_COUNTER = {};
export let RESOURCE_LIMIT = null;

function parseCapGranted(raw) {
  if (!raw) return [];
  return raw
    .split(",")
    .map((x) => x.trim())
    .filter((x) => x);
}

function toNum(value) {
  if (typeof value === "number") return value;
  if (typeof value === "bigint") return Number(value);
  if (typeof value === "string") {
    const n = Number(value);
    if (!Number.isFinite(n)) throw new Error(`expected number, got ${value}`);
    return n;
  }
  if (typeof value === "boolean") return value ? 1 : 0;
  throw new Error(`expected number-like, got ${typeof value}`);
}

export function capCheck(fnName, declaredTools) {
  if (CAP_POLICY_MODE !== "allow_list") return;
  const missing = declaredTools.filter((tool) => !CONTROL_TOOLS.includes(tool) && !CAP_GRANTED.has(tool));
  if (missing.length > 0) {
    throw new Error(`${fnName}: missing capabilities ${JSON.stringify(missing)}`);
  }
}

export function resourceTick(counter, amount = 1) {
  RESOURCE_COUNTER[counter] = (RESOURCE_COUNTER[counter] ?? 0) + amount;
  if (RESOURCE_LIMIT == null) return;
  const total = Object.values(RESOURCE_COUNTER).reduce((x, y) => x + y, 0);
  if (total > RESOURCE_LIMIT) {
    throw new Error(`resource limit exceeded: ${total} > ${RESOURCE_LIMIT}`);
  }
}

export function traceEnter(fnName, args) {
  TRACE_LOG.push({ event: "enter", fn: fnName, args });
}

export function traceExit(fnName, result) {
  TRACE_LOG.push({ event: "exit", fn: fnName, result });
}

export function isTruthy(value) {
  if (value === null || value === undefined || value === false) return false;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") return value.length > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "object") return Object.keys(value).length > 0;
  return true;
}

export function withErrorContext(exc, fnName) {
  return `${fnName}: ${String(exc?.message ?? exc)}`;
}

export function tryCatch(body, handler) {
  try {
    return body();
  } catch (err) {
    if (err === RERAISE) throw err;
    return handler(err);
  }
}

export function propagate(thunk) {
  return thunk();
}

export function seq(thunks) {
  let out = null;
  for (const thunk of thunks) {
    out = thunk();
  }
  return out;
}

export function reraise() {
  return RERAISE;
}

export function isException(exc, types) {
  if (!types || types.length === 0) return true;
  const name = exc && typeof exc === "object" ? exc.name : typeof exc;
  for (const t of types) {
    if (typeof t === "function" && exc instanceof t) return true;
    if (typeof t === "string" && (name === t || String(exc) === t)) return true;
  }
  return false;
}

export function WILD_PATTERN(value) {
  return WILD;
}

export function capture(name) {
  return new CapturePattern(name);
}

export function match(subject, arms) {
  for (const [pat, thunk] of arms) {
    if (pat instanceof CapturePattern) {
      return thunk(subject);
    }
    if (pat === WILD || subject === pat) {
      return thunk();
    }
  }
  throw new Error(`non-exhaustive match for subject=${String(subject)}`);
}

export function binop(op, left, right) {
  if (op === "+") {
    if (typeof left === "string" || typeof right === "string") return String(left) + String(right);
    return toNum(left) + toNum(right);
  }
  if (op === "-") return toNum(left) - toNum(right);
  if (op === "*") return toNum(left) * toNum(right);
  if (op === "%") return toNum(left) % toNum(right);
  if (op === "==") return left === right;
  if (op === "!=") return left !== right;
  if (op === "<") return toNum(left) < toNum(right);
  if (op === "<=") return toNum(left) <= toNum(right);
  if (op === ">") return toNum(left) > toNum(right);
  if (op === ">=") return toNum(left) >= toNum(right);
  throw new Error(`unsupported operator ${op}`);
}

export function num(value) {
  return toNum(value);
}

export function idiv(a, b) {
  const lhs = toNum(a);
  const rhs = toNum(b);
  if (rhs === 0) throw new Error("diamond_runtime.idiv divide by zero");
  return Math.trunc(lhs / rhs);
}

export function midpoint(a, b) {
  return idiv(toNum(a) + toNum(b), 2);
}

export function pow(a, b) {
  return Math.pow(toNum(a), toNum(b));
}

export function len(x) {
  if (x == null) throw new Error("len of null");
  if (Array.isArray(x) || typeof x === "string") return x.length;
  if (typeof x === "object") return Object.keys(x).length;
  throw new Error(`len unsupported for ${typeof x}`);
}

export function trim(x) {
  return String(x).trim();
}

export function split(x, sep) {
  return String(x).split(sep);
}

export function peek(s, i, defaultValue = undefined) {
  if (!s) return defaultValue;
  if (typeof s === "string") return s[i] ?? defaultValue;
  if (Array.isArray(s)) return s[i] ?? defaultValue;
  throw new Error("peek expects string or list");
}

export function take(s, i, n) {
  if (!s) return "";
  if (n <= 0) return "";
  if (i < 0) i = 0;
  if (typeof s === "string") return s.slice(i, i + n);
  if (Array.isArray(s)) return s.slice(i, i + n);
  throw new Error("take expects string or list");
}

export function guard(cond, msg, pos = null) {
  if (cond) return true;
  if (pos == null) throw new Error(msg);
  throw new Error(`${msg} @ ${pos}`);
}

function isDiamondObject(value) {
  return !!value && typeof value === "object" && value.__dm_kind === "obj";
}

export function obj_new(fields, className = null) {
  if (!fields || typeof fields !== "object" || Array.isArray(fields)) {
    throw new Error("obj_new expects object fields");
  }
  return {
    __dm_kind: "obj",
    __dm_class: className,
    __dm_fields: { ...fields },
  };
}

export function obj_get(obj, name) {
  if (!isDiamondObject(obj)) {
    throw new Error(`expected DiamondObject, got ${typeof obj}`);
  }
  if (!Object.prototype.hasOwnProperty.call(obj.__dm_fields, name)) {
    throw new Error(`unknown field: ${name}`);
  }
  return obj.__dm_fields[name];
}

export function obj_set(obj, name, value) {
  if (!isDiamondObject(obj)) {
    throw new Error(`expected DiamondObject, got ${typeof obj}`);
  }
  if (!Object.prototype.hasOwnProperty.call(obj.__dm_fields, name)) {
    throw new Error(`unknown field: ${name}`);
  }
  obj.__dm_fields[name] = value;
  return value;
}

export function obj_is(left, right) {
  return left === right;
}

export function obj_eq(left, right) {
  return left === right;
}

export function obj_invoke(scope, obj, name, args = []) {
  if (isDiamondObject(obj)) {
    const cls = obj.__dm_class;
    if (!cls) throw new Error(`object has no class binding for method ${name}`);
    const sym = `${cls}__${name}`;
    const fn = scope?.[sym];
    if (typeof fn !== "function") throw new Error(`unknown method ${sym}`);
    return fn(obj, ...args);
  }
  const fn = member(obj, name);
  if (typeof fn !== "function") throw new Error(`member ${name} is not callable`);
  return fn(...args);
}

export function index(obj, index) {
  if (obj == null) throw new Error("index on null");
  const idx = toNum(index);
  if (!Number.isInteger(idx)) throw new Error(`index must be integer: ${idx}`);
  if (idx < 0) throw new Error(`index out of bounds: ${idx}`);
  if (Array.isArray(obj)) {
    if (idx >= obj.length) throw new Error(`index out of bounds: ${idx}`);
    return obj[idx];
  }
  if (typeof obj === "string") {
    if (idx >= obj.length) throw new Error(`index out of bounds: ${idx}`);
    return obj[idx];
  }
  throw new Error("index expects list or string");
}

export function slice(obj, start, end) {
  if (obj == null) throw new Error("slice on null");
  const startIdx = start == null ? undefined : toNum(start);
  const endIdx = end == null ? undefined : toNum(end);
  if (Array.isArray(obj)) return obj.slice(startIdx, endIdx);
  if (typeof obj === "string") return obj.slice(startIdx, endIdx);
  throw new Error("slice expects list or string");
}

export function put(m, key, value) {
  const out = { ...(m ?? {}) };
  out[key] = value;
  return out;
}

export function get(m, key, defaultValue) {
  if (m == null || typeof m !== "object") return defaultValue;
  return Object.prototype.hasOwnProperty.call(m, key) ? m[key] : defaultValue;
}

export function del(m, key) {
  const out = { ...(m ?? {}) };
  delete out[key];
  return out;
}

export function member(obj, key) {
  if (isDiamondObject(obj)) {
    return obj_get(obj, key);
  }
  if (obj == null) throw new Error(`missing member ${key}`);
  if (typeof obj !== "object") return obj[key];
  return obj[key];
}

export function patch(record, updates) {
  if (isDiamondObject(record)) {
    for (const [k, v] of Object.entries(updates ?? {})) {
      obj_set(record, k, v);
    }
    return record;
  }
  return { ...(record ?? {}), ...(updates ?? {}) };
}

export function mapBind(base, keyName, mapper = null) {
  if (!Array.isArray(base)) throw new Error("mapBind expects array");
  if (typeof keyName === "function" && mapper == null) {
    mapper = keyName;
  }
  const out = [];
  for (const item of base) {
    out.push(mapper(item));
  }
  return out;
}

export function left_half(seq) {
  if (!Array.isArray(seq)) throw new Error("left_half expects list");
  return seq.slice(0, Math.floor(len(seq) / 2));
}

export function right_half(seq) {
  if (!Array.isArray(seq)) throw new Error("right_half expects list");
  return seq.slice(Math.floor(len(seq) / 2));
}

export function rangeInclusive(start, end) {
  const out = [];
  for (let i = toNum(start); i <= toNum(end); i += 1) out.push(i);
  return out;
}

export function fold(items, init, step) {
  let acc = init;
  for (const x of items ?? []) acc = step(acc, x);
  return acc;
}

export function call_with(fn, args = null, kwargs = null) {
  if (typeof fn !== "function") throw new Error("call_with requires callable");
  return fn(...(args ?? []), ...(kwargs ? [kwargs] : []));
}

export const callWith = call_with;

export function extern_call(symbol, args = null) {
  throw new Error(`external contract stub invoked: ${symbol} args=${JSON.stringify(args)}`);
}

export const externCall = extern_call;

export function sleep(seconds) {
  const ms = toNum(seconds) * 1000;
  const start = Date.now();
  while (Date.now() - start < ms) {}
}

export function rand_uniform(a, b) {
  const lo = toNum(a);
  const hi = toNum(b);
  const base = Date.now() / 1000;
  const frac = base - Math.floor(base);
  return lo + (hi - lo) * frac;
}

export function is_tuple(value) {
  return Array.isArray(value);
}

export function log_retry_warning(logger, err, delay) {
  if (logger && typeof logger === "object" && typeof logger.warning === "function") {
    logger.warning(`${err}, retrying in ${delay} seconds`);
  }
}

export function make_retry_decorator(
  retryCallFn,
  exceptions = Error,
  tries = -1,
  delay = 0,
  maxDelay = null,
  backoff = 1,
  jitter = 0,
  logger = null,
) {
  return (fn) => (...args) =>
    retryCallFn(fn, args, Object.create(null), exceptions, tries, delay, maxDelay, backoff, jitter, logger);
}

export function ini_repr(value) {
  return JSON.stringify(value);
}

export function ini_pair(a, b) {
  return [a, b];
}

export function ini_splitlines_keepends(data) {
  return String(data).split(/\r?\n/);
}

export function ini_iscommentline(line) {
  const c = String(line).trimStart()[0];
  return c === "#" || c === ";";
}

export function ini_raise(path, lineno, msg) {
  const error = new Error(`${path}:${lineno}: ${msg}`);
  error.name = "IniParseError";
  throw error;
}

export function ini_parseline(path, line, lineno, stripComments, stripSectionWhitespace) {
  let txt = String(line);
  if (ini_iscommentline(txt)) txt = "";
  else txt = txt.trimEnd();
  if (txt === "") return [null, null];

  if (txt[0] === "[") {
    const lineRaw = txt;
    const clean = txt.split("#")[0].split(";")[0];
    if (clean.endsWith("]")) {
      const section = clean.slice(1, -1);
      return [stripSectionWhitespace ? section.trim() : section, null];
    }
    return [null, lineRaw.trim()];
  }

  if (!/^\s/.test(txt)) {
    let name;
    let value;
    try {
      const parts = txt.split("=", 2);
      if (parts.length !== 2) {
        const colon = txt.split(":", 2);
        if (colon.length !== 2) throw new Error();
        [name, value] = colon;
      } else {
        [name, value] = parts;
      }
    } catch {
      throw new Error(`${path}:${lineno}: unexpected line: ${txt}`);
    }
    if (stripComments) {
      value = value.split("#")[0].split(";")[0];
    }
    return [name.trim(), String(value).trim()];
  }

  const data = String(txt).trim();
  if (stripComments) {
    return [null, data.split("#")[0].split(";")[0].trim()];
  }
  return [null, data];
}

export function ini_parse_lines(path, lineIter, stripInlineComments, stripSectionWhitespace = false) {
  const out = [];
  let section = null;
  let i = 0;
  for (const line of lineIter) {
    const [name, value] = ini_parseline(path, line, i, stripInlineComments, stripSectionWhitespace);
    if (name !== null && value !== null) {
      out.push([i, section, name, value]);
    } else if (name !== null && value === null) {
      section = name;
      out.push([i, section, null, null]);
    } else if (name === null && value !== null) {
      if (out.length === 0) {
        ini_raise(path, i, "unexpected value continuation");
      }
      const last = out[out.length - 1];
      if (last[2] == null) throw new Error(`unexpected value continuation @ ${path}:${i}`);
      const prev = last[3];
      last[3] = prev ? `${prev}\n${value}` : value;
    }
    i += 1;
  }
  return out;
}

export function ini_parse_ini_data(path, data, stripInlineComments, stripSectionWhitespace = false) {
  const tokens = ini_parse_lines(path, ini_splitlines_keepends(data), stripInlineComments, stripSectionWhitespace);
  const sources = new Map();
  const sections = {};
  for (const [lineno, section, name, value] of tokens) {
    if (section == null) throw new Error(`no section header defined at ${path}:${lineno}`);
    sources.set(`${section}:${name}`, lineno);
    if (name == null) {
      if (sections[section] != null) throw new Error(`duplicate section ${section}`);
      sections[section] = {};
    } else {
      if (sections[section]?.[name] != null) throw new Error(`duplicate name ${name} in ${section}`);
      if (value == null) throw new Error(`missing value at ${path}:${lineno}`);
      sections[section][name] = value;
    }
  }
  return [sections, sources];
}

export function re_group(match, key = null) {
  if (match == null) return null;
  if (key == null) return match[0] ?? match;
  if (typeof key === "number") return match[key + 1];
  return match.groups ? match.groups[key] : null;
}

export function pad6(text) {
  return String(text).padStart(6, "0");
}

export function parseIntBase(text, base) {
  return parseInt(text, base);
}

export const parse_int_base = parseIntBase;

export function dt_date(year, month, day) {
  return new Date(Date.UTC(year, month - 1, day)).toISOString().slice(0, 10);
}

export function dt_datetime(year, month, day, hour, minute, second, micros, tz) {
  const d = new Date(Date.UTC(year, month - 1, day, hour, minute, second, Math.floor(micros / 1000)));
  return d.toISOString();
}

export function dt_time(hour, minute, second, micros) {
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}:${String(second).padStart(2, "0")}`;
}

export function tz_utc() {
  return "UTC";
}

export function tz_offset(hours, minutes) {
  const sign = hours >= 0 ? "+" : "-";
  return `${sign}${String(Math.abs(hours)).padStart(2, "0")}${String(Math.abs(minutes)).padStart(2, "0")}`;
}

export function to_s(value) {
  if (value == null) return String(value);
  return typeof value === "string" ? value : JSON.stringify(value);
}

export function to_i(value) {
  return parseInt(to_s(value), 10);
}

export function to_b(value) {
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (value == null) return false;
  if (typeof value === "string") {
    const lower = value.toLowerCase();
    if (["true", "1", "yes"].includes(lower)) return true;
    if (["false", "0", "no", ""] .includes(lower)) return false;
  }
  return Boolean(value);
}

export function to_o(value) {
  return value;
}

export function json_dumps(value) {
  const compact = JSON.stringify(value);
  if (compact === undefined) {
    throw new Error("json_dumps: value is not JSON serializable");
  }
  return compact;
}

export function json_loads(text) {
  return JSON.parse(String(text));
}
