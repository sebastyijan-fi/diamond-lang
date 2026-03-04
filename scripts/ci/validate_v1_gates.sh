#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  PYTHON_BIN="python"
fi

usage() {
  cat <<'EOF'
Usage:
  ./scripts/ci/validate_v1_gates.sh [--tokenizer-json PATH] [--skip-behavior]

Environment overrides:
  TOKENIZER_JSON               tokenizer.json path (if --tokenizer-json omitted)
  STDLIB_CONFORMANCE_RUNTIME   runtime module path for stdlib conformance runner
  STDLIB_CONFORMANCE_CASES     stdlib conformance cases dir
  COMPLETENESS_MIN_CLASSIFIED_COVERAGE     minimum classified baseline coverage percentage (default 100)
  COMPLETENESS_MIN_IMPLEMENTATION_COVERAGE minimum implemented coverage percentage (default 0)
  CAP_VALIDATION_STRICT_INPUTS comma-separated core .dmd paths/dirs (warnings capped)
  CAP_VALIDATION_RELAXED_INPUTS comma-separated port .dmd paths/dirs (warnings budgeted)
  CAP_VALIDATION_STRICT_MAX_WARNINGS  default 0
  CAP_VALIDATION_RELAXED_MAX_WARNINGS default 0
  SEM_VALIDATION_INPUTS       comma-separated .dmd paths/dirs for static semantic validation
  SEM_VALIDATION_MAX_WARNINGS default 0
  CANONICAL_SYNTAX_INPUTS     comma-separated .dmd paths/dirs for canonical syntax validation
  DIAMOND_EXPERIMENTAL_SYNTAX default 0 (set 1 to downgrade canonical syntax violations to warnings)
  RUN_ID                       run id for construct-tool bench
  CSV_OUT                      output csv path
  APPEND_JSONL                 optional jsonl log path
  BEHAVIOR_OUT_DIR             transpiled python output dir for behavior run
  PORTFOLIO_NET_MIN            default 0.35
  PORTFOLIO_VS_TOOLS_MIN       default 0.60
  PORTFOLIO_TOOL_OVERHEAD_MAX  default 0.15
  PROGRAM_NET_MIN              default 0.05
  PROGRAM_TOOL_OVERHEAD_MAX    default 0.20
  EVIDENCE_BASELINE_CSVS       optional comma-separated baseline benchmark csvs
  EVIDENCE_CANDIDATE_CSVS      optional comma-separated candidate benchmark csvs
  EVIDENCE_METRIC              default net_reduction
  EVIDENCE_BOOTSTRAP_SAMPLES   default 5000
  EVIDENCE_MIN_MEAN_IMPROVEMENT default 0.005
  EVIDENCE_MIN_CI_LOWER        default 0.0
  EVIDENCE_MIN_PROB_POSITIVE   default 0.90
  EVIDENCE_REPORT_JSON         default /tmp/diamond_syntax_evidence_ci.json
  EVIDENCE_REPORT_MD           default docs/completeness/SYNTAX_EVIDENCE_REPORT.md
EOF
}

TOKENIZER_JSON="${TOKENIZER_JSON:-}"
SKIP_BEHAVIOR=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tokenizer-json)
      TOKENIZER_JSON="${2:-}"
      shift 2
      ;;
    --skip-behavior)
      SKIP_BEHAVIOR=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$TOKENIZER_JSON" ]]; then
  REF_FILE="$HOME/.cache/huggingface/hub/models--Qwen--Qwen3-8B/refs/main"
  if [[ -f "$REF_FILE" ]]; then
    SNAPSHOT="$(cat "$REF_FILE")"
    CANDIDATE="$HOME/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/$SNAPSHOT/tokenizer.json"
    if [[ -f "$CANDIDATE" ]]; then
      TOKENIZER_JSON="$CANDIDATE"
    fi
  fi
fi

if [[ -z "$TOKENIZER_JSON" || ! -f "$TOKENIZER_JSON" ]]; then
  echo "Tokenizer not found. Pass --tokenizer-json or set TOKENIZER_JSON." >&2
  exit 2
fi

