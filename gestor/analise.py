"""Cálculos puros: agregação de cliques, custo por clique no grupo e projeção do limite."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime

ORIGENS_META = ("fb", "facebook", "ig", "instagram", "meta")
ORIGENS_TIKTOK = ("tt", "tiktok")


def normalizar_origem(src: str) -> str:
    s = (src or "").strip().lower()
    if s.startswith(ORIGENS_META):
        return "meta"
    if s.startswith(ORIGENS_TIKTOK):
        return "tiktok"
    return s or "direto"


def normalizar_nome(nome: str) -> str:
    return " ".join((nome or "").lower().split())


@dataclass(frozen=True)
class Clique:
    dia: date
    origem: str
    meio: str
    campanha: str
    conteudo: str
    grupo: int

    @classmethod
    def de_registro(cls, reg: dict) -> "Clique | None":
        try:
            momento = datetime.fromisoformat(reg["ts"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            return None
        return cls(
            dia=momento.astimezone().date(),  # ts vem em UTC; o dia do relatório é o local (BRT)
            origem=normalizar_origem(reg.get("src", "")),
            meio=(reg.get("med") or "").lower(),
            campanha=reg.get("camp", ""),
            conteudo=reg.get("cont", ""),
            grupo=int(reg.get("grp") or 0),
        )


def carregar_cliques(registros: list[dict], ignorar_teste: bool = True) -> list[Clique]:
    cliques = [c for c in map(Clique.de_registro, registros) if c]
    if ignorar_teste:
        cliques = [c for c in cliques if c.origem != "teste"]
    return cliques


def no_periodo(cliques: list[Clique], inicio: date, fim: date) -> list[Clique]:
    return [c for c in cliques if inicio <= c.dia <= fim]


def contar_por(cliques: list[Clique], campo: str) -> Counter:
    return Counter(getattr(c, campo) or "(sem valor)" for c in cliques)


def por_dia(cliques: list[Clique], inicio: date, fim: date) -> list[tuple[date, dict[str, int]]]:
    """Série diária com contagem por origem, incluindo dias sem cliques."""
    contagem: dict[date, Counter] = {}
    for c in cliques:
        contagem.setdefault(c.dia, Counter())[c.origem] += 1
    dias = (fim - inicio).days + 1
    return [
        (d, dict(contagem.get(d, Counter())))
        for d in (date.fromordinal(inicio.toordinal() + i) for i in range(dias))
    ]


def juntar_campanhas(insights: list[dict], cliques: list[Clique], origem: str) -> list[dict]:
    """Cruza métricas da plataforma com cliques no botão (via utm_campaign = nome da campanha)."""
    cliques_camp = Counter(normalizar_nome(c.campanha) for c in cliques if c.origem == origem)
    linhas = []
    for ins in insights:
        chave = normalizar_nome(ins["campanha"])
        entradas = cliques_camp.pop(chave, 0)
        linhas.append(ins | {
            "cliques_grupo": entradas,
            "custo_por_clique_grupo": ins["gasto"] / entradas if entradas else None,
        })
    # Cliques cuja utm_campaign não bateu com nenhuma campanha da plataforma
    for chave, qtd in cliques_camp.items():
        linhas.append({"campanha": chave or "(sem utm_campaign)", "gasto": 0.0, "cliques_grupo": qtd,
                       "custo_por_clique_grupo": None})
    return sorted(linhas, key=lambda linha: linha["gasto"], reverse=True)


def projetar_limite(membros: int, limite: int, cliques_por_dia: float, taxa_entrada: float) -> dict:
    """Estima em quantos dias o grupo atinge o limite de membros."""
    vagas = max(limite - membros, 0)
    entradas_dia = cliques_por_dia * taxa_entrada
    dias = math.ceil(vagas / entradas_dia) if entradas_dia > 0 else None
    ocupacao = membros / limite if limite else 0
    if ocupacao >= 0.95 or (dias is not None and dias <= 3):
        status = "critico"
    elif ocupacao >= 0.85 or (dias is not None and dias <= 10):
        status = "atencao"
    else:
        status = "ok"
    return {
        "membros": membros,
        "limite": limite,
        "vagas": vagas,
        "ocupacao": ocupacao,
        "entradas_estimadas_dia": entradas_dia,
        "dias_ate_lotar": dias,
        "status": status,
    }
