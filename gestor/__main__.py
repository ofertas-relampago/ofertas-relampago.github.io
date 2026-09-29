"""Linha de comando do gestor.

    python -m gestor landing              gera docs/config.js a partir do .env
    python -m gestor testar-webhook       envia um clique de teste ao Make
    python -m gestor sync                 baixa os cliques do Make para dados/cliques.csv
    python -m gestor relatorio --dias 7   gera relatório HTML (Make + Meta Ads [+ TikTok Ads])
    python -m gestor grupo --membros 870  projeta quando o grupo atinge o limite
"""
from __future__ import annotations

import argparse
import sys
import webbrowser
from datetime import date, timedelta

from . import analise, landing, make_api, meta_ads, relatorio_html, tiktok_ads
from .config import ARQUIVO_CLIQUES, PASTA_RELATORIOS, Config


def _sair(msg: str) -> None:
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def _periodo(dias: int) -> tuple[date, date]:
    fim = date.today()
    return fim - timedelta(days=dias - 1), fim


def _carregar_cliques(cfg: Config, offline: bool) -> list[analise.Clique]:
    if not offline:
        if cfg.tem_make:
            novos, total = make_api.sincronizar(cfg, ARQUIVO_CLIQUES)
            print(f"Make: {novos} cliques novos ({total} no total)")
        else:
            print("Make API não configurada no .env; usando apenas o CSV local.")
    return analise.carregar_cliques(list(make_api.ler_csv(ARQUIVO_CLIQUES).values()))


def cmd_landing(cfg: Config, _args) -> None:
    if not cfg.grupos_whatsapp:
        _sair("defina GRUPOS_WHATSAPP no .env")
    if any("SEU_CODIGO" in link for link in cfg.grupos_whatsapp):
        _sair("GRUPOS_WHATSAPP ainda tem o link de exemplo; cole o link de convite real do grupo no .env")
    destino = landing.gerar_config_js(cfg)
    print(f"Gerado {destino}")
    print(f"Grupo ativo: [{cfg.grupo_ativo}] {cfg.grupos_whatsapp[min(cfg.grupo_ativo, len(cfg.grupos_whatsapp) - 1)]}")
    for nome, valor in (("Meta Pixel", cfg.meta_pixel_id), ("TikTok Pixel", cfg.tiktok_pixel_id),
                        ("Webhook Make", cfg.make_webhook_url)):
        print(f"  {nome}: {'ok' if valor else 'NÃO configurado'}")


def cmd_testar_webhook(cfg: Config, _args) -> None:
    if not cfg.make_webhook_url:
        _sair("defina MAKE_WEBHOOK_URL no .env")
    print(f"Webhook respondeu HTTP {make_api.enviar_clique_teste(cfg)}")


def cmd_sync(cfg: Config, _args) -> None:
    if not cfg.tem_make:
        _sair("defina MAKE_API_TOKEN e MAKE_DATA_STORE_ID no .env")
    novos, total = make_api.sincronizar(cfg, ARQUIVO_CLIQUES)
    print(f"{novos} cliques novos, {total} no total -> {ARQUIVO_CLIQUES}")


def cmd_grupo(cfg: Config, args) -> None:
    inicio, fim = _periodo(7)
    cliques = analise.no_periodo(_carregar_cliques(cfg, args.offline), inicio, fim)
    p = analise.projetar_limite(args.membros, cfg.limite_grupo, len(cliques) / 7, cfg.taxa_entrada)
    print(f"Membros: {p['membros']}/{p['limite']} ({p['ocupacao']:.0%}) - status: {p['status'].upper()}")
    print(f"Cliques últimos 7 dias: {len(cliques)} -> ~{p['entradas_estimadas_dia']:.1f} entradas/dia "
          f"(taxa de entrada {cfg.taxa_entrada:.0%})")
    if p["dias_ate_lotar"] is None:
        print("Sem cliques no período, não dá para projetar.")
    else:
        print(f"Previsão: lota em ~{p['dias_ate_lotar']} dias ({date.today() + timedelta(days=p['dias_ate_lotar']):%d/%m})")
    if p["status"] != "ok":
        print("-> Crie o próximo grupo, adicione o link em GRUPOS_WHATSAPP, ajuste GRUPO_ATIVO e rode "
              "`python -m gestor landing`.")