PORTFOLIO_NET_MIN="${PORTFOLIO_NET_MIN:-0.35}"
PORTFOLIO_VS_TOOLS_MIN="${PORTFOLIO_VS_TOOLS_MIN:-0.60}"
PORTFOLIO_TOOL_OVERHEAD_MAX="${PORTFOLIO_TOOL_OVERHEAD_MAX:-0.15}"
PROGRAM_NET_MIN="${PROGRAM_NET_MIN:-0.05}"
PROGRAM_TOOL_OVERHEAD_MAX="${PROGRAM_TOOL_OVERHEAD_MAX:-0.20}"
EVIDENCE_BASELINE_CSVS="${EVIDENCE_BASELINE_CSVS:-}"
EVIDENCE_CANDIDATE_CSVS="${EVIDENCE_CANDIDATE_CSVS:-}"
EVIDENCE_METRIC="${EVIDENCE_METRIC:-net_reduction}"
EVIDENCE_BOOTSTRAP_SAMPLES="${EVIDENCE_BOOTSTRAP_SAMPLES:-5000}"
EVIDENCE_MIN_MEAN_IMPROVEMENT="${EVIDENCE_MIN_MEAN_IMPROVEMENT:-0.005}"
EVIDENCE_MIN_CI_LOWER="${EVIDENCE_MIN_CI_LOWER:-0.0}"
EVIDENCE_MIN_PROB_POSITIVE="${EVIDENCE_MIN_PROB_POSITIVE:-0.90}"
EVIDENCE_REPORT_JSON="${EVIDENCE_REPORT_JSON:-/tmp/diamond_syntax_evidence_ci.json}"
EVIDENCE_REPORT_MD="${EVIDENCE_REPORT_MD:-docs/completeness/SYNTAX_EVIDENCE_REPORT.md}"

RUN_ID="${RUN_ID:-run_$(date -u +%Y%m%dT%H%M%SZ)_ci_v1_gates}"
CSV_OUT="${CSV_OUT:-/tmp/diamond_construct_tool_ci_latest.csv}"
BEHAVIOR_OUT_DIR="${BEHAVIOR_OUT_DIR:-/tmp/diamond_python_exec_ci_portfolio14}"
STDLIB_CONFORMANCE_RUNTIME="${STDLIB_CONFORMANCE_RUNTIME:-src/transpiler/runtime/diamond_runtime.py}"
STDLIB_CONFORMANCE_CASES="${STDLIB_CONFORMANCE_CASES:-src/conformance/cases}"
CAP_VALIDATION_STRICT_INPUTS="${CAP_VALIDATION_STRICT_INPUTS:-docs/decisions/profile_v1/programs,research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_full}"
CAP_VALIDATION_RELAXED_INPUTS="${CAP_VALIDATION_RELAXED_INPUTS:-certification/real-repos/retry/diamond,certification/real-repos/iniconfig/diamond,certification/real-repos/tomli/diamond}"
CAP_VALIDATION_STRICT_MAX_WARNINGS="${CAP_VALIDATION_STRICT_MAX_WARNINGS:-0}"
CAP_VALIDATION_RELAXED_MAX_WARNINGS="${CAP_VALIDATION_RELAXED_MAX_WARNINGS:-0}"
SEM_VALIDATION_INPUTS="${SEM_VALIDATION_INPUTS:-research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_full,certification/real-repos/retry/diamond,certification/real-repos/iniconfig/diamond,certification/real-repos/tomli/diamond}"
SEM_VALIDATION_MAX_WARNINGS="${SEM_VALIDATION_MAX_WARNINGS:-0}"
CANONICAL_SYNTAX_INPUTS="${CANONICAL_SYNTAX_INPUTS:-docs/decisions/profile_v1/programs,research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_full}"

if [[ -n "${CAP_VALIDATION_INPUTS:-}" ]]; then
  CAP_VALIDATION_STRICT_INPUTS="$CAP_VALIDATION_INPUTS"
fi

echo "[canonical] Syntax profile validation"
if [[ -n "$CANONICAL_SYNTAX_INPUTS" ]]; then
  IFS=',' read -r -a _CANON_INPUTS <<< "$CANONICAL_SYNTAX_INPUTS"
  CANON_CMD=("$PYTHON_BIN" scripts/canonical/validate_canonical_syntax.py)
  for p in "${_CANON_INPUTS[@]}"; do
    if [[ -n "$p" ]]; then
      CANON_CMD+=(--in "$p")
    fi
  done
  if [[ "${DIAMOND_EXPERIMENTAL_SYNTAX:-0}" == "1" ]]; then
    CANON_CMD+=(--experimental-mode)
  fi
  "${CANON_CMD[@]}"
else
  echo "canonical syntax validation: skipped (no inputs)"
fi

echo "[evolution] Profile v1 policy validation"
"$PYTHON_BIN" scripts/evolution/validate_evolution_policy.py \
  --policy docs/decisions/profile_v1/evolution_policy_v1.json

echo "[evolution] Migration tool regressions"
"$PYTHON_BIN" scripts/evolution/migrate_to_v1_tests.py
"$PYTHON_BIN" scripts/evolution/validate_evolution_policy_tests.py

