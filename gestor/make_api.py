"""Leitura dos cliques gravados no Data Store do Make e cache local em CSV."""
from __future__ import annotations

import csv
from pathlib import Path

import requests

from .config import Config

CAMPOS = ["key", "ts", "src", "med", "camp", "cont", "fbclid", "ttclid", "ref", "grp", "eid"]


def listar_registros(cfg: Config, por_pagina: int = 100) -> list[dict]:
    """Baixa todos os registros do Data Store (paginado)."""
    url = f"https://{cfg.make_zona}.make.com/api/v2/data-stores/{cfg.make_data_store_id}/data"
    headers = {"Authorization": f"Token {cfg.make_api_token}"}
    registros: list[dict] = []
    offset = 0
    while True:
        resp = requests.get(
            url,
            headers=headers,
            params={"pg[limit]": por_pagina, "pg[offset]": offset},
            timeout=30,
        )
        resp.raise_for_status()
        lote = resp.json().get("records", [])
        registros += [{"key": r["key"], **(r.get("data") or {})} for r in lote]
        if len(lote) < por_pagina:
            return registros
        offset += por_pagina


def ler_csv(caminho: Path) -> dict[str, dict]:
    if not caminho.exists():
        return {}
    with caminho.open(encoding="utf-8", newline="") as f:
        return {linha["key"]: linha for linha in csv.DictReader(f)}


def sincronizar(cfg: Config, caminho: Path) -> tuple[int, int]:
    """Mescla os registros do Make no CSV local. Retorna (novos, total)."""
    existentes = ler_csv(caminho)
    novos = 0
    for reg in listar_registros(cfg):
        chave = str(reg.get("key") or reg.get("eid"))
        if chave not in existentes:
            novos += 1
        existentes[chave] = {campo: str(reg.get(campo, "") or "") for campo in CAMPOS} | {"key": chave}

    caminho.parent.mkdir(parents=True, exist_ok=True)
    linhas = sorted(existentes.values(), key=lambda linha: linha.get("ts", ""))
    with caminho.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)
    return novos, len(linhas)


def enviar_clique_teste(cfg: Config) -> int:
    """Envia um clique falso ao webhook para o Make aprender a estrutura dos dados."""
    from datetime import datetime, timezone

    dados = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "src": "teste",
        "med": "teste",
        "camp": "teste",
        "cont": "",
        "fbclid": "",
        "ttclid": "",
        "ref": "",
        "grp": "0",
        "eid": "teste-" + datetime.now().strftime("%Y%m%d%H%M%S"),
    }
    resp = requests.post(cfg.make_webhook_url, data=dados, timeout=30)
    return resp.status_code
