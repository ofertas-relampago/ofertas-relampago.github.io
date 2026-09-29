"""Configuração central, lida do arquivo .env na raiz do projeto."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
PASTA_LANDING = RAIZ / "docs"
PASTA_DADOS = RAIZ / "dados"
PASTA_RELATORIOS = RAIZ / "relatorios"
ARQUIVO_CLIQUES = PASTA_DADOS / "cliques.csv"

load_dotenv(RAIZ / ".env")


def _env(nome: str, padrao: str = "") -> str:
    return os.getenv(nome, padrao).strip()


def _lista(nome: str) -> list[str]:
    return [item.strip() for item in _env(nome).split(",") if item.strip()]


@dataclass(frozen=True)
class Config:
    # Landing page
    grupos_whatsapp: list[str]
    grupo_ativo: int
    meta_pixel_id: str
    tiktok_pixel_id: str
    make_webhook_url: str
    # Make API (leitura do Data Store)
    make_api_token: str
    make_zona: str
    make_data_store_id: str
    # Meta Ads
    meta_access_token: str
    meta_ad_account_id: str
    meta_api_version: str
    # TikTok Ads (opcional; o TikTok nesta fase é orgânico)
    tiktok_access_token: str
    tiktok_advertiser_id: str
    # Grupo
    limite_grupo: int
    taxa_entrada: float

    @classmethod
    def carregar(cls) -> "Config":
        return cls(
            grupos_whatsapp=_lista("GRUPOS_WHATSAPP"),
            grupo_ativo=int(_env("GRUPO_ATIVO", "0")),
            meta_pixel_id=_env("META_PIXEL_ID"),
            tiktok_pixel_id=_env("TIKTOK_PIXEL_ID"),
            make_webhook_url=_env("MAKE_WEBHOOK_URL"),
            make_api_token=_env("MAKE_API_TOKEN"),
            make_zona=_env("MAKE_ZONA", "us2"),
            make_data_store_id=_env("MAKE_DATA_STORE_ID"),
            meta_access_token=_env("META_ACCESS_TOKEN"),
            meta_ad_account_id=_env("META_AD_ACCOUNT_ID").removeprefix("act_"),
            meta_api_version=_env("META_API_VERSION", "v23.0"),
            tiktok_access_token=_env("TIKTOK_ACCESS_TOKEN"),
            tiktok_advertiser_id=_env("TIKTOK_ADVERTISER_ID"),
            limite_grupo=int(_env("LIMITE_GRUPO", "1024")),
            taxa_entrada=float(_env("TAXA_ENTRADA", "0.7")),
        )

    @property
    def tem_make(self) -> bool:
        return bool(self.make_api_token and self.make_data_store_id)

    @property
    def tem_meta(self) -> bool:
        return bool(self.meta_access_token and self.meta_ad_account_id)

    @property
    def tem_tiktok(self) -> bool:
        return bool(self.tiktok_access_token and self.tiktok_advertiser_id)
