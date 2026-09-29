"""Relatório HTML autocontido (abre direto no navegador, sem internet)."""
from __future__ import annotations

from collections import Counter
from datetime import date
from html import escape

CORES = {"meta": "#2f6fde", "tiktok": "#d9366f", "direto": "#8a948f"}
COR_OUTROS = "#c29b2e"


def _brl(valor: float | None) -> str:
    if valor is None:
        return "–"
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _int(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def _cor(origem: str) -> str:
    return CORES.get(origem, COR_OUTROS)


def _tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    if not linhas:
        return '<p class="vazio">Sem dados no período.</p>'
    th = "".join(f"<th>{escape(c)}</th>" for c in cabecalho)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>" for linha in linhas)
    return f'<div class="rolagem"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def _grafico_dias(serie: list[tuple[date, dict[str, int]]]) -> str:
    maximo = max((sum(c.values()) for _, c in serie), default=0) or 1
    barras = []
    for dia, contagem in serie:
        total = sum(contagem.values())
        segmentos = "".join(
            f'<span style="height:{qtd / maximo * 100:.1f}%;background:{_cor(orig)}" '
            f'title="{escape(orig)}: {qtd}"></span>'
            for orig, qtd in sorted(contagem.items())
        )
        barras.append(
            f'<div class="dia"><div class="pilha">{segmentos}</div>'
            f'<b>{total}</b><small>{dia:%d/%m}</small></div>'
        )
    return f'<div class="grafico">{"".join(barras)}</div>'


def gerar(
    inicio: date,
    fim: date,
    por_origem: Counter,
    serie: list[tuple[date, dict[str, int]]],
    campanhas_meta: list[dict] | None,
    campanhas_tiktok: list[dict] | None,
    conteudos_tiktok: Counter,
    projecao: dict | None,
    avisos: list[str],
) -> str:
    total = sum(por_origem.values())
    gasto_meta = sum(c["gasto"] for c in campanhas_meta or [])
    cliques_meta = por_origem.get("meta", 0)

    cartoes = [
        ("Cliques no botão", _int(total)),
        ("Vindos do Meta", _int(cliques_meta)),
        ("Vindos do TikTok", _int(por_origem.get("tiktok", 0))),
        ("Gasto Meta", _brl(gasto_meta) if campanhas_meta is not None else "–"),
        ("Custo por clique no grupo (Meta)", _brl(gasto_meta / cliques_meta) if cliques_meta and gasto_meta else "–"),
    ]
    html_cartoes = "".join(f'<div class="cartao"><small>{escape(t)}</small><b>{v}</b></div>' for t, v in cartoes)

    legenda = "".join(
        f'<span><i style="background:{_cor(o)}"></i>{escape(o)} ({q})</span>' for o, q in por_origem.most_common()
    )

    secoes = [f'<section><h2>Cliques por dia</h2><div class="legenda">{legenda}</div>{_grafico_dias(serie)}</section>']

    if campanhas_meta is not None:
        linhas = [[
            escape(c["campanha"]), _brl(c["gasto"]), _int(c.get("impressoes", 0)), _int(c.get("cliques_link", 0)),
            _int(c.get("visualizacoes_lp", 0)), _int(c.get("leads_pixel", 0)), _int(c["cliques_grupo"]),
            _brl(c["custo_por_clique_grupo"]),
        ] for c in campanhas_meta]
        secoes.append("<section><h2>Campanhas Meta Ads</h2>" + _tabela(
            ["Campanha", "Gasto", "Impressões", "Cliques link", "Visualiz. LP", "Leads (pixel)",
             "Cliques no grupo", "Custo/clique grupo"], linhas) + "</section>")

    if campanhas_tiktok is not None:
        linhas = [[
            escape(c["campanha"]), _brl(c["gasto"]), _int(c.get("impressoes", 0)), _int(c.get("cliques_link", 0)),
            _int(c["cliques_grupo"]), _brl(c["custo_por_clique_grupo"]),
        ] for c in campanhas_tiktok]
        secoes.append("<section><h2>Campanhas TikTok Ads</h2>" + _tabela(
            ["Campanha", "Gasto", "Impressões", "Cliques", "Cliques no grupo", "Custo/clique grupo"], linhas)
            + "</section>")

    linhas = [[escape(conteudo), _int(qtd)] for conteudo, qtd in conteudos_tiktok.most_common()]
    secoes.append("<section><h2>TikTok orgânico por vídeo (utm_content)</h2>"
                  + _tabela(["Vídeo / posição", "Cliques no grupo"], linhas) + "</section>")

    if projecao:
        dias = projecao["dias_ate_lotar"]
        secoes.append(
            f'<section><h2>Capacidade do grupo</h2><div class="grupo {projecao["status"]}">'
            f'<b>{projecao["membros"]} / {projecao["limite"]}</b> membros ({projecao["ocupacao"]:.0%}) · '
            f'~{projecao["entradas_estimadas_dia"]:.1f} entradas/dia · '
            f'{"lota em ~" + str(dias) + " dias" if dias is not None else "sem entradas no período"}'
            f'<div class="barra"><span style="width:{min(projecao["ocupacao"], 1) * 100:.0f}%"></span></div>'
            f'</div></section>'
        )

    html_avisos = "".join(f'<p class="aviso">{escape(a)}</p>' for a in avisos)

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Relatório de Tráfego {inicio:%d/%m} a {fim:%d/%m/%Y}</title>
<style>
:root {{ --bg:#f4f6f5; --card:#fff; --text:#1b1f1d; --muted:#5c6661; --line:#e2e6e4; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0f1412; --card:#18201c; --text:#eef2f0; --muted:#a3b0a9; --line:#2a332e; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:24px 16px; background:var(--bg); color:var(--text);
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
main {{ max-width:1000px; margin:0 auto; }}
h1 {{ margin:0 0 4px; font-size:24px; }} h2 {{ font-size:17px; margin:0 0 12px; }}
.periodo {{ color:var(--muted); margin:0 0 20px; }}
.cartoes {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-bottom:20px; }}
.cartao, section {{ background:var(--card); border-radius:14px; padding:16px; }}
.cartao small {{ display:block; color:var(--muted); font-size:13px; }}
.cartao b {{ font-size:24px; font-variant-numeric:tabular-nums; }}
section {{ margin-bottom:16px; }}
.legenda {{ display:flex; flex-wrap:wrap; gap:14px; font-size:13px; color:var(--muted); margin-bottom:10px; }}
.legenda i {{ display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:5px; }}
.grafico {{ display:flex; gap:4px; align-items:flex-end; height:180px; overflow-x:auto; }}
.dia {{ flex:1 0 28px; display:flex; flex-direction:column; align-items:center; height:100%; font-size:11px; }}
.pilha {{ flex:1; width:70%; display:flex; flex-direction:column-reverse; }}
.pilha span {{ display:block; width:100%; }}
.pilha span:last-child {{ border-radius:4px 4px 0 0; }}
.dia small {{ color:var(--muted); }}
.rolagem {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; font-variant-numeric:tabular-nums; }}
th, td {{ padding:8px; border-bottom:1px solid var(--line); text-align:right; white-space:nowrap; }}
th:first-child, td:first-child {{ text-align:left; white-space:normal; }}
th {{ color:var(--muted); font-weight:600; font-size:12px; }}
.vazio {{ color:var(--muted); }}
.aviso {{ background:#fff4d6; color:#6b4a00; padding:10px 14px; border-radius:10px; }}
.grupo .barra {{ height:10px; background:var(--line); border-radius:6px; margin-top:10px; overflow:hidden; }}
.grupo .barra span {{ display:block; height:100%; background:#1faa59; }}
.grupo.atencao .barra span {{ background:#d99a00; }} .grupo.critico .barra span {{ background:#d33; }}
</style></head><body><main>
<h1>Relatório de Tráfego</h1>
<p class="periodo">{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}</p>
{html_avisos}
<div class="cartoes">{html_cartoes}</div>
{"".join(secoes)}
</main></body></html>
"""
