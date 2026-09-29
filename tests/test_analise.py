from datetime import date

from gestor import analise


def reg(ts, src, camp="", cont="", med=""):
    return {"ts": ts, "src": src, "camp": camp, "cont": cont, "med": med, "grp": "0"}


def test_normalizar_origem():
    assert analise.normalizar_origem("Instagram") == "meta"
    assert analise.normalizar_origem("fb") == "meta"
    assert analise.normalizar_origem("TikTok") == "tiktok"
    assert analise.normalizar_origem("") == "direto"
    assert analise.normalizar_origem("google") == "google"


def test_carregar_ignora_teste_e_invalidos():
    cliques = analise.carregar_cliques([
        reg("2026-09-20T12:00:00.000Z", "meta"),
        reg("2026-09-20T12:00:00Z", "teste"),
        {"src": "meta"},
        reg("data-ruim", "tiktok"),
    ])
    assert len(cliques) == 1
    assert cliques[0].dia == date(2026, 9, 20)


def test_por_dia_inclui_dias_vazios():
    cliques = analise.carregar_cliques([reg("2026-09-20T10:00:00Z", "meta"), reg("2026-09-22T10:00:00Z", "tt")])
    serie = analise.por_dia(cliques, date(2026, 9, 20), date(2026, 9, 22))
    assert [s[1] for s in serie] == [{"meta": 1}, {}, {"tiktok": 1}]


def test_juntar_campanhas_calcula_custo_e_sobras():
    cliques = analise.carregar_cliques([
        reg("2026-09-20T10:00:00Z", "meta", camp="Ofertas  Julho"),
        reg("2026-09-20T11:00:00Z", "meta", camp="ofertas julho"),
        reg("2026-09-20T12:00:00Z", "meta", camp="campanha-sumida"),
        reg("2026-09-20T12:00:00Z", "tiktok", camp="ofertas julho"),
    ])
    insights = [{"campanha": "Ofertas Julho", "gasto": 10.0}, {"campanha": "Sem cliques", "gasto": 5.0}]
    linhas = {linha["campanha"]: linha for linha in analise.juntar_campanhas(insights, cliques, "meta")}
    assert linhas["Ofertas Julho"]["cliques_grupo"] == 2
    assert linhas["Ofertas Julho"]["custo_por_clique_grupo"] == 5.0
    assert linhas["Sem cliques"]["custo_por_clique_grupo"] is None
    assert linhas["campanha-sumida"]["cliques_grupo"] == 1


def test_projetar_limite():
    p = analise.projetar_limite(membros=900, limite=1024, cliques_por_dia=20, taxa_entrada=0.5)
    assert p["vagas"] == 124
    assert p["dias_ate_lotar"] == 13
    assert p["status"] == "atencao"  # ocupação 88%

    assert analise.projetar_limite(100, 1024, 0, 0.7)["dias_ate_lotar"] is None
    assert analise.projetar_limite(1000, 1024, 10, 0.7)["status"] == "critico"