echo "[interop] Profile v1 validation"
"$PYTHON_BIN" scripts/interop/validate_interop_profile.py \
  --profile docs/decisions/profile_v1/interop_profile_v1.json \
  --repo-root "$ROOT_DIR"

echo "[interop] Validator regressions"
"$PYTHON_BIN" scripts/interop/validate_interop_profile_tests.py

echo "[equality] Contract validation"
"$PYTHON_BIN" scripts/equality/validate_equality_contract.py \
  --contract docs/decisions/profile_v1/equality_identity_hash_v1.json \
  --repo-root "$ROOT_DIR"

echo "[equality] Validator regressions"
"$PYTHON_BIN" scripts/equality/validate_equality_contract_tests.py

echo "[panic] Contract validation"
"$PYTHON_BIN" scripts/panic/validate_panic_cleanup_policy.py \
  --policy docs/decisions/profile_v1/panic_cleanup_profile_v1.json \
  --repo-root "$ROOT_DIR"

echo "[panic] Validator regressions"
"$PYTHON_BIN" scripts/panic/validate_panic_cleanup_policy_tests.py

echo "[concurrency] Contract validation"
"$PYTHON_BIN" scripts/concurrency/validate_concurrency_policy.py \
  --policy docs/decisions/profile_v1/concurrency_profile_v1.json \
  --repo-root "$ROOT_DIR" \
  --in docs/decisions/profile_v1/programs \
  --in research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_full

echo "[concurrency] Validator regressions"
"$PYTHON_BIN" scripts/concurrency/validate_concurrency_policy_tests.py

echo "[scope] Profile v1 exclusions validation"
"$PYTHON_BIN" scripts/scope/validate_scope_policy.py \
  --policy docs/decisions/profile_v1/scope_profile_v1.json \
  --repo-root "$ROOT_DIR" \
  --in docs/decisions/profile_v1/programs \
  --in research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_full

echo "[scope] Validator regressions"
"$PYTHON_BIN" scripts/scope/validate_scope_policy_tests.py

echo "[packaging] Lockfile regressions"
"$PYTHON_BIN" scripts/packaging/diamond_lock_tests.py

LOCK_INPUTS="${LOCK_INPUTS:-docs/decisions/profile_v1/programs}"
LOCK_FILE="${LOCK_FILE:-/tmp/diamond.lock.json}"
IFS=',' read -r -a _LOCK_INPUT_ARR <<< "$LOCK_INPUTS"

LOCK_GEN_CMD=(
  "$PYTHON_BIN" scripts/packaging/diamond_lock.py
  --out "$LOCK_FILE"
  --repo-root "$ROOT_DIR"
)
LOCK_VAL_CMD=(
  "$PYTHON_BIN" scripts/packaging/validate_diamond_lock.py
  --lock "$LOCK_FILE"
  --repo-root "$ROOT_DIR"
)
for p in "${_LOCK_INPUT_ARR[@]}"; do
  if [[ -n "$p" ]]; then
    LOCK_GEN_CMD+=(--in "$p")
    LOCK_VAL_CMD+=(--in "$p")
  fi
done
"${LOCK_GEN_CMD[@]}"
"${LOCK_VAL_CMD[@]}"

echo "[memory] Policy validation"
"$PYTHON_BIN" scripts/memory/validate_memory_runtime_policy.py \
  --policy docs/decisions/profile_v1/memory_runtime_profile_v1.json \
  --repo-root "$ROOT_DIR"

echo "[memory] Validator regressions"
"$PYTHON_BIN" scripts/memory/validate_memory_runtime_policy_tests.py

COMPLETENESS_MIN_CLASSIFIED_COVERAGE="${COMPLETENESS_MIN_CLASSIFIED_COVERAGE:-100}"
COMPLETENESS_MIN_IMPLEMENTATION_COVERAGE="${COMPLETENESS_MIN_IMPLEMENTATION_COVERAGE:-0}"

echo "[completeness] Inventory validation"
"$PYTHON_BIN" scripts/completeness/validate_inventory.py \
  --check-paths \
  --min-classified-coverage "$COMPLETENESS_MIN_CLASSIFIED_COVERAGE" \
  --min-implementation-coverage "$COMPLETENESS_MIN_IMPLEMENTATION_COVERAGE" \
  --report-out docs/completeness/STATUS_REPORT.md

echo "[1/9] Diagnose regressions"
"$PYTHON_BIN" src/transpiler/diagnose_regression_tests.py

echo "[2/9] Parser regressions"
"$PYTHON_BIN" src/transpiler/parser_regression_tests.py

