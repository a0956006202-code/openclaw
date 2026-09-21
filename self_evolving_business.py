"""Bounded market experimentation and sub-brand incubation workflow.

This module creates reviewable artifacts only. Publishing, spending money,
processing customer data, and changing production integrations remain outside
its authority and require an operator-approved downstream workflow.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_OUTPUT = Path("data/ai/self-evolving")
AUDIT_LOG = Path("logs/self-evolving-business.jsonl")
BLOCKED_TEXT = re.compile(r"(?:email|e-mail|電話|phone|token|password|密碼|信用卡|credit.?card)", re.I)


class EvolutionError(ValueError):
    """Raised when an experiment violates an explicit guardrail."""


@dataclass(frozen=True)
class MarketSignal:
    name: str
    source: str
    demand_score: float
    fit_score: float
    evidence_score: float
    risk_score: float
    description: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "MarketSignal":
        required = ("name", "source", "demand_score", "fit_score", "evidence_score", "risk_score")
        missing = [key for key in required if key not in value]
        if missing:
            raise EvolutionError(f"市場訊號缺少欄位：{', '.join(missing)}")
        description = str(value.get("description", ""))
        if BLOCKED_TEXT.search(description):
            raise EvolutionError(f"市場訊號疑似包含個資欄位：{value['name']}")
        scores = [float(value[key]) for key in required[2:]]
        if any(score < 0 or score > 100 for score in scores):
            raise EvolutionError(f"市場訊號分數必須介於 0 到 100：{value['name']}")
        return cls(value["name"], value["source"], *scores, description)

    @property
    def opportunity_score(self) -> float:
        return round(
            self.demand_score * 0.35
            + self.fit_score * 0.25
            + self.evidence_score * 0.25
            + (100 - self.risk_score) * 0.15,
            2,
        )


@dataclass(frozen=True)
class ExperimentPlan:
    experiment_id: str
    candidate: str
    hypothesis: str
    variants: tuple[str, str]
    primary_metric: str
    max_sample_size: int
    max_budget: float
    status: str
    human_approval_required: bool
    direct_publishing: bool
    financial_decisions: bool


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _append_audit(event: str, details: dict[str, Any], audit_path: Path = AUDIT_LOG) -> None:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"created_at": _now(), "event": event, **details}
    with audit_path.open("a", encoding="utf-8") as target:
        target.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_signals(path: Path) -> list[MarketSignal]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = payload.get("signals", payload) if isinstance(payload, dict) else payload
    if not isinstance(values, list):
        raise EvolutionError("市場訊號檔必須是陣列或包含 signals 陣列的 JSON")
    return [MarketSignal.from_dict(value) for value in values]


def propose_experiments(
    signals: Iterable[MarketSignal],
    *,
    output_dir: Path = DEFAULT_OUTPUT,
    min_score: float = 65,
    max_sample_size: int = 100,
    max_budget: float = 0,
    audit_path: Path = AUDIT_LOG,
) -> list[Path]:
    if max_sample_size <= 0 or max_sample_size > 1000:
        raise EvolutionError("MVP 樣本數必須介於 1 到 1000")
    if max_budget < 0:
        raise EvolutionError("MVP 預算不可為負數")
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for signal in sorted(signals, key=lambda item: item.opportunity_score, reverse=True):
        if signal.opportunity_score < min_score:
            continue
        experiment_id = _id(f"{signal.name}:{signal.source}")
        plan = ExperimentPlan(
            experiment_id=experiment_id,
            candidate=signal.name,
            hypothesis=f"針對 {signal.name} 的小規模方案能改善 {signal.source} 所反映的需求。",
            variants=("control", "value-proposition-test"),
            primary_metric="qualified_interest_rate",
            max_sample_size=max_sample_size,
            max_budget=max_budget,
            status="draft",
            human_approval_required=True,
            direct_publishing=False,
            financial_decisions=False,
        )
        artifact = {
            "type": "mvp_experiment_plan",
            "created_at": _now(),
            "signal": asdict(signal),
            "opportunity_score": signal.opportunity_score,
            "plan": asdict(plan),
            "data_policy": {
                "personal_data_allowed": False,
                "consent_required": True,
                "synthetic_or_aggregate_metrics_only": True,
            },
        }
        path = output_dir / f"experiment-{experiment_id}.json"
        path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        _append_audit("experiment_proposed", {"experiment_id": experiment_id, "candidate": signal.name}, audit_path)
        paths.append(path)
    return paths


def evaluate_experiment(path: Path, observations: list[dict[str, Any]], *, audit_path: Path = AUDIT_LOG) -> dict[str, Any]:
    artifact = json.loads(path.read_text(encoding="utf-8"))
    plan = artifact["plan"]
    if len(observations) > plan["max_sample_size"]:
        raise EvolutionError("觀測數量超過 MVP 樣本上限")
    totals: dict[str, int] = {variant: 0 for variant in plan["variants"]}
    successes: dict[str, int] = {variant: 0 for variant in plan["variants"]}
    for observation in observations:
        variant = observation.get("variant")
        if variant not in totals or not isinstance(observation.get("success"), bool):
            raise EvolutionError("觀測資料必須包含合法 variant 與布林 success")
        totals[variant] += 1
        successes[variant] += int(observation["success"])
    rates = {variant: (successes[variant] / totals[variant] if totals[variant] else 0) for variant in totals}
    winner = max(rates, key=rates.get) if observations else None
    result = {
        "type": "mvp_experiment_result",
        "experiment_id": plan["experiment_id"],
        "evaluated_at": _now(),
        "totals": totals,
        "successes": successes,
        "rates": rates,
        "winner": winner,
        "promotion_status": "pending_human_review",
    }
    result_path = path.with_name(f"result-{plan['experiment_id']}.json")
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _append_audit("experiment_evaluated", {"experiment_id": plan["experiment_id"], "winner": winner}, audit_path)
    return result


def approve_incubation(
    experiment_path: Path,
    result_path: Path,
    *,
    approver: str,
    output_dir: Path = DEFAULT_OUTPUT,
    audit_path: Path = AUDIT_LOG,
) -> Path:
    if not approver.strip():
        raise EvolutionError("孵化核准必須留下 approver 身份")
    experiment = json.loads(experiment_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("promotion_status") != "pending_human_review":
        raise EvolutionError("此實驗不是待人工審查狀態")
    winner = result.get("winner")
    if not winner or not result.get("rates", {}).get(winner):
        raise EvolutionError("沒有足夠的正向結果可提交孵化")
    experiment_id = experiment["plan"]["experiment_id"]
    launch = {
        "type": "sub_brand_incubation_manifest",
        "created_at": _now(),
        "experiment_id": experiment_id,
        "sub_brand_slug": f"{experiment['plan']['candidate'].lower().replace(' ', '-')}-{experiment_id}",
        "approved_by": approver,
        "approved_variant": winner,
        "next_steps": [
            "human_review_positioning",
            "configure_compliant_payment_provider",
            "configure_delivery_and_support",
            "privacy_and_legal_review",
            "manual_publish_approval",
        ],
        "automatic_actions": [],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"launch-{experiment_id}.json"
    path.write_text(json.dumps(launch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _append_audit("incubation_approved", {"experiment_id": experiment_id, "approver": approver}, audit_path)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="受控的市場實驗與子品牌孵化編排器")
    subparsers = parser.add_subparsers(dest="command", required=True)
    propose = subparsers.add_parser("propose")
    propose.add_argument("signals", type=Path)
    propose.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    propose.add_argument("--min-score", type=float, default=65)
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("experiment", type=Path)
    evaluate.add_argument("observations", type=Path)
    approve = subparsers.add_parser("approve")
    approve.add_argument("experiment", type=Path)
    approve.add_argument("result", type=Path)
    approve.add_argument("--approver", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "propose":
            paths = propose_experiments(load_signals(args.signals), output_dir=args.output_dir, min_score=args.min_score)
            print(json.dumps([str(path) for path in paths], ensure_ascii=False))
        elif args.command == "evaluate":
            observations = json.loads(args.observations.read_text(encoding="utf-8"))
            print(json.dumps(evaluate_experiment(args.experiment, observations), ensure_ascii=False))
        else:
            print(approve_incubation(args.experiment, args.result, approver=args.approver))
    except (EvolutionError, OSError, json.JSONDecodeError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
