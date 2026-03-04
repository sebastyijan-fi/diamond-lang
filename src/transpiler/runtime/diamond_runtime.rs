use serde_json::{json, Map, Value};
use std::cell::RefCell;
use std::collections::HashMap;
use std::collections::HashSet;
use std::io::{self, Write};
use std::panic::{self, AssertUnwindSafe};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

pub const WILD: &str = "__dm_wild__";
pub const RERAISE: &str = "__dm_reraise__";
const CONTROL_TOOLS: &[&str] = &["c", "t", "b", "e"];

thread_local! {
    static TRACE_LOG: RefCell<Vec<HashMap<&'static str, Value>>> = const { RefCell::new(Vec::new()) };
    static RESOURCE_COUNTER: RefCell<HashMap<String, i64>> = RefCell::new(HashMap::new());
    static RESOURCE_LIMIT: RefCell<Option<i64>> = RefCell::new(None);
    static CAP_POLICY_MODE: RefCell<String> = RefCell::new(
        std::env::var("DIAMOND_CAP_MODE").unwrap_or_else(|_| "allow_all".to_string())
    );
    static CAP_GRANTED: RefCell<HashSet<String>> = RefCell::new(HashSet::new());
}

#[derive(Debug)]
pub struct IniParseError {
    pub path: String,
    pub lineno: i64,
    pub msg: String,
}

impl std::fmt::Display for IniParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}:{}: {}", self.path, self.lineno, self.msg)
    }
}

impl std::error::Error for IniParseError {}

fn parse_cap_mode() -> String {
    std::env::var("DIAMOND_CAP_MODE").unwrap_or_else(|_| "allow_all".to_string())
}

fn parse_cap_granted() -> HashSet<String> {
    let raw = std::env::var("DIAMOND_CAP_GRANTED").unwrap_or_default();
    raw.split(',')
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(ToString::to_string)
        .collect()
}

pub fn reset_capability_state() {
    CAP_GRANTED.with(|g| *g.borrow_mut() = parse_cap_granted());
    CAP_POLICY_MODE.with(|m| *m.borrow_mut() = parse_cap_mode());
}

pub fn declared_capabilities(declared_tools: &[&str]) -> Vec<&str> {
    declared_tools
        .iter()
        .copied()
        .filter(|tool| !CONTROL_TOOLS.contains(tool))
        .collect()
}

pub fn cap_check(fn_name: &str, declared_tools: &[&str]) {
    let required = declared_capabilities(declared_tools);
    if required.is_empty() {
        return;
    }
    let mode = CAP_POLICY_MODE.with(|mode| mode.borrow().clone());
    if mode == "allow_all" {
        return;
    }
    let granted = CAP_GRANTED.with(|gr| gr.borrow().clone());
    let missing: Vec<_> = required.into_iter().filter(|tool| !granted.contains(*tool)).collect();
    if !missing.is_empty() {
        panic!("{fn_name}: missing capabilities {missing:?}");
    }
}

pub fn set_capability_policy(mode: &str, granted: &[&str]) {
    CAP_POLICY_MODE.with(|m| *m.borrow_mut() = mode.to_string());
    CAP_GRANTED.with(|g| {
        g.borrow_mut().clear();
        for tool in granted {
            g.borrow_mut().insert((*tool).to_string());
        }
    });
}

pub fn reset_capability_policy() {
    CAP_POLICY_MODE.with(|m| *m.borrow_mut() = parse_cap_mode());
    CAP_GRANTED.with(|g| *g.borrow_mut() = parse_cap_granted());
}

pub fn trace_enter(fn_name: &str, args: Vec<Value>) {
    TRACE_LOG.with(|log| {
        log.borrow_mut().push(HashMap::from([
            ("event", json!("enter")),
            ("fn", json!(fn_name)),
            ("args", json!(args)),
        ]));
    });
}