echo "[3/9] Backend object regressions"
"$PYTHON_BIN" src/transpiler/backend_object_regression_tests.py

echo "[4/9] Semantic validation"
"$PYTHON_BIN" src/transpiler/semantic_validation_tests.py

if [[ -n "$SEM_VALIDATION_INPUTS" ]]; then
  IFS=',' read -r -a _SEM_INPUTS <<< "$SEM_VALIDATION_INPUTS"
  SEM_CMD=(
    "$PYTHON_BIN" src/transpiler/semantic_validate.py
    --max-warnings "$SEM_VALIDATION_MAX_WARNINGS"
  )
  for p in "${_SEM_INPUTS[@]}"; do
    if [[ -n "$p" ]]; then
      SEM_CMD+=(--in "$p")
    fi
  done
  "${SEM_CMD[@]}"
else
  echo "semantic validation: skipped (no inputs)"
fi

echo "[5/9] Module-system regressions"
"$PYTHON_BIN" src/transpiler/module_system_regression_tests.py

echo "[6/9] Capability validation"
"$PYTHON_BIN" src/transpiler/capability_validation_tests.py

run_cap_validation_lane() {
  local lane="$1"
  local input_csv="$2"
  local max_warnings="$3"
  if [[ -z "$input_csv" ]]; then
    echo "capability lane '$lane': skipped (no inputs)"
    return 0
  fi

  IFS=',' read -r -a _CAP_INPUTS <<< "$input_csv"
  CAP_CMD=(
    "$PYTHON_BIN" src/transpiler/capability_validate.py
    --max-warnings "$max_warnings"
  )
  for p in "${_CAP_INPUTS[@]}"; do
    if [[ -n "$p" ]]; then
      CAP_CMD+=(--in "$p")
    fi
  done

  echo "capability lane '$lane': max_warnings=$max_warnings"
  "${CAP_CMD[@]}"
}

run_cap_validation_lane "core_strict" "$CAP_VALIDATION_STRICT_INPUTS" "$CAP_VALIDATION_STRICT_MAX_WARNINGS"
run_cap_validation_lane "port_relaxed" "$CAP_VALIDATION_RELAXED_INPUTS" "$CAP_VALIDATION_RELAXED_MAX_WARNINGS"

echo "[7/9] Stdlib conformance"
"$PYTHON_BIN" src/conformance/run_stdlib_conformance.py \
  --runtime "$STDLIB_CONFORMANCE_RUNTIME" \
  --cases-dir "$STDLIB_CONFORMANCE_CASES"

if [[ "$SKIP_BEHAVIOR" -ne 1 ]]; then
  echo "[8/9] Behavior equivalence: portfolio14-v4"
  "$PYTHON_BIN" src/transpiler/run_behavior_tests.py \
    --batch all_portfolio14_v4 \
    --in-dir research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_full \
    --out-dir "$BEHAVIOR_OUT_DIR" \
    --ref-dir research/benchmarks/corpus/reference_python_portfolio14_v4
else
  echo "[8/9] Behavior equivalence: skipped (--skip-behavior)"
fi

echo "[9/9] Construct-tool measurement"
BENCH_CMD=(
  "$PYTHON_BIN" research/benchmarks/tools/construct_tool_bench.py
  --python-dir research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/python
  --python-tools-dir research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/python_with_tools
  --diamond-base-dir research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_base
  --diamond-full-dir research/benchmarks/construct_tool/scenarios/fn_error_portfolio14_v4_math_patch/diamond_full
  --tokenizer-json "$TOKENIZER_JSON"
  --run-id "$RUN_ID"
  --question construct_tool_budget_ci
  --candidate v4_gate_lock_ci
  --out-csv "$CSV_OUT"
)

if [[ -n "${APPEND_JSONL:-}" ]]; then
  BENCH_CMD+=(--append-jsonl "$APPEND_JSONL")
fi

"${BENCH_CMD[@]}"

