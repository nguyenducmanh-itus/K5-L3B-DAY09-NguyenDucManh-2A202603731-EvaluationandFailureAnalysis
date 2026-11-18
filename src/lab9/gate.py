"""CI gate for evaluation regressions, slices, and report integrity."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item

def _row_keys(report: dict) -> list[tuple[str, int]]:
    return [(str(r.get("item_id")), r.get("seed")) for r in report.get("rows", [])]

def _slice_map(report: dict) -> dict[str, tuple[str, ...]]:
    out = {}
    for row in report.get("rows", []):
        item = str(row.get("item_id"))
        tags = tuple(sorted(row.get("slices") or []))
        if item in out and out[item] != tags:
            out[item] = ("<inconsistent>",)
        else:
            out[item] = tags
    return out

def _ratchet_issues(spec: dict, base_spec: dict) -> list[str]:
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []
    issues = []
    old_metrics = {m["id"]: m for m in base_spec.get("metrics", [])}
    new_metrics = {m["id"]: m for m in spec.get("metrics", [])}
    for mid, old in old_metrics.items():
        new = new_metrics.get(mid)
        if new is None:
            issues.append(f"metric {mid} removed")
            continue
        a, b = old.get("threshold", {}), new.get("threshold", {})
        if "min" in a and ("min" not in b or b["min"] < a["min"]):
            issues.append(f"metric {mid} min threshold loosened")
        if "max" in a and ("max" not in b or b["max"] > a["max"]):
            issues.append(f"metric {mid} max threshold loosened")
        if old.get("blocking") and not new.get("blocking"):
            issues.append(f"metric {mid} no longer blocking")
        if (a.get("no_significant_drop") and not b.get("no_significant_drop")):
            issues.append(f"metric {mid} no_significant_drop removed")
    old_slices = {s["name"]: s for s in base_spec.get("slices", [])}
    new_slices = {s["name"]: s for s in spec.get("slices", [])}
    for name, old in old_slices.items():
        new = new_slices.get(name)
        if new is None:
            issues.append(f"slice {name} removed")
            continue
        if old.get("metric") != new.get("metric"):
            issues.append(f"slice {name} metric changed")
        if "min" in old and ("min" not in new or new["min"] < old["min"]):
            issues.append(f"slice {name} min threshold loosened")
        if "max" in old and ("max" not in new or new["max"] > old["max"]):
            issues.append(f"slice {name} max threshold loosened")
        if old.get("blocking") and not new.get("blocking"):
            issues.append(f"slice {name} no longer blocking")
        if old.get("no_significant_drop") and not new.get("no_significant_drop"):
            issues.append(f"slice {name} no_significant_drop removed")
    return issues

def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """Reject non-finite, incomplete, cherry-picked, relabelled, or loosened evidence."""
    problems = []
    metrics = pr.get("metrics") or {}
    for mid, value in metrics.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(value):
            problems.append(f"metric {mid} is not finite")
    rows = pr.get("rows") or []
    base_rows = base.get("rows") or []
    manifest = pr.get("manifest") or {}
    want = int(manifest.get("items", 0)) * len(manifest.get("seeds", []))
    if len(rows) != want:
        problems.append(f"row count {len(rows)} != manifest items×seeds {want}")
    keys, base_keys = _row_keys(pr), _row_keys(base)
    if len(set(keys)) != len(keys):
        problems.append("duplicate (item_id, seed) rows")
    if len(set(base_keys)) != len(base_keys):
        problems.append("baseline has duplicate (item_id, seed) rows")
    if set(keys) != set(base_keys):
        problems.append("(item_id, seed) set differs from baseline")
    if pr.get("evaluator_failures"):
        problems.append("evaluator_failures is non-empty")
    graded_ids = {m["id"] for m in spec.get("metrics", []) if m.get("grader")}
    for i, row in enumerate(rows):
        for mid in graded_ids:
            if mid in row and row[mid] is None:
                problems.append(f"row {i} has missing graded value {mid}")
    if _slice_map(pr) != _slice_map(base):
        problems.append("item slice tags differ from baseline")
    if base_spec is not None:
        problems.extend(_ratchet_issues(spec, base_spec))
    return problems

def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, metric = entry["name"], entry["metric"]
        a, b = per_item(pr, metric, slice_name=name), per_item(base, metric, slice_name=name)
        keys = sorted(set(a) & set(b))
        value = sum(a[k] for k in keys) / len(keys) if keys else None
        verdict, notes = "ok", []
        if value is None:
            verdict = "missing"
            notes.append("no paired items in slice")
        if value is not None and "min" in entry and value < entry["min"]:
            verdict = "fail"
            notes.append(f"mean {value:.3f} < min {entry['min']}")
        if value is not None and "max" in entry and value > entry["max"]:
            verdict = "fail"
            notes.append(f"mean {value:.3f} > max {entry['max']}")
        if value is not None and entry.get("no_significant_drop"):
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                    n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                    confidence=bs.get("confidence", .95))
            notes.append(f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]")
            if hi < 0:
                verdict = "fail"
        label = "BLOCK" if verdict != "ok" and entry.get("blocking") else ("warn" if verdict != "ok" else "ok")
        if label == "BLOCK":
            blocked.append(f"slice:{name}/{metric}")
        lines.append(f"  slice:{name}/{metric:<16} {value!s:<8} {'; '.join(notes):<48} {label}")
    return blocked, lines

def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid) is not None:
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            if not keys:
                verdict = "missing"
                note = "no paired items"
            else:
                d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                    n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                    confidence=bs.get("confidence", .95))
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<30} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines

def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