def cmd_relatorio(cfg: Config, args) -> None:
    inicio, fim = _periodo(args.dias)
    cliques = analise.no_periodo(_carregar_cliques(cfg, args.offline), inicio, fim)
    avisos: list[str] = []

    campanhas_meta = None
    if cfg.tem_meta and not args.offline:
        try:
            campanhas_meta = analise.juntar_campanhas(meta_ads.insights_campanhas(cfg, inicio, fim), cliques, "meta")
        except Exception as erro:  # relatório sai mesmo se a API falhar
            avisos.append(f"Não foi possível ler o Meta Ads: {erro}")

    campanhas_tiktok = None
    if cfg.tem_tiktok and not args.offline:
        try:
            campanhas_tiktok = analise.juntar_campanhas(
                tiktok_ads.insights_campanhas(cfg, inicio, fim),
                [c for c in cliques if c.meio in ("paid", "cpc", "ads")],
                "tiktok",
            )
        except Exception as erro:
            avisos.append(f"Não foi possível ler o TikTok Ads: {erro}")

    por_origem = analise.contar_por(cliques, "origem")
    projecao = None
    if args.membros is not None:
        projecao = analise.projetar_limite(args.membros, cfg.limite_grupo, len(cliques) / args.dias, cfg.taxa_entrada)
        if projecao["status"] != "ok":
            avisos.append("Grupo perto do limite: prepare o próximo link de grupo.")

    html = relatorio_html.gerar(
        inicio=inicio,
        fim=fim,
        por_origem=por_origem,
        serie=analise.por_dia(cliques, inicio, fim),
        campanhas_meta=campanhas_meta,
        campanhas_tiktok=campanhas_tiktok,
        conteudos_tiktok=analise.contar_por([c for c in cliques if c.origem == "tiktok"], "conteudo"),
        projecao=projecao,
        avisos=avisos,
    )
    PASTA_RELATORIOS.mkdir(exist_ok=True)
    destino = PASTA_RELATORIOS / f"relatorio-{fim:%Y-%m-%d}.html"
    destino.write_text(html, encoding="utf-8")

    print(f"\nPeríodo {inicio:%d/%m} a {fim:%d/%m}: {len(cliques)} cliques no botão")
    for origem, qtd in por_origem.most_common():
        print(f"  {origem:<10} {qtd}")
    for aviso in avisos:
        print(f"AVISO: {aviso}")
    print(f"Relatório: {destino}")
    if args.abrir:
        webbrowser.open(destino.as_uri())


def main() -> None:
    parser = argparse.ArgumentParser(prog="gestor", description="Gestor de tráfego Meta + TikTok -> WhatsApp")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("landing", help="gera docs/config.js a partir do .env").set_defaults(func=cmd_landing)
    sub.add_parser("testar-webhook", help="envia clique de teste ao Make").set_defaults(func=cmd_testar_webhook)
    sub.add_parser("sync", help="baixa cliques do Make").set_defaults(func=cmd_sync)

    p = sub.add_parser("grupo", help="projeção do limite de membros")
    p.add_argument("--membros", type=int, required=True, help="membros atuais do grupo ativo")
    p.add_argument("--offline", action="store_true", help="não consulta o Make, usa só o CSV local")
    p.set_defaults(func=cmd_grupo)

    p = sub.add_parser("relatorio", help="gera relatório HTML")
    p.add_argument("--dias", type=int, default=7)
    p.add_argument("--membros", type=int, help="membros atuais (inclui projeção do limite)")
    p.add_argument("--offline", action="store_true", help="não consulta APIs, usa só o CSV local")
    p.add_argument("--abrir", action="store_true", help="abre o relatório no navegador")
    p.set_defaults(func=cmd_relatorio)

    args = parser.parse_args()
    args.func(Config.carregar(), args)


if __name__ == "__main__":
    main()
