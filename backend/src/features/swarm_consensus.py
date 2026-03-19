"""
StrategyVault — Lightweight Swarm Consensus Adapter
Inspired by Moon Dev's SwarmAgent (moon-dev-ai-agents/src/agents/swarm_agent.py).

Instead of requiring all API keys (Claude, GPT-5, Grok, DeepSeek), this adapter
uses Gemini (already wired) as its primary model and gracefully falls back when
other models aren't configured.

Usage:
    from src.features.swarm_consensus import get_strategy_consensus
    result = get_strategy_consensus(strategy_code, strategy_description)
    confidence = result["confidence"]   # 0.0–1.0
    verdict    = result["verdict"]      # "BUY" | "HOLD" | "REJECT"
    summary    = result["summary"]      # 1-sentence AI summary
"""

import os
import json
import re
import time
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.config import settings


# ── System prompt sent to each AI judge ────────────────────────────────────
JUDGE_SYSTEM_PROMPT = """You are a quantitative trading strategy evaluator.
You will review strategy code and its description, then output a JSON response.
Be critical and realistic. Most strategies will not beat buy-and-hold after costs.

Respond ONLY with valid JSON in this exact format:
{"verdict": "BUY|HOLD|REJECT", "confidence": 0.75, "reason": "one sentence"}

verdict must be one of: BUY, HOLD, REJECT
confidence must be a float between 0.0 and 1.0"""


def _query_gemini(prompt: str) -> Optional[Dict]:
    """Query Gemini with the judge prompt."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"{JUDGE_SYSTEM_PROMPT}\n\n{prompt}",
            generation_config={"temperature": 0.3, "max_output_tokens": 200},
        )
        text = response.text.strip()
        # Extract JSON
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[SwarmConsensus] Gemini error: {e}")
    return None


def _query_openai(prompt: str) -> Optional[Dict]:
    """Query OpenAI GPT if API key is present."""
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        text = resp.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[SwarmConsensus] OpenAI error: {e}")
    return None


def _query_anthropic(prompt: str) -> Optional[Dict]:
    """Query Anthropic Claude if API key is present."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        msg = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            system=JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[SwarmConsensus] Anthropic error: {e}")
    return None


# Model registry — add more providers here
_JUDGES = {
    "gemini":    _query_gemini,
    "openai":    _query_openai,
    "anthropic": _query_anthropic,
}


def get_strategy_consensus(
    strategy_code: str,
    strategy_description: str,
    timeout: int = 20,
) -> Dict[str, Any]:
    """
    Query multiple AI judges in parallel (Moon Dev Swarm pattern).
    Returns aggregated verdict + confidence.

    Args:
        strategy_code: The strategy Python source
        strategy_description: Short description of the strategy idea
        timeout: Seconds to wait for each model

    Returns:
        {
            "verdict": "BUY"|"HOLD"|"REJECT",
            "confidence": float,
            "summary": str,
            "individual_verdicts": dict,
            "num_judges": int,
        }
    """
    prompt = f"""Strategy Description: {strategy_description}

Strategy Code:
```python
{strategy_code[:2000]}
```

Evaluate this trading strategy. Is it sound? Does it have edge? Output JSON only."""

    results = {}

    # Query all available judges in parallel
    with ThreadPoolExecutor(max_workers=len(_JUDGES)) as ex:
        futures = {ex.submit(fn, prompt): name for name, fn in _JUDGES.items()}
        for future in as_completed(futures, timeout=timeout + 5):
            name = futures[future]
            try:
                result = future.result(timeout=3)
                if result and isinstance(result, dict):
                    results[name] = result
            except Exception:
                pass

    if not results:
        # Fallback — no API available
        return {
            "verdict": "HOLD",
            "confidence": 0.5,
            "summary": "No AI consensus available — defaulting to HOLD.",
            "individual_verdicts": {},
            "num_judges": 0,
        }

    # Aggregate
    weighted = {"BUY": 0.0, "HOLD": 0.0, "REJECT": 0.0}
    for r in results.values():
        v = r.get("verdict", "HOLD").upper()
        c = float(r.get("confidence", 0.5))
        if v in weighted:
            weighted[v] += c

    final_verdict = max(weighted, key=weighted.get)
    avg_confidence = sum(
        float(r.get("confidence", 0.5)) for r in results.values()
    ) / len(results)

    # Build summary from individual reasons
    reasons = [r.get("reason", "") for r in results.values() if r.get("reason")]
    summary = " | ".join(reasons[:2]) if reasons else f"Consensus: {final_verdict}"

    return {
        "verdict": final_verdict,
        "confidence": round(avg_confidence, 3),
        "summary": summary,
        "individual_verdicts": {
            k: {"verdict": v.get("verdict"), "confidence": v.get("confidence")}
            for k, v in results.items()
        },
        "num_judges": len(results),
    }
