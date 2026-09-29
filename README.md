# Gestor de Tráfego — Grupo de Ofertas no WhatsApp

Porta de entrada automatizada para o grupo de ofertas do Mercado Livre:

```
Meta Ads (pago) ─┐                              ┌─> Meta Pixel / TikTok Pixel (evento Lead / Contact)
                 ├─> Landing page (GitHub Pages) ┼─> Webhook Make ─> Data Store (origem do clique)
TikTok (orgânico)┘        botão "Entrar"         └─> Redireciona p/ link do grupo no WhatsApp

Python (local):  Make Data Store + Meta Ads API [+ TikTok Ads API] ─> relatório HTML + projeção do limite do grupo
```

| Pasta | O que é |
|---|---|
| `docs/` | Landing page estática, publicada no GitHub Pages |
| `gestor/` | Pacote Python: gera a config da landing, baixa cliques do Make, lê Meta/TikTok Ads, gera relatório |
| `tests/` | Testes das regras de cálculo (`pytest`) |

Custo: R$ 0 (GitHub Pages + Make free + APIs gratuitas). Domínio próprio é opcional.

---

## 1. Instalação (uma vez)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Preencha o `.env` com o link do grupo (`GRUPOS_WHATSAPP`) e rode:

```powershell
python -m gestor landing
```

Isso gera `docs/config.js`. **Sempre que mudar o `.env`, rode de novo e publique.**

## 2. Make (registro da origem dos cliques)

1. **Data Store**: Make > Data stores > Add. Crie uma estrutura com os campos (todos *Text*):
   `ts, src, med, camp, cont, fbclid, ttclid, ref, grp, eid`
2. **Cenário**: *Webhooks > Custom webhook* → *Data store > Add/replace a record*
   - Key: `{{eid}}` · mapeie cada campo do webhook para o campo de mesmo nome
3. Copie a URL do webhook para `MAKE_WEBHOOK_URL` no `.env`, rode `python -m gestor testar-webhook`
   com o webhook em "Redetermine data structure" para o Make aprender os campos.
4. Ative o cenário (webhooks rodam na hora, mesmo no plano free).
5. Para o Python ler os dados: Make > perfil > **API access** > gerar token (escopo `datastores:read`).
   Preencha `MAKE_API_TOKEN`, `MAKE_ZONA` (prefixo da URL, ex.: `us2`) e `MAKE_DATA_STORE_ID`
   (número na URL do data store).

> **Limite do Make free**: cada clique consome 2 operações (webhook + gravação). Com ~1.000 ops/mês,
> isso dá ~500 cliques/mês. Acompanhe em Make > Organization > Usage. Se estourar, os pixels
> continuam medindo; só o registro no Make para até o mês virar.

## 3. GitHub Pages (hospedagem da landing)

1. Crie um repositório **público** no GitHub (ex.: `ofertas`).
2. Envie os arquivos (Git, GitHub Desktop, ou "Add file > Upload files" no site).
   O `.gitignore` já impede que `.env`, `dados/` e `relatorios/` subam.
3. Settings > Pages > *Deploy from a branch* > `main` / pasta **`/docs`**.
4. A página fica em `https://SEU_USUARIO.github.io/ofertas/`.

## 4. Meta Ads

1. Business Manager > Gerenciador de Eventos > criar **Pixel** → `META_PIXEL_ID` no `.env` → `python -m gestor landing` → publicar.
2. No anúncio, URL de destino: a landing. Em **Parâmetros de URL** cole:
   ```
   utm_source=meta&utm_medium=paid&utm_campaign={{campaign.name}}&utm_content={{ad.name}}
   ```
   O relatório cruza `utm_campaign` com o nome da campanha para calcular o **custo por clique no grupo**.
3. Otimize a campanha para o evento **Lead** (disparado no clique do botão).
4. Para o relatório: Configurações do negócio > Usuários do sistema > gerar token com `ads_read`
   → `META_ACCESS_TOKEN`; ID da conta de anúncios → `META_AD_ACCOUNT_ID`.

## 5. TikTok (orgânico)

Use links com UTM (o navegador do TikTok costuma não informar a origem sozinho):

- Bio: `https://SEU_USUARIO.github.io/ofertas/?utm_source=tiktok&utm_medium=bio&utm_content=bio`
- Por vídeo (comentário fixado / link): `...?utm_source=tiktok&utm_medium=video&utm_content=nome-do-video`

O relatório mostra quantos cliques cada vídeo gerou. `TIKTOK_PIXEL_ID` e as chaves de TikTok Ads
só são necessários se um dia rodar anúncio pago lá.

## 6. Rotina semanal

```powershell
python -m gestor relatorio --dias 7 --membros 870 --abrir
```

- Baixa os cliques novos do Make, lê o Meta Ads e gera `relatorios/relatorio-AAAA-MM-DD.html`
- Com `--membros` (número atual do grupo), projeta em quantos dias ele chega a 1024

Outros comandos:

```powershell
python -m gestor grupo --membros 870    # só a projeção do limite
python -m gestor sync                   # só baixa os cliques
python -m gestor relatorio --offline    # sem chamar APIs, usa o CSV local
```

### Quando o grupo lotar

1. Crie um novo grupo e copie o link de convite.
2. No `.env`: `GRUPOS_WHATSAPP=link1,link2` e `GRUPO_ATIVO=1`.
3. `python -m gestor landing` e publique o `docs/config.js`. Nenhum anúncio precisa ser alterado.

## Segurança

- O que está em `docs/config.js` é público por natureza (IDs de pixel, link do grupo, URL do webhook).
- Tokens (Make API, Meta, TikTok) ficam só no `.env`, que não vai para o GitHub.
- A URL do webhook é visível; se alguém abusar dela, gere uma nova no Make e rode `landing` de novo.

## Próximos passos (fase 2)

- **Conversions API do Meta** (servidor): melhora a atribuição quando o pixel é bloqueado.
- Agendar o relatório (Agendador de Tarefas do Windows ou GitHub Actions num repositório privado).
- Migrar para Comunidade do WhatsApp se passar de vários grupos.
