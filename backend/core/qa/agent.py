"""Dr. QA — conversational experimentation agent."""
from __future__ import annotations

import json
import re
from typing import Any

from .experiments import run_aa_test, run_ab_test, run_kpi_gate
from .prompts_data import QA_SYSTEM_PROMPT
from .tools import dispatch_tool, get_registry

_TOOL_PATTERN = re.compile(r"```tool\s*\n(.*?)\n```", re.DOTALL)


class QAAgent:
    """Dr. QA — multi-turn conversational experimentation engineer."""

    def __init__(self) -> None:
        self.history: list[dict] = [{"role": "system", "content": QA_SYSTEM_PROMPT}]
        self.registry = get_registry()

    async def chat(self, user_message: str) -> str:
        from core.llm import chat as llm_chat

        self.history.append({"role": "user", "content": user_message})
        response = await llm_chat(self.history, temperature=0.3, max_tokens=1500)

        tool_calls = _TOOL_PATTERN.findall(response)
        if tool_calls:
            tool_results = []
            for raw in tool_calls:
                try:
                    call = json.loads(raw)
                    result = dispatch_tool(call["tool"], call.get("args", {}))
                    tool_results.append(f"[TOOL RESULT: {call['tool']}]\n{result}")
                except Exception as e:
                    tool_results.append(f"[TOOL ERROR] {e}")

            self.history.append({"role": "assistant", "content": response})
            tool_context = "\n\n".join(tool_results)
            self.history.append({"role": "user", "content": f"Результаты инструментов:\n{tool_context}"})
            response = await llm_chat(self.history, temperature=0.3, max_tokens=1500)

        self.history.append({"role": "assistant", "content": response})
        return response

    def reset(self) -> None:
        self.history = [{"role": "system", "content": QA_SYSTEM_PROMPT}]

    async def run_pipeline(
        self,
        hypothesis_name: str,
        variant_prompt: str = "",
        skip_aa: bool = False,
        canary_pct: int = 5,
        canary_ttl_hours: int = 24,
    ) -> dict:
        h = self.registry.add(hypothesis_name, method="ab")
        result: dict[str, Any] = {"hypothesis_id": h.id, "name": h.name, "steps": {}}

        if not skip_aa:
            print("[Dr.QA] Step 1/4: A/A validation...")
            aa = run_aa_test()
            result["steps"]["aa"] = aa
            if not aa.get("stable", False):
                self.registry.update_status(h.id, "killed", "AA failed: infra unstable")
                result["decision"] = "ABORT"
                result["reason"] = f"A/A нестабилен (drift={aa.get('drift_pp')}pp). Инфраструктура ненадёжна."
                return result

        print("[Dr.QA] Step 2/4: A/B test...")
        ab = run_ab_test(variant_prompt)
        result["steps"]["ab"] = ab
        if "error" in ab:
            self.registry.update_status(h.id, "killed", ab["error"])
            result["decision"] = "ERROR"
            result["reason"] = ab["error"]
            return result

        n = ab.get("n", 0)
        if n < 30:
            needed = ab.get("min_n_needed", 30)
            self.registry.update_status(h.id, "draft", f"n={n}<30")
            result["decision"] = "INSUFFICIENT DATA"
            result["reason"] = f"n={n} кейсов. Нужно минимум {needed}. Добавь eval-сценарии."
            return result

        print("[Dr.QA] Step 3/4: KPI gate...")
        from .config import DATA_DIR

        gate = run_kpi_gate(str(DATA_DIR / "ab_variant.json"))
        result["steps"]["gate"] = gate

        stats = ab.get("stats", {})
        deltas = ab.get("deltas", {})
        decisions = gate.get("decisions", [])
        all_accepted = all(d.get("accept", False) for d in decisions) if decisions else False
        p_value = stats.get("p_value", 1.0)
        significant = stats.get("significant", False)

        if all_accepted and (significant or abs(deltas.get("accuracy_pp", 0)) < 0.5):
            decision = "ACCEPT"
            reason = (
                f"KPI gate passed. accuracy Δ={deltas.get('accuracy_pp')}pp, "
                f"latency Δ={deltas.get('latency_pct')}%, p={p_value}"
            )
        else:
            decision = "REJECT"
            reason = (
                f"KPI gate {'failed' if not all_accepted else 'passed but p={p_value}>0.05'}. "
                f"accuracy Δ={deltas.get('accuracy_pp')}pp"
            )

        if decision == "ACCEPT":
            print(f"[Dr.QA] Step 4/4: Canary {canary_pct}% for {canary_ttl_hours}h...")
            self.registry.set_canary(h.id, canary_pct, canary_ttl_hours)
            result["steps"]["canary"] = {"pct": canary_pct, "ttl_hours": canary_ttl_hours}
        else:
            self.registry.save_result(h.id, ab, decision, reason)

        result["decision"] = decision
        result["reason"] = reason
        result["stats"] = stats
        result["deltas"] = deltas
        return result