pub fn trace_exit(fn_name: &str, result: &Value) {
    TRACE_LOG.with(|log| {
        log.borrow_mut().push(HashMap::from([
            ("event", json!("exit")),
            ("fn", json!(fn_name)),
            ("result", result.clone()),
        ]));
    });
}

pub fn with_error_context(err: &str, fn_name: &str) -> String {
    format!("{fn_name}: {err}")
}

pub fn resource_tick(counter: &str, amount: i64) {
    RESOURCE_COUNTER.with(|r| {
        let mut counters = r.borrow_mut();
        let next = counters.entry(counter.to_string()).or_default();
        *next += amount;
    });
    let limit = RESOURCE_LIMIT.with(|limit| *limit.borrow());
    if let Some(limit) = limit {
        let total: i64 = RESOURCE_COUNTER.with(|r| r.borrow().values().sum());
        if total > limit {
            panic!("resource limit exceeded: {total} > {limit}");
        }
    }
}

pub fn set_resource_limit(limit: i64) {
    RESOURCE_LIMIT.with(|x| *x.borrow_mut() = Some(limit));
}

pub fn reset_resource_limit() {
    RESOURCE_LIMIT.with(|x| *x.borrow_mut() = None);
}

fn parse_num(value: &Value) -> f64 {
    match value {
        Value::Number(n) => n.as_f64().unwrap_or(0.0),
        Value::String(s) => s.parse::<f64>().unwrap_or(0.0),
        Value::Bool(b) => {
            if *b {
                1.0
            } else {
                0.0
            }
        }
        _ => 0.0,
    }
}

fn as_i64(value: &Value) -> i64 {
    if let Value::Number(n) = value {
        if let Some(v) = n.as_i64() {
            return v;
        }
        if let Some(v) = n.as_u64() {
            return v as i64;
        }
        if let Some(v) = n.as_f64() {
            return v as i64;
        }
    }
    parse_num(value) as i64
}

pub fn is_truthy(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::Number(n) => n.as_i64().is_some_and(|n| n != 0),
        Value::String(s) => !s.is_empty(),
        Value::Array(a) => !a.is_empty(),
        Value::Object(o) => !o.is_empty(),
    }
}

pub fn num(raw: &str) -> Value {
    if raw.contains(['.', 'e', 'E']) {
        return json!(raw.parse::<f64>().unwrap_or(0.0));
    }
    match raw.parse::<i64>() {
        Ok(v) => json!(v),
        Err(_) => json!(raw.parse::<f64>().unwrap_or(0.0)),
    }
}

pub fn idiv(a: Value, b: Value) -> Value {
    let denominator = parse_num(&b);
    if denominator == 0.0 {
        panic!("diamond_runtime.idiv divide by zero");
    }
    let result = (parse_num(&a) / denominator).trunc() as i64;
    json!(result)
}

pub fn midpoint(a: Value, b: Value) -> Value {
    let sum = parse_num(&a) + parse_num(&b);
    json!((sum / 2.0).floor() as i64)
}

pub fn pow(a: Value, b: Value) -> Value {
    json!(parse_num(&a).powf(parse_num(&b)))
}

pub fn binop(op: &str, left: Value, right: Value) -> Value {
    match op {
        "+" => {
            if left.is_string() || right.is_string() {
                json!(format!("{}{}", to_s(&left), to_s(&right)))
            } else {
                json!(parse_num(&left) + parse_num(&right))
            }
        }
        "-" => json!(parse_num(&left) - parse_num(&right)),
        "*" => json!(parse_num(&left) * parse_num(&right)),
        "%" => json!(parse_num(&left) % parse_num(&right)),
        "==" => json!(left == right),
        "!=" => json!(left != right),
        "<" => json!(parse_num(&left) < parse_num(&right)),
        "<=" => json!(parse_num(&left) <= parse_num(&right)),
        ">" => json!(parse_num(&left) > parse_num(&right)),
        ">=" => json!(parse_num(&left) >= parse_num(&right)),
        _ => panic!("unsupported operator {op}"),
    }
}

