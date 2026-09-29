"""Métricas de campanhas do Meta Ads via Graph API (Marketing API)."""
from __future__ import annotations

import json
from datetime import date

import requests

from .config import Config

ACOES_LEAD = ("offsite_conversion.fb_pixel_lead", "lead")


def _acao(acoes: list[dict] | None, tipos: tuple[str, ...]) -> int:
    for acao in acoes or []:
        if acao.get("action_type") in tipos:
            return int(float(acao.get("value", 0)))
    return 0


def insights_campanhas(cfg: Config, inicio: date, fim: date) -> list[dict]:
    """Gasto, impressões, cliques e leads (pixel) por campanha no período."""
    url = f"https://graph.facebook.com/{cfg.meta_api_version}/act_{cfg.meta_ad_account_id}/insights"
    params = {
        "level": "campaign",
        "fields": "campaign_id,campaign_name,spend,impressions,reach,inline_link_clicks,actions",
        "time_range": json.dumps({"since": inicio.isoformat(), "until": fim.isoformat()}),
        "limit": 100,
        "access_token": cfg.meta_access_token,
    }
    linhas: list[dict] = []
    while url:
        resp = requests.get(url, params=params, timeout=30)
        corpo = resp.json()
        if "error" in corpo:
            raise RuntimeError(f"Meta API: {corpo['error'].get('message')}")
        for item in corpo.get("data", []):
            acoes = item.get("actions")
            linhas.append({
                "campanha": item.get("campaign_name", ""),
                "gasto": float(item.get("spend", 0)),
                "impressoes": int(item.get("impressions", 0)),
                "alcance": int(item.get("reach", 0)),
                "cliques_link": int(item.get("inline_link_clicks", 0)),
                "visualizacoes_lp": _acao(acoes, ("landing_page_view",)),
                "leads_pixel": _acao(acoes, ACOES_LEAD),
            })
        url = corpo.get("paging", {}).get("next")
        params = None  # a URL "next" já traz todos os parâmetros
    return linhas
