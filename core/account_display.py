from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.datetime_utils import serialize_datetime


def _text(value: Any) -> str:
    return str(value or "").strip()


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _format_value(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _format_reset_at(value: Any) -> str:
    try:
        timestamp = int(value or 0)
    except (TypeError, ValueError):
        timestamp = 0
    if timestamp <= 0:
        return ""
    return datetime.fromtimestamp(timestamp, timezone.utc).astimezone().strftime("%m/%d %H:%M")


def _format_maybe_timestamp(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return _format_reset_at(value)
    text = _text(value)
    if text.isdigit():
        return _format_reset_at(text)
    return text


def _metric(
    key: str,
    label: str,
    value: Any,
    *,
    sub: str = "",
    percent: int | float | None = None,
    tone: str = "muted",
) -> dict[str, Any] | None:
    text = _format_value(value)
    if not text:
        return None
    payload: dict[str, Any] = {
        "key": key,
        "label": label,
        "value": text,
        "tone": tone,
    }
    if sub:
        payload["sub"] = sub
    if percent is not None:
        try:
            payload["percent"] = max(0, min(100, round(float(percent), 2)))
        except (TypeError, ValueError):
            pass
    return payload


def _append_metric(items: list[dict[str, Any]], metric: dict[str, Any] | None) -> None:
    if metric:
        items.append(metric)


def _quota_metric(key: str, label: str, limit: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(limit, dict):
        return None
    window = _safe_dict(limit.get("primary_window"))
    used_percent = window.get("used_percent")
    try:
        remaining_percent = max(0, min(100, 100 - float(used_percent or 0)))
    except (TypeError, ValueError):
        remaining_percent = None
    reset_label = _format_reset_at(window.get("reset_at"))
    sub = f"Resets {reset_label}" if reset_label else ""
    if remaining_percent is None:
        return _metric(key, label, "Available" if limit.get("allowed") else "Limited", sub=sub, tone="good" if limit.get("allowed") else "danger")
    tone = "danger" if bool(limit.get("limit_reached")) or remaining_percent <= 0 else ("warning" if remaining_percent <= 20 else "good")
    return _metric(
        key,
        label,
        f"{remaining_percent:g}% remaining",
        sub=sub,
        percent=remaining_percent,
        tone=tone,
    )


def _build_chatgpt_metrics(overview: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    primary: list[dict[str, Any]] = []
    secondary: list[dict[str, Any]] = []
    usage = _safe_dict(overview.get("chatgpt_usage") or overview.get("wham_usage"))
    if not usage:
        return primary, secondary

    _append_metric(primary, _quota_metric("chatgpt_weekly_limit", "Weekly Limit", _safe_dict(usage.get("rate_limit"))))
    _append_metric(primary, _quota_metric("chatgpt_code_review_weekly_limit", "Code Review Weekly Limit", _safe_dict(usage.get("code_review_rate_limit"))))

    credits = _safe_dict(usage.get("credits"))
    if credits:
        if credits.get("unlimited"):
            _append_metric(secondary, _metric("chatgpt_credits", "Credits", "Unlimited", tone="good"))
        elif credits.get("balance") not in (None, ""):
            _append_metric(secondary, _metric("chatgpt_credits", "Credits", credits.get("balance"), tone="muted"))
        if credits.get("approx_local_messages") not in (None, ""):
            _append_metric(secondary, _metric("chatgpt_local_messages", "Local Messages", credits.get("approx_local_messages"), tone="muted"))
        if credits.get("approx_cloud_messages") not in (None, ""):
            _append_metric(secondary, _metric("chatgpt_cloud_messages", "Cloud Messages", credits.get("approx_cloud_messages"), tone="muted"))
    return primary, secondary


def _build_generic_usage_metrics(overview: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    primary: list[dict[str, Any]] = []
    secondary: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []

    _append_metric(primary, _metric("remaining_credits", "Remaining Credits", overview.get("remaining_credits"), tone="good"))
    _append_metric(primary, _metric("usage_total", "Used Credits", overview.get("usage_total"), tone="muted"))
    _append_metric(secondary, _metric("plan_credits", "Total Credits", overview.get("plan_credits"), tone="muted"))
    _append_metric(secondary, _metric("reset_days", "Reset Countdown", overview.get("days_until_reset"), sub="days", tone="muted"))
    _append_metric(secondary, _metric("next_reset_at", "Next Reset", _format_maybe_timestamp(overview.get("next_reset_at")), tone="muted"))

    usage_models = _safe_list(overview.get("usage_models"))
    if usage_models:
        sections.append(
            {
                "key": "usage_models",
                "title": "Model Usage",
                "items": [
                    {
                        "title": _text(item.get("model")) or "model",
                        "metrics": [
                            metric
                            for metric in [
                                _metric("num_requests", "Requests", item.get("num_requests")),
                                _metric("remaining_requests", "Remaining Requests", item.get("remaining_requests"), tone="good"),
                                _metric("num_tokens", "Token", item.get("num_tokens")),
                                _metric("remaining_tokens", "Remaining Tokens", item.get("remaining_tokens"), tone="good"),
                            ]
                            if metric
                        ],
                    }
                    for item in usage_models
                    if isinstance(item, dict)
                ],
            }
        )

    usage_breakdowns = _safe_list(overview.get("usage_breakdowns"))
    if usage_breakdowns:
        sections.append(
            {
                "key": "usage_breakdowns",
                "title": "Credit Details",
                "items": [
                    {
                        "title": _text(item.get("display_name")) or "usage",
                        "metrics": [
                            metric
                            for metric in [
                                _metric("current_usage", "Used", item.get("current_usage")),
                                _metric("usage_limit", "Limit", item.get("usage_limit")),
                                _metric("remaining_usage", "Remaining", item.get("remaining_usage"), tone="good"),
                                _metric("trial_status", "Trial Status", item.get("trial_status")),
                                _metric("trial_expiry", "Trial Expiry", item.get("trial_expiry")),
                                _metric("trial_remaining_usage", "Trial Remaining", item.get("trial_remaining_usage"), tone="good"),
                            ]
                            if metric
                        ],
                    }
                    for item in usage_breakdowns
                    if isinstance(item, dict)
                ],
            }
        )

    return primary, secondary, sections


def build_account_display_summary(
    *,
    platform: str,
    email: str,
    lifecycle_status: str,
    validity_status: str,
    plan_state: str,
    plan_name: str,
    display_status: str,
    overview: dict[str, Any] | None,
    provider_resources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    overview = _safe_dict(overview)
    checked_at = overview.get("checked_at")
    if isinstance(checked_at, datetime):
        checked_at_value = serialize_datetime(checked_at)
    else:
        checked_at_value = _text(checked_at)

    primary_metrics: list[dict[str, Any]] = []
    secondary_metrics: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []

    effective_plan_name = _text(plan_name or overview.get("plan_name") or overview.get("plan"))
    if effective_plan_name:
        _append_metric(secondary_metrics, _metric("plan_name", "Plan", effective_plan_name, tone="muted"))
    if plan_state and plan_state != "unknown":
        _append_metric(secondary_metrics, _metric("plan_state", "Plan Status", plan_state, tone="muted"))
    if checked_at_value:
        _append_metric(secondary_metrics, _metric("checked_at", "Last Checked", checked_at_value, tone="muted"))

    chatgpt_primary, chatgpt_secondary = _build_chatgpt_metrics(overview)
    primary_metrics.extend(chatgpt_primary)
    secondary_metrics.extend(chatgpt_secondary)

    generic_primary, generic_secondary, generic_sections = _build_generic_usage_metrics(overview)
    primary_metrics.extend(generic_primary)
    secondary_metrics.extend(generic_secondary)
    sections.extend(generic_sections)

    warnings: list[dict[str, Any]] = []
    if validity_status == "invalid" or lifecycle_status == "invalid":
        warnings.append({"key": "invalid", "tone": "danger", "message": "Account is currently detected as invalid"})
    if validity_status == "unknown":
        warnings.append({"key": "unknown_validity", "tone": "warning", "message": "Validity check has not been completed yet"})
    if overview.get("quota_note"):
        warnings.append({"key": "quota_note", "tone": "warning", "message": _text(overview.get("quota_note"))})
    if overview.get("check_error"):
        warnings.append({"key": "check_error", "tone": "danger", "message": _text(overview.get("check_error"))})

    badges = [
        {"label": _text(chip), "tone": "muted"}
        for chip in _safe_list(overview.get("chips"))
        if _text(chip)
    ]
    for resource in provider_resources or []:
        if isinstance(resource, dict) and resource.get("resource_type") == "mailbox" and (resource.get("handle") or resource.get("display_name")):
            badges.append({"label": "Email Verified", "tone": "muted"})
            break

    return {
        "identity": {
            "email": email,
            "remote_email": _text(overview.get("remote_email")),
            "platform": platform,
        },
        "status": {
            "display": display_status,
            "lifecycle": lifecycle_status,
            "validity": validity_status,
            "plan_state": plan_state,
            "plan_name": effective_plan_name,
            "checked_at": checked_at_value,
        },
        "primary_metrics": primary_metrics,
        "secondary_metrics": secondary_metrics,
        "badges": badges,
        "warnings": warnings,
        "sections": sections,
    }