pub fn len(x: Value) -> Value {
    let out = match x {
        Value::Array(a) => a.len() as i64,
        Value::String(s) => s.len() as i64,
        Value::Object(o) => o.len() as i64,
        _ => panic!("len unsupported"),
    };
    json!(out)
}

pub fn trim(x: Value) -> Value {
    json!(to_s(&x).trim().to_string())
}

pub fn split(x: Value, sep: &str) -> Value {
    let base = to_s(&x);
    let out: Vec<Value> = base.split(sep).map(|x| Value::String(x.to_string())).collect();
    Value::Array(out)
}

pub fn peek(s: Value, i: Value, default: Value) -> Value {
    let index = as_i64(&i) as usize;
    match s {
        Value::String(s) => s.chars().nth(index).map(|x| Value::String(x.to_string())).unwrap_or(default),
        Value::Array(items) => items.get(index).cloned().unwrap_or(default),
        _ => panic!("peek expects string or array"),
    }
}

pub fn take(s: Value, i: Value, n: Value) -> Value {
    if parse_num(&n) <= 0.0 {
        return json!("");
    }
    let start = as_i64(&i).max(0) as usize;
    let count = parse_num(&n) as usize;
    match s {
        Value::String(s) => Value::String(s.chars().skip(start).take(count).collect()),
        Value::Array(items) => Value::Array(items.into_iter().skip(start).take(count).collect()),
        _ => panic!("take expects string or array"),
    }
}

pub fn guard(cond: Value, msg: &str, pos: Option<Value>) -> bool {
    if is_truthy(&cond) {
        return true;
    }
    match pos {
        Some(value) => panic!("{} @ {value}", msg),
        None => panic!("{msg}"),
    }
}

fn is_diamond_object(value: &Value) -> bool {
    match value {
        Value::Object(map) => map.get("__dm_kind").and_then(Value::as_str) == Some("obj"),
        _ => false,
    }
}

pub fn obj_new(fields: Value, class_name: Option<&str>) -> Value {
    let out_fields = match fields {
        Value::Object(m) => m,
        _ => panic!("obj_new expects object fields"),
    };
    let mut out = Map::new();
    out.insert("__dm_kind".to_string(), Value::String("obj".to_string()));
    match class_name {
        Some(name) => out.insert("__dm_class".to_string(), Value::String(name.to_string())),
        None => out.insert("__dm_class".to_string(), Value::Null),
    };
    out.insert("__dm_fields".to_string(), Value::Object(out_fields));
    Value::Object(out)
}

pub fn obj_class_name(obj: &Value) -> Option<&str> {
    match obj {
        Value::Object(map) => map.get("__dm_class").and_then(Value::as_str),
        _ => None,
    }
}

pub fn obj_get(obj: Value, name: &str) -> Value {
    match obj {
        Value::Object(map) => {
            let fields = map.get("__dm_fields").and_then(Value::as_object).unwrap_or_else(|| panic!("expected DiamondObject"));
            fields.get(name).cloned().unwrap_or_else(|| panic!("unknown field: {name}"))
        }
        _ => panic!("expected DiamondObject"),
    }
}

pub fn member(obj: Value, name: &str) -> Value {
    if is_diamond_object(&obj) {
        return obj_get(obj, name);
    }
    match obj {
        Value::Object(map) => map.get(name).cloned().unwrap_or(Value::Null),
        _ => panic!("member on non-object"),
    }
}

pub fn del_(record: Value, key: Value) -> Value {
    let key = match key.as_str() {
        Some(raw) => raw.to_string(),
        None => to_s(&key),
    };
    let mut out = match record {
        Value::Object(items) => items,
        _ => panic!("del_ expects object"),
    };
    out.remove(&key);
    Value::Object(out)
}

