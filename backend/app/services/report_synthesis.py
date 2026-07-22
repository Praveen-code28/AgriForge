"""Deterministic report assembly + single-call LLM synthesis for AgriForge.

Design goals (hackathon / low-budget):
- The deterministic systems (DL model, weather pipeline, treatment knowledge)
  are the source of truth. The LLM is used ONLY to phrase results in
  farmer-friendly language.
- At most ONE LLM call per analysis, with a hard timeout.
- If the LLM is missing, slow, or fails, a useful deterministic report is
  returned instead (never "Risk: UNKNOWN" when data is available).
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Optional

from backend.app.core.config import get_settings
from backend.app.schemas.ai_report import (
    AIReport,
    AIReportDisease,
    AIReportRisk,
    AIReportSource,
    AIReportTreatment,
    AIReportWeather,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Deterministic extraction helpers
# ---------------------------------------------------------------------------
def _primary(disease_result: dict[str, Any]) -> dict[str, Any]:
    return disease_result.get("primary", {}) or {}


def _is_healthy(disease: str) -> bool:
    return str(disease).lower() in ("healthy", "unknown", "")


def _weather_risk_score(weather_result: Any) -> Optional[int]:
    if not isinstance(weather_result, dict) or weather_result.get("skipped"):
        return None
    analysis = weather_result.get("weather_analysis")
    if isinstance(analysis, dict) and isinstance(analysis.get("risk_score"), (int, float)):
        return int(analysis["risk_score"])
    return None


def compute_risk(
    disease: str,
    treatment_found: bool,
    weather_result: Any,
) -> tuple[str, list[str]]:
    """Compute a deterministic risk level and reasons.

    Returns one of LOW / MODERATE / HIGH / CRITICAL. Never UNKNOWN when a
    disease is present, so the farmer always gets an actionable signal.
    """
    if _is_healthy(disease):
        return "LOW", ["No disease detected; crop appears healthy."]

    reasons: list[str] = [f"Active disease detected: {disease.replace('_', ' ')}."]
    score = _weather_risk_score(weather_result)

    if score is None:
        # Disease present but no weather signal available.
        level = "MODERATE"
        reasons.append("Weather data unavailable; treat as moderate risk until confirmed.")
    elif score >= 70:
        level = "HIGH"
        reasons.append(f"Weather strongly favours disease spread (weather risk {score}/100).")
    elif score >= 40:
        level = "MODERATE"
        reasons.append(f"Weather is moderately favourable for disease spread (weather risk {score}/100).")
    else:
        level = "MODERATE"
        reasons.append(f"Weather is currently not favourable for spread (weather risk {score}/100), but disease is present.")

    if not treatment_found:
        reasons.append("No local treatment knowledge found; expert confirmation recommended.")
        if level == "HIGH":
            level = "CRITICAL"

    return level, reasons[:4]


# ---------------------------------------------------------------------------
# Compact context (token optimisation)
# ---------------------------------------------------------------------------
def _compact_weather(weather_result: Any) -> dict[str, Any]:
    if not isinstance(weather_result, dict) or weather_result.get("skipped"):
        return {"available": False}
    current = weather_result.get("current_weather", {}) or {}
    analysis = weather_result.get("weather_analysis", {}) or {}
    spray = weather_result.get("spray_recommendation", {}) or {}
    return {
        "available": True,
        "temperature_c": current.get("temperature"),
        "humidity_pct": current.get("humidity"),
        "condition": current.get("condition"),
        "disease_risk": analysis.get("risk"),
        "disease_risk_reasons": (analysis.get("reasons") or [])[:2],
        "spray_today": spray.get("spray_today"),
        "best_spray_time": spray.get("best_time"),
    }


def _treatment_actions(treatment_result: dict[str, Any]) -> list[str]:
    treatment = treatment_result.get("treatment") or {}
    actions: list[str] = []
    if isinstance(treatment, dict):
        actions.extend(treatment.get("immediate_actions", []) or [])
        actions.extend(treatment.get("cultural_control", []) or [])
    return [str(a) for a in actions][:6]


def _compact_treatment(treatment_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "found": bool(treatment_result.get("found")),
        "disease_name": treatment_result.get("disease_name"),
        "immediate_actions": _treatment_actions(treatment_result),
        "prevention": [str(p) for p in (treatment_result.get("prevention") or [])][:6],
        "farmer_advice": treatment_result.get("farmer_advice") or treatment_result.get("message"),
    }


def build_compact_context(
    disease_result: dict[str, Any],
    weather_result: Any,
    treatment_result: dict[str, Any],
    risk_level: str,
    risk_reasons: list[str],
    research: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    primary = _primary(disease_result)
    context = {
        "crop": primary.get("plant", "Unknown"),
        "disease": primary.get("disease", "Unknown"),
        "weather": _compact_weather(weather_result),
        "treatment": _compact_treatment(treatment_result),
        "risk": {"level": risk_level, "reasons": risk_reasons},
    }
    if research:
        context["research"] = [
            {"title": r.get("title"), "snippet": (r.get("snippet") or "")[:300]}
            for r in research[:3]
        ]
    return context


# ---------------------------------------------------------------------------
# Deterministic report (fallback + base)
# ---------------------------------------------------------------------------
def build_deterministic_report(
    disease_result: dict[str, Any],
    weather_result: Any,
    treatment_result: dict[str, Any],
    research: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    primary = _primary(disease_result)
    crop = primary.get("plant", "Unknown")
    disease = primary.get("disease", "Unknown")
    confidence = float(primary.get("confidence", 0.0) or 0.0)
    healthy = _is_healthy(disease)
    treatment_found = bool(treatment_result.get("found"))

    level, reasons = compute_risk(disease, treatment_found, weather_result)

    cw = _compact_weather(weather_result)
    if cw.get("available"):
        weather_summary = (
            f"{cw.get('condition') or 'Current conditions'}, "
            f"{cw.get('temperature_c')}°C, {cw.get('humidity_pct')}% humidity."
        )
        if healthy:
            weather_impact = "Conditions look manageable; keep monitoring the crop."
        else:
            impact_bits = cw.get("disease_risk_reasons") or []
            weather_impact = (
                f"Disease-favourability is {cw.get('disease_risk') or 'unknown'}. "
                + " ".join(impact_bits)
            ).strip()
    else:
        weather_summary = "Live weather data was not available for this location."
        weather_impact = "Weather impact could not be assessed; rely on field observation."

    immediate = [] if healthy else _treatment_actions(treatment_result)
    if not immediate and not healthy:
        advice = treatment_result.get("farmer_advice") or treatment_result.get("message")
        immediate = [advice] if advice else ["Consult a local agricultural extension officer."]
    prevention = [str(p) for p in (treatment_result.get("prevention") or [])][:6]

    maintenance = prevention[:4] if prevention else [
        "Inspect the crop regularly for new or worsening symptoms.",
        "Follow locally approved agricultural practices.",
    ]

    severity = treatment_result.get("severity_guidance") or {}
    if healthy:
        if_untreated = "No action needed. Continue routine care and monitoring."
    elif isinstance(severity, dict) and severity.get(level.lower()):
        if_untreated = severity[level.lower()]
    elif isinstance(severity, dict) and severity.get("high"):
        if_untreated = severity["high"]
    else:
        if_untreated = (
            "The condition may worsen and reduce yield if left untreated. "
            "Consult a local agricultural extension officer for confirmation."
        )

    if healthy:
        farmer_summary = f"Good news: your {crop} looks healthy. Keep up regular watering, nutrition, and monitoring."
    else:
        farmer_summary = (
            f"AgriForge detected {disease.replace('_', ' ')} in your {crop} "
            f"(risk level: {level}). "
            + (immediate[0] if immediate else "Consult a local agricultural expert.")
        )

    sources = []
    for r in (research or [])[:3]:
        url = r.get("url")
        if url:
            sources.append(
                AIReportSource(
                    organization=r.get("organization_hint") or r.get("domain") or "trusted source",
                    title=r.get("title") or "Reference",
                    url=url,
                    retrieved_at=r.get("retrieved_at") or "",
                )
            )

    report = AIReport(
        crop=crop,
        disease=AIReportDisease(name=disease, confidence=confidence),
        weather=AIReportWeather(summary=weather_summary, impact=weather_impact),
        risk=AIReportRisk(level=level, reasons=reasons),
        treatment=AIReportTreatment(
            immediate_actions=[str(a) for a in immediate],
            preventive_measures=prevention,
        ),
        maintenance=maintenance,
        if_untreated=if_untreated,
        additional_research=[r.get("title", "") for r in (research or [])][:3],
        farmer_summary=farmer_summary,
        sources=sources,
    )
    return report.model_dump()


# ---------------------------------------------------------------------------
# Single-call LLM synthesis
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = (
    "You are an agricultural communicator. You turn already-computed, factual "
    "agronomic data into a concise, farmer-friendly report. "
    "STRICT RULES: Use ONLY the data provided. Never invent diseases, weather "
    "values, pesticide dosages, chemical concentrations, application intervals, "
    "prices, yields, or citations. Do not change the crop, disease, or risk "
    "level. Keep every field short and practical. "
    "Respond with ONLY a JSON object, no markdown, matching exactly these keys: "
    '{"weather_summary": str, "weather_impact": str, "immediate_actions": '
    '[str], "preventive_measures": [str], "maintenance": [str], '
    '"if_untreated": str, "farmer_summary": str}. '
    "immediate_actions and preventive_measures must be drawn strictly from the "
    "provided treatment data."
)


def _extract_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
    elif raw.startswith("```"):
        raw = raw.split("```", 1)[1].split("```", 1)[0].strip()
    if not raw.startswith("{"):
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start : end + 1]
    return json.loads(raw)


def _merge_llm_prose(base_report: dict[str, Any], prose: dict[str, Any]) -> dict[str, Any]:
    """Overlay LLM prose onto the deterministic report.

    Core values (crop, disease, confidence, risk, sources) are NEVER taken from
    the LLM. Lists fall back to deterministic values when the LLM omits them.
    """
    report = dict(base_report)

    if isinstance(prose.get("weather_summary"), str) and prose["weather_summary"].strip():
        report["weather"]["summary"] = prose["weather_summary"].strip()
    if isinstance(prose.get("weather_impact"), str) and prose["weather_impact"].strip():
        report["weather"]["impact"] = prose["weather_impact"].strip()

    for field in ("immediate_actions", "preventive_measures"):
        val = prose.get(field)
        if isinstance(val, list) and val:
            report["treatment"][field] = [str(x) for x in val][:8]

    if isinstance(prose.get("maintenance"), list) and prose["maintenance"]:
        report["maintenance"] = [str(x) for x in prose["maintenance"]][:8]
    if isinstance(prose.get("if_untreated"), str) and prose["if_untreated"].strip():
        report["if_untreated"] = prose["if_untreated"].strip()
    if isinstance(prose.get("farmer_summary"), str) and prose["farmer_summary"].strip():
        report["farmer_summary"] = prose["farmer_summary"].strip()

    return report


async def synthesize_with_llm(
    llm: Any,
    context: dict[str, Any],
    base_report: dict[str, Any],
    timeout: float,
) -> Optional[dict[str, Any]]:
    """Perform a single LLM synthesis call. Returns None on any failure/timeout."""
    if llm is None:
        return None

    user_prompt = (
        "Generate the farmer report JSON from this data:\n"
        + json.dumps(context, ensure_ascii=False)
    )

    def _call() -> str:
        # crewai LLM.call accepts a message list or a string depending on version.
        try:
            return llm.call(
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]
            )
        except TypeError:
            return llm.call(_SYSTEM_PROMPT + "\n\n" + user_prompt)

    try:
        raw = await asyncio.wait_for(asyncio.to_thread(_call), timeout=timeout)
        prose = _extract_json(str(raw))
        merged = _merge_llm_prose(base_report, prose)
        # Validate against schema so we never return a malformed report.
        return AIReport(**merged).model_dump()
    except asyncio.TimeoutError:
        logger.warning("LLM_TIMEOUT after %.1fs; using deterministic report.", timeout)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM synthesis failed (%s); using deterministic report.", _classify_llm_error(exc))
        return None


def _classify_llm_error(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if "401" in text or "authentication" in text or "api key" in text or "unauthorized" in text:
        return "LLM_AUTHENTICATION_FAILED"
    if "403" in text or "forbidden" in text:
        return "LLM_AUTHENTICATION_FAILED"
    if "429" in text or "rate limit" in text:
        return "LLM_RATE_LIMITED"
    if "timeout" in text or "timed out" in text:
        return "LLM_TIMEOUT"
    if "not found" in text or "does not exist" in text or "no such model" in text or "invalid model" in text:
        return "LLM_MODEL_NOT_AVAILABLE"
    return f"LLM_ERROR ({type(exc).__name__})"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
async def generate_report(
    disease_result: dict[str, Any],
    weather_result: Any,
    treatment_result: dict[str, Any],
    llm: Any = None,
    search_fn: Optional[Callable[[str], list[dict[str, Any]]]] = None,
    timeout: Optional[float] = None,
) -> tuple[dict[str, Any], str, dict[str, float]]:
    """Return (ai_report_dict, source, timings).

    source is 'llm' or 'deterministic_fallback'.
    """
    settings = get_settings()
    if timeout is None:
        timeout = float(getattr(settings, "LLM_TIMEOUT_SECONDS", 45))

    timings: dict[str, float] = {}
    primary = _primary(disease_result)
    disease = primary.get("disease", "Unknown")
    crop = primary.get("plant", "Unknown")
    treatment_found = bool(treatment_result.get("found"))

    # Optional trusted research: only when needed (disease present + no local KB).
    research: Optional[list[dict[str, Any]]] = None
    if search_fn is not None and not _is_healthy(disease) and not treatment_found:
        t0 = time.perf_counter()
        try:
            research = await asyncio.wait_for(
                asyncio.to_thread(search_fn, f"{crop} {disease} treatment management"),
                timeout=min(timeout, 15),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Trusted research skipped: %s", exc)
            research = None
        timings["research"] = round(time.perf_counter() - t0, 3)

    base_report = build_deterministic_report(disease_result, weather_result, treatment_result, research)

    level, reasons = compute_risk(disease, treatment_found, weather_result)
    context = build_compact_context(
        disease_result, weather_result, treatment_result, level, reasons, research
    )

    t0 = time.perf_counter()
    llm_report = await synthesize_with_llm(llm, context, base_report, timeout)
    timings["llm"] = round(time.perf_counter() - t0, 3)

    if llm_report is not None:
        return llm_report, "llm", timings
    return base_report, "deterministic_fallback", timings
