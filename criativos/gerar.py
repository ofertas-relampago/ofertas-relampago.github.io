"""Gera as imagens de divulgação a partir de criativos/logo-mestre.jpg.

    python criativos/gerar.py

Saídas: docs/logo.jpg, docs/og.jpg (prévia de link), criativos/feed-1080x1080.jpg,
criativos/stories-1080x1920.jpg. Regra do programa de afiliados: marca própria em destaque,
Mercado Livre só citado de forma descritiva, nunca a logo dele.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "criativos"
DOCS = RAIZ / "docs"
FONTES = Path("C:/Windows/Fonts")

VERDE, AMARELO, TINTA, BRANCO = (18, 86, 52), (255, 206, 58), (43, 33, 24), (255, 255, 255)


def impact(tam):
    return ImageFont.truetype(str(FONTES / "impact.ttf"), tam)


def segoe(tam):
    return ImageFont.truetype(str(FONTES / "seguibl.ttf"), tam)


def centralizado(d, y, texto, fonte, cor, largura):
    d.text(((largura - d.textlength(texto, font=fonte)) / 2, y), texto, font=fonte, fill=cor)


def botao(d, y, texto, fonte, largura, x=None):
    tw = d.textlength(texto, font=fonte)
    x = (largura - tw) / 2 - 40 if x is None else x
    altura = fonte.size + 44
    d.rounded_rectangle((x, y, x + tw + 80, y + altura), radius=altura // 2, fill=AMARELO)
    d.text((x + 40, y + 14), texto, font=fonte, fill=TINTA)


def gerar():
    logo = Image.open(PASTA / "logo-mestre.jpg").convert("RGB")

    logo.resize((720, round(720 * logo.height / logo.width)), Image.LANCZOS).save(
        DOCS / "logo.jpg", quality=85, optimize=True, progressive=True)

    # Prévia de link (Facebook/WhatsApp): 1200x630
    og = Image.new("RGB", (1200, 630), VERDE)
    w = round(630 * logo.width / logo.height)
    og.paste(logo.resize((w, 630), Image.LANCZOS), (0, 0))
    d = ImageDraw.Draw(og)
    x0 = w + 40
    d.text((x0, 110), "OFERTAS", font=impact(84), fill=AMARELO)
    d.text((x0, 200), "RELÂMPAGO", font=impact(84), fill=AMARELO)
    y = 320
    for linha in ("Achadinhos com", "desconto todo dia", "no seu WhatsApp"):
        d.text((x0, y), linha, font=segoe(32), fill=BRANCO)
        y += 42
    botao(d, 470, "Entre grátis", segoe(30), 1200, x=x0)
    og.save(DOCS / "og.jpg", quality=86, optimize=True)

    # Feed 1080x1080
    c = Image.new("RGB", (1080, 1080), VERDE)
    c.paste(logo.resize((720, 638), Image.LANCZOS), (180, 40))
    d = ImageDraw.Draw(c)
    centralizado(d, 700, "ACHADINHOS COM DESCONTO", impact(72), AMARELO, 1080)
    centralizado(d, 792, "todo dia no seu WhatsApp", segoe(46), BRANCO, 1080)
    botao(d, 900, "Entre grátis no grupo", segoe(46), 1080)
    c.save(PASTA / "feed-1080x1080.jpg", quality=90)

    # Stories/Reels 1080x1920 (texto fora dos ~250px de cima e de baixo)
    c = Image.new("RGB", (1080, 1920), VERDE)
    c.paste(logo.resize((1000, 886), Image.LANCZOS), (40, 300))
    d = ImageDraw.Draw(c)
    centralizado(d, 1230, "ACHADINHOS", impact(116), AMARELO, 1080)
    centralizado(d, 1360, "COM DESCONTO", impact(116), AMARELO, 1080)
    centralizado(d, 1500, "todo dia no seu WhatsApp", segoe(52), BRANCO, 1080)
    botao(d, 1600, "Entre grátis no grupo", segoe(50), 1080)
    c.save(PASTA / "stories-1080x1920.jpg", quality=90)


if __name__ == "__main__":
    gerar()
    print("Imagens geradas em docs/ e criativos/")