pub fn index(obj: Value, index: Value) -> Value {
    let idx_raw = as_i64(&index);
    if idx_raw < 0 {
        panic!("index out of bounds: {idx_raw}");
    }
    let idx = idx_raw as usize;
    match obj {
        Value::Array(items) => items
            .get(idx)
            .cloned()
            .unwrap_or_else(|| panic!("index out of bounds: {idx_raw}")),
        Value::String(s) => s
            .chars()
            .nth(idx)
            .map(|c| Value::String(c.to_string()))
            .unwrap_or_else(|| panic!("index out of bounds: {idx_raw}")),
        _ => panic!("index expects array or string"),
    }
}

pub fn slice(obj: Value, start: Value, end: Value) -> Value {
    let start_idx = if start.is_null() { None } else { Some(as_i64(&start) as usize) };
    let end_idx = if end.is_null() { None } else { Some(as_i64(&end) as usize) };
    match obj {
        Value::Array(items) => {
            let lo = start_idx.unwrap_or(0);
            let hi = end_idx.unwrap_or(items.len());
            Value::Array(items[lo.min(items.len())..hi.min(items.len())].to_vec())
        }
        Value::String(text) => {
            let chars: Vec<_> = text.chars().collect();
            let lo = start_idx.unwrap_or(0).min(chars.len());
            let hi = end_idx.unwrap_or(chars.len()).min(chars.len());
            Value::String(chars[lo..hi].iter().collect())
        }
        _ => panic!("slice expects array or string"),
    }
}

pub fn patch(record: Value, updates: Value) -> Value {
    if is_diamond_object(&record) {
        let mut obj = match record {
            Value::Object(m) => m,
            _ => panic!("patch expects object"),
        };
        let fields = obj
            .get_mut("__dm_fields")
            .and_then(Value::as_object_mut)
            .unwrap_or_else(|| panic!("expected DiamondObject"));
        let additions = match updates {
            Value::Object(updates) => updates,
            _ => panic!("patch updates must be object"),
        };
        for (k, v) in additions {
            if !fields.contains_key(&k) {
                panic!("unknown field: {k}");
            }
            fields.insert(k, v);
        }
        return Value::Object(obj);
    }
    let mut out = match record {
        Value::Object(map) => map,
        _ => panic!("patch expects object"),
    };
    let additions = match updates {
        Value::Object(updates) => updates,
        _ => panic!("patch updates must be object"),
    };
    for (k, v) in additions {
        out.insert(k, v);
    }
    Value::Object(out)
}

pub fn map_bind(base: Value, mapper: impl Fn(Value) -> Value) -> Value {
    let input = match base {
        Value::Array(items) => items,
        _ => panic!("map_bind expects array"),
    };
    Value::Array(input.into_iter().map(mapper).collect())
}

pub fn range_inclusive(start: Value, end: Value) -> Value {
    let mut out = Vec::new();
    let mut i = as_i64(&start);
    let end = as_i64(&end);
    while i <= end {
        out.push(json!(i));
        i += 1;
    }
    Value::Array(out)
}

pub fn left_half(seq: Value) -> Value {
    let input = match seq {
        Value::Array(items) => items,
        _ => panic!("left_half expects array"),
    };
    let mid = input.len() / 2;
    Value::Array(input[..mid].to_vec())
}

pub fn right_half(seq: Value) -> Value {
    let input = match seq {
        Value::Array(items) => items,
        _ => panic!("right_half expects array"),
    };
    let mid = input.len() / 2;
    Value::Array(input[mid..].to_vec())
}

pub fn fold(items: Value, init: Value, step: impl Fn(Value, Value) -> Value) -> Value {
    let input = match items {
        Value::Array(items) => items,
        _ => panic!("fold expects array"),
    };
    let mut acc = init;
    for item in input {
        acc = step(acc, item);
    }
    acc
}

pub fn propagate(thunk: impl FnOnce() -> Value) -> Value {
    thunk()
}

pub fn try_catch(body: impl FnOnce() -> Value, handler: impl FnOnce(Value) -> Value) -> Value {
    match panic::catch_unwind(AssertUnwindSafe(body)) {
        Ok(v) => v,
        Err(exc) => {
            let err = panic_to_value(exc);
            if is_reraise(&err) {
                panic!("{}", RERAISE);
            }
            let out = handler(err);
            if is_reraise(&out) {
                panic!("{}", RERAISE);
            }
            out
        }
    }
}

