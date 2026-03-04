# Latest Probe Summary (2026-03-03)

## Repos Probed

1. `hukkin/tomli` (`c20c491`, MIT)
- Baseline tests: `16 passed, 744 subtests`
- Friction score: `131`
- Top pressure:
  - exception flow: `60`
  - loops: `17`
  - classes: `5`

2. `pallets/click` (`cdab890`, BSD-3-Clause)
- Baseline tests in current env: `2 failed, 1318 passed, 21 skipped, 1 xfailed`
- Friction score: `1658`
- Top pressure:
  - decorators: `206`
  - exception flow: `194`
  - loops: `101`
  - classes: `78`
  - yield/generator: `56`

3. `theskumar/python-dotenv` (`da0c820`, BSD-3-Clause)
- Baseline tests (raw): `12 failed, 205 passed, 1 skipped` (CLI entrypoint not installed in probe mode)
- Baseline tests (functional fallback `-k 'not cli'`): `176 passed, 1 skipped, 41 deselected`
- Friction score: `256`
- Top pressure:
  - decorators: `34`
  - exception flow: `22`
  - yield/generator: `13`
  - loops: `12`
  - classes: `10`

## Core Evolution Signal

Priority pressure from probes confirms:
1. parser/state-machine primitives,
2. class/decorator model,
3. generator model,
4. CLI/runtime boundary handling in probe infrastructure,
as immediate post-v1 language evolution tracks.

References:
- `src/probing/reports/run_20260303T204447Z_probe_tomli_probe.json`
- `src/probing/reports/run_20260303T204519Z_probe_click_probe.json`
- `src/probing/reports/run_20260303T210236Z_probe_dotenv_probe.json`
- `docs/decisions/profile_v1/CORE_GAP_BACKLOG.md`
- `docs/decisions/profile_v1/D11_STATE_MACHINE_CANDIDATES.md`