if [[ -n "$EVIDENCE_BASELINE_CSVS" && -n "$EVIDENCE_CANDIDATE_CSVS" ]]; then
  echo "[9.5/10] Syntax evidence gate"
  IFS=',' read -r -a _EVIDENCE_BASELINE <<< "$EVIDENCE_BASELINE_CSVS"
  IFS=',' read -r -a _EVIDENCE_CANDIDATE <<< "$EVIDENCE_CANDIDATE_CSVS"
  EVIDENCE_CMD=(
    "$PYTHON_BIN" research/benchmarks/tools/syntax_evidence_gate.py
    --metric "$EVIDENCE_METRIC"
    --bootstrap-samples "$EVIDENCE_BOOTSTRAP_SAMPLES"
    --min-mean-improvement "$EVIDENCE_MIN_MEAN_IMPROVEMENT"
    --min-ci-lower "$EVIDENCE_MIN_CI_LOWER"
    --min-prob-positive "$EVIDENCE_MIN_PROB_POSITIVE"
    --out-json "$EVIDENCE_REPORT_JSON"
    --out-md "$EVIDENCE_REPORT_MD"
  )
  for p in "${_EVIDENCE_BASELINE[@]}"; do
    if [[ -n "$p" ]]; then
      EVIDENCE_CMD+=(--baseline-csv "$p")
    fi
  done
  for p in "${_EVIDENCE_CANDIDATE[@]}"; do
    if [[ -n "$p" ]]; then
      EVIDENCE_CMD+=(--candidate-csv "$p")
    fi
  done
  "${EVIDENCE_CMD[@]}"
else
  echo "[9.5/10] Syntax evidence gate: skipped (set EVIDENCE_BASELINE_CSVS and EVIDENCE_CANDIDATE_CSVS)"
fi

echo "[10/10] Gate checks"
"$PYTHON_BIN" - "$CSV_OUT" \
  "$PORTFOLIO_NET_MIN" \
  "$PORTFOLIO_VS_TOOLS_MIN" \
  "$PORTFOLIO_TOOL_OVERHEAD_MAX" \
  "$PROGRAM_NET_MIN" \
  "$PROGRAM_TOOL_OVERHEAD_MAX" <<'PY'
import csv
import sys
from pathlib import Path

csv_path = Path(sys.argv[1])
portfolio_net_min = float(sys.argv[2])
portfolio_vs_tools_min = float(sys.argv[3])
portfolio_tool_overhead_max = float(sys.argv[4])
program_net_min = float(sys.argv[5])
program_tool_overhead_max = float(sys.argv[6])

rows = list(csv.DictReader(csv_path.open()))
if not rows:
    print("FAIL: empty csv")
    sys.exit(1)

total = None
program_rows = []
for row in rows:
    if row["program"] == "TOTAL":
        total = row
    else:
        program_rows.append(row)

if total is None:
    print("FAIL: TOTAL row missing")
    sys.exit(1)

def f(name: str) -> float:
    return float(total[name])

portfolio_failures = []
if f("net_reduction") < portfolio_net_min:
    portfolio_failures.append(
        f"portfolio net_reduction {f('net_reduction'):.6f} < {portfolio_net_min:.6f}"
    )
if f("vs_python_with_tools") < portfolio_vs_tools_min:
    portfolio_failures.append(
        f"portfolio vs_python_with_tools {f('vs_python_with_tools'):.6f} < {portfolio_vs_tools_min:.6f}"
    )
if f("tool_overhead") > portfolio_tool_overhead_max:
    portfolio_failures.append(
        f"portfolio tool_overhead {f('tool_overhead'):.6f} > {portfolio_tool_overhead_max:.6f}"
    )

per_program_net_failures = []
per_program_overhead_failures = []
for row in program_rows:
    net = float(row["net_reduction"])
    ovh = float(row["tool_overhead"])
    if net < program_net_min:
        per_program_net_failures.append((row["program"], net))
    if ovh > program_tool_overhead_max:
        per_program_overhead_failures.append((row["program"], ovh))

print(
    "portfolio:"
    f" net={f('net_reduction'):.4%},"
    f" vs_tools={f('vs_python_with_tools'):.4%},"
    f" overhead={f('tool_overhead'):.4%}"
)
print(
    "thresholds:"
    f" net>={portfolio_net_min:.2%},"
    f" vs_tools>={portfolio_vs_tools_min:.2%},"
    f" overhead<={portfolio_tool_overhead_max:.2%},"
    f" per_program_net>={program_net_min:.2%},"
    f" per_program_overhead<={program_tool_overhead_max:.2%}"
)

failed = False
if portfolio_failures:
    failed = True
    print("FAIL: portfolio gates")
    for item in portfolio_failures:
        print(f"  - {item}")

if per_program_net_failures:
    failed = True
    print("FAIL: per-program net_reduction floor")
    for program, net in per_program_net_failures:
        print(f"  - {program}: {net:.6f}")

if per_program_overhead_failures:
    failed = True
    print("FAIL: per-program tool_overhead cap")
    for program, ovh in per_program_overhead_failures:
        print(f"  - {program}: {ovh:.6f}")

if failed:
    sys.exit(1)

print("PASS: all v1 gate checks")
PY

echo "Validation succeeded."