pub fn call_with(fn_ref: Value, fargs: Option<Value>, fkwargs: Option<Value>) -> Value {
    let _kwargs = fkwargs;
    let _args = fargs.unwrap_or_else(|| json!([]));
    if let Some(func_name) = fn_ref.as_str() {
        panic!("call_with by name is not supported in Rust backend: {func_name}");
    }
    panic!("call_with with non-string function reference is not supported in Rust backend");
}

pub fn extern_call(symbol: &str, args: Option<Value>) -> Value {
    let payload = args.unwrap_or_else(|| json!([]));
    panic!("external contract stub invoked: {symbol} args={payload:?}");
}

pub fn sleep(seconds: f64) {
    if !seconds.is_finite() || seconds < 0.0 {
        return;
    }
    thread::sleep(Duration::from_millis((seconds * 1000.0) as u64));
}

pub fn rand_uniform(low: f64, high: f64) -> f64 {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() % 1000)
        .unwrap_or(0);
    let frac = (secs as f64) / 1000.0;
    low + (high - low) * frac
}

pub fn is_tuple(value: &Value) -> bool {
    matches!(value, Value::Array(_))
}

pub fn log_retry_warning(_logger: &Value, err: &Value, delay: f64) {
    let _ = writeln!(io::stdout(), "retry warning: {err:?}, retrying in {delay} seconds");
}

pub fn make_retry_decorator(
    retry_call_fn: &Value,
    _exceptions: &Value,
    _tries: Value,
    _delay: Value,
    _max_delay: Value,
    _backoff: Value,
    _jitter: Value,
    _logger: Value,
) -> Value {
    json!({ "retry_decorator_of": retry_call_fn })
}

pub fn ini_repr(value: &Value) -> Value {
    json!(format!("{value:?}"))
}

pub fn ini_pair(a: &str, b: Option<&str>) -> Value {
    json!([a, b])
}

pub fn ini_splitlines_keepends(data: &str) -> Value {
    let lines: Vec<Value> = data
        .split_inclusive('\n')
        .map(|s| Value::String(s.to_string()))
        .collect();
    Value::Array(lines)
}

pub fn iscommentline(line: &str) -> bool {
    matches!(line.trim_start().chars().next(), Some('#') | Some(';'))
}

pub fn ini_iscommentline(line: &str) -> Value {
    json!(iscommentline(line))
}

pub fn ini_parseline(path: &str, line: &str, lineno: i64, strip_inline_comments: bool, strip_section_whitespace: bool) -> Value {
    let mut raw = line.to_string();
    if iscommentline(&raw) {
        raw.clear();
    } else {
        raw = raw.trim_end().to_string();
    }
    if raw.is_empty() {
        return json!([Value::Null, Value::Null]);
    }
    if raw.starts_with('[') {
        let mut line_copy = raw.clone();
        for c in ['#', ';'] {
            if let Some(i) = line_copy.find(c) {
                line_copy = line_copy[..i].to_string();
            }
        }
        if line_copy.ends_with(']') {
            let section = &line_copy[1..line_copy.len() - 1];
            let section = if strip_section_whitespace {
                section.trim()
            } else {
                section
            };
            return json!([json!(section), Value::Null]);
        }
        return json!([Value::Null, line_copy]);
    }

    if !raw.as_bytes().first().is_some_and(|b| b.is_ascii_whitespace()) {
        let mut name = None;
        let mut value = None;
        if let Some(pos) = raw.find('=') {
            name = Some(raw[..pos].to_string());
            value = Some(raw[pos + 1..].to_string());
        } else if let Some(pos) = raw.find(':') {
            name = Some(raw[..pos].to_string());
            value = Some(raw[pos + 1..].to_string());
        } else {
            panic!("{}", IniParseError {
                path: path.to_string(),
                lineno,
                msg: format!("unexpected line: {raw:?}"),
            });
        }
        let mut key = name.unwrap_or_default().trim().to_string();
        let mut v = value.unwrap_or_default().trim().to_string();
        if strip_inline_comments {
            for c in ["#", ";"] {
                if let Some(i) = v.find(c) {
                    v = v[..i].to_string();
                }
            }
            v = v.trim_end().to_string();
        }
        if key.is_empty() {
            panic!("{}", IniParseError {
                path: path.to_string(),
                lineno,
                msg: "empty key".to_string(),
            });
        }
        return json!([json!(key), json!(v)]);
    }

    let mut out = raw.trim().to_string();
    if strip_inline_comments {
        for c in ["#", ";"] {
            if let Some(i) = out.find(c) {
                out = out[..i].to_string();
            }
        }
        out = out.trim().to_string();
    }
    json!([Value::Null, Value::String(out)])
}

