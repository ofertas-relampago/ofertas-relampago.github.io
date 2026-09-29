"""Métricas de campanhas do TikTok Ads (Business API v1.3).

Opcional: nesta fase o TikTok é orgânico e os cliques vêm do Make.
Só é usado se TIKTOK_ACCESS_TOKEN e TIKTOK_ADVERTISER_ID estiverem no .env.
"""
from __future__ import annotations

import json
from datetime import date

import requests

from .config import Config

URL_RELATORIO = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"


def insights_campanhas(cfg: Config, inicio: date, fim: date) -> list[dict]:
    linhas: list[dict] = []
    pagina = 1
    while True:
        resp = requests.get(
            URL_RELATORIO,
            headers={"Access-Token": cfg.tiktok_access_token},
            params={
                "advertiser_id": cfg.tiktok_advertiser_id,
                "report_type": "BASIC",
                "data_level": "AUCTION_CAMPAIGN",
                "dimensions": json.dumps(["campaign_id"]),
                "metrics": json.dumps(["campaign_name", "spend", "impressions", "clicks"]),
                "start_date": inicio.isoformat(),
                "end_date": fim.isoformat(),
                "page": pagina,
                "page_size": 200,
            },
            timeout=30,
        )
        corpo = resp.json()
        if corpo.get("code") != 0:
            raise RuntimeError(f"TikTok API: {corpo.get('message')}")
        dados = corpo.get("data", {})
        for item in dados.get("list", []):
            m = item.get("metrics", {})
            linhas.append({
                "campanha": m.get("campaign_name", ""),
                "gasto": float(m.get("spend", 0)),
                "impressoes": int(float(m.get("impressions", 0))),
                "cliques_link": int(float(m.get("clicks", 0))),
            })
        if pagina >= dados.get("page_info", {}).get("total_page", 1):
            return linhas
        pagina += 1
