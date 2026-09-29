"""Gera docs/config.js a partir do .env (fonte única de configuração)."""
from __future__ import annotations

import json
from pathlib import Path

from .config import PASTA_LANDING, Config


def gerar_config_js(cfg: Config, destino: Path = PASTA_LANDING / "config.js") -> Path:
    dados = {
        "gruposWhatsApp": cfg.grupos_whatsapp,
        "grupoAtivo": cfg.grupo_ativo,
        "metaPixelId": cfg.meta_pixel_id,
        "tiktokPixelId": cfg.tiktok_pixel_id,
        "makeWebhookUrl": cfg.make_webhook_url,
        "redirectDelayMs": 350,
    }
    conteudo = (
        "// Gerado por `python -m gestor landing`. Edite o .env, não este arquivo.\n"
        f"window.LP_CONFIG = {json.dumps(dados, indent=2, ensure_ascii=False)};\n"
    )
    destino.write_text(conteudo, encoding="utf-8")
    return destino