pub fn ini_parse_lines(
    path: &str,
    line_iter: Vec<&str>,
    strip_inline_comments: bool,
    strip_section_whitespace: bool,
) -> Value {
    let mut out = Vec::new();
    let mut section: Option<String> = None;
    let mut lineno = 0_i64;
    for line in line_iter {
        let parsed = ini_parseline(path, line, lineno, strip_inline_comments, strip_section_whitespace);
        let pair = parsed.as_array().expect("parseline must return pair");
        let raw_key = pair.first().and_then(Value::as_str).map(str::to_string);
        let raw_value = pair.get(1).cloned().unwrap_or(Value::Null);
        match raw_key {
            Some(name) if raw_value.is_null() => {
                if let Some(sec) = &name {
                    section = Some(sec.clone());
                    out.push(json!([json!(lineno), json!(section), Value::Null, Value::Null]));
                }
            }
            Some(name) => out.push(json!([json!(lineno), json!(section), json!(name), raw_value])),
            None => {
                if let Some(last) = out.last_mut() {
                    if section.is_none() {
                        panic!("{}", IniParseError {
                            path: path.to_string(),
                            lineno,
                            msg: "unexpected value continuation".to_string(),
                        });
                    }
                }
                if let Some(last) = out.last_mut() {
                    if let Some(last_name) = last[2].as_str() {
                        if let Some(existing) = last[3].as_str() {
                            last[3] = json!(format!("{existing}\n{raw_value}"));
                        }
                    } else {
                        panic!("{}", IniParseError {
                            path: path.to_string(),
                            lineno,
                            msg: "unexpected value continuation".to_string(),
                        });
                    }
                }
            }
        }
        lineno += 1;
    }
    Value::Array(out)
}

pub fn ini_parse_ini_data(
    path: &str,
    data: &str,
    strip_inline_comments: bool,
    strip_section_whitespace: bool,
) -> Value {
    let tokens = ini_parse_lines(
        path,
        ini_splitlines_keepends(data)
            .as_array()
            .unwrap_or(&Vec::new())
            .iter()
            .map(|v| to_s(v).as_str().to_string())
            .collect::<Vec<_>>()
            .iter()
            .map(String::as_str)
            .collect::<Vec<_>>(),
        strip_inline_comments,
        strip_section_whitespace,
    )
    .as_array()
    .cloned()
    .unwrap_or_default();

    let mut sources = HashMap::new();
    let mut sections: HashMap<String, HashMap<String, String>> = HashMap::new();

    for row in tokens {
        let row_vec = row.as_array().cloned().unwrap_or_default();
        let lineno = row_vec.first().and_then(Value::as_i64).unwrap_or(0);
        let section = row_vec.get(1).and_then(Value::as_str).unwrap_or("");
        let name = row_vec.get(2).and_then(Value::as_str).unwrap_or("");
        let value = row_vec.get(3).and_then(Value::as_str).unwrap_or("");
        if section.is_empty() {
            panic!("{}", IniParseError {
                path: path.to_string(),
                lineno,
                msg: "no section header defined".to_string(),
            });
        }
        sources.insert(format!("{}:{name:?}"), row_vec.first().cloned().unwrap_or(Value::Null));
        if name.is_empty() {
            if sections.contains_key(section) {
                panic!("{}", IniParseError {
                    path: path.to_string(),
                    lineno,
                    msg: format!("duplicate section {section:?}"),
                });
            }
            sections.insert(section.to_string(), HashMap::new());
        } else {
            let sec = sections.entry(section.to_string()).or_default();
            if sec.contains_key(name) {
                panic!("{}", IniParseError {
                    path: path.to_string(),
                    lineno,
                    msg: format!("duplicate name {name:?}"),
                });
            }
            sec.insert(name.to_string(), value.to_string());
        }
    }
    json!([sections, sources])
}

pub fn re_group(text: &str, key: Option<&str>) -> Value {
    if key.is_none() {
        Value::String(text.to_string())
    } else {
        Value::String(key.unwrap_or_default().to_string())
    }
}

pub fn pad6(text: &str) -> Value {
    Value::String(format!("{text:0>6}"))
}

pub fn parse_int_base(text: &str, base: u32) -> Value {
    match i64::from_str_radix(text, base) {
        Ok(v) => json!(v),
        Err(_) => json!(0),
    }
}

pub fn dt_date(year: i64, month: i64, day: i64) -> Value {
    json!(format!("{year:04}-{month:02}-{day:02}"))
}

pub fn dt_datetime(year: i64, month: i64, day: i64, hour: i64, minute: i64, second: i64, micros: i64, _tz: &str) -> Value {
    json!(format!("{year:04}-{month:02}-{day:02}T{hour:02}:{minute:02}:{second:02}.{micros:06}"))
}

pub fn dt_time(hour: i64, minute: i64, second: i64, _micros: i64) -> Value {
    json!(format!("{hour:02}:{minute:02}:{second:02}"))
}

pub fn tz_utc() -> Value {
    json!("UTC")
}

pub fn tz_offset(hours: i64, minutes: i64) -> Value {
    json!(format!("{hours:+}:{minutes:02}"))
}

pub fn to_s(value: &Value) -> String {
    match value {
        Value::String(s) => s.clone(),
        _ => format!("{value}")
    }
}

pub fn to_i(value: &Value) -> i64 {
    as_i64(value)
}

pub fn to_b(value: &Value) -> bool {
    is_truthy(value)
}

pub fn to_o<T>(value: T) -> T {
    value
}

pub fn json_dumps(value: Value) -> Value {
    Value::String(value.to_string())
}

pub fn json_loads(text: Value) -> Value {
    let raw = to_s(&text);
    match serde_json::from_str::<Value>(&raw) {
        Ok(v) => v,
        Err(err) => panic!("json_loads parse error: {err}"),
    }
}

pub fn is_exception(err: &Value, types: &[Value]) -> bool {
    if types.is_empty() {
        return true;
    }
    let text = to_s(err);
    types.iter().any(|ty| to_s(ty) == text || text.contains(&to_s(ty)))
}

pub fn is_reraise(value: &Value) -> bool {
    if let Value::String(v) = value {
        v == RERAISE
    } else {
        false
    }
}

pub fn reraise() -> Value {
    json!(RERAISE)
}

pub fn panic_to_string(err: Box<dyn std::any::Any + Send>) -> String {
    if let Ok(err) = err.downcast::<String>() {
        return *err;
    }
    if let Ok(err) = err.downcast::<&str>() {
        return err.to_string();
    }
    if let Ok(err) = err.downcast::<Value>() {
        return to_s(&err);
    }
    "panic".to_string()
}

pub fn panic_to_value(err: Box<dyn std::any::Any + Send>) -> Value {
    if let Ok(err) = err.downcast::<String>() {
        return json!(*err);
    }
    if let Ok(err) = err.downcast::<&str>() {
        return json!(err.to_string());
    }
    if let Ok(err) = err.downcast::<Value>() {
        return *err;
    }
    json!("panic")
}
