# ⚽ FUT Monitor — monitor de preços do EA FC 26 Ultimate Team

Monitor automático de preços de cartas usando os dados públicos do [fut.gg](https://www.fut.gg),
com alertas no WhatsApp e uma interface web com a carta, stats, PlayStyles e gráfico de
histórico de preços. **Stack 100% gratuita** — só precisa de uma conta no GitHub.

## Como funciona

```
GitHub Actions (a cada 30 min)
  └─ collector/collector.py
       ├─ lê data/players.json (sua watchlist)
       ├─ busca os preços no CDN público do fut.gg (todas as ~27 mil cartas)
       ├─ salva histórico em data/history/<cardId>.json
       ├─ na 1ª vez, extrai metadados da carta (stats, imagem, PlayStyles…)
       ├─ avalia seus alertas e envia WhatsApp via CallMeBot
       └─ commita os dados de volta no repositório

GitHub Pages (grátis)
  └─ index.html — interface que lê os JSONs do repositório
```

---

## Instalação (~10 minutos)

### 1. Crie o repositório no GitHub

1. Acesse <https://github.com/new>
2. Nome sugerido: `fut-monitor`. Deixe **Public** (o GitHub Pages gratuito exige
   repositório público — os dados são só preços de cartas, nada sensível; seu
   token e telefone **não** ficam no repositório).
3. Crie o repositório vazio e envie todos os arquivos desta pasta:
   - **Sem instalar nada:** na página do repo, use *uploading an existing file*
     e arraste TODOS os arquivos/pastas.
   - **IMPORTANTE — arquivo do agendador:** nesta pasta ele está salvo como
     `workflow-monitor.yml` (na raiz). No GitHub ele precisa ficar em
     `.github/workflows/monitor.yml`. Pelo site: *Add file → Create new file*,
     digite o nome `.github/workflows/monitor.yml` e cole o conteúdo de
     `workflow-monitor.yml`. (Se usar git, apenas mova/renomeie o arquivo para
     esse caminho antes do commit.)
   - **Com git:**
     ```bash
     cd "fut monitor"
     git init && git add . && git commit -m "FUT Monitor"
     git branch -M main
     git remote add origin https://github.com/SEU_USUARIO/fut-monitor.git
     git push -u origin main
     ```

### 2. Ative o WhatsApp gratuito (CallMeBot)

1. Adicione o número **+34 644 84 71 89** aos contatos do seu celular.
2. Envie para ele, pelo WhatsApp, a mensagem: `I allow callmebot to send me messages`
3. Em ~2 minutos ele responde com sua **apikey** (ex.: `Your APIKEY is 123456`).

### 3. Configure os segredos no GitHub

No repositório: **Settings → Secrets and variables → Actions → New repository secret**

| Nome | Valor |
|---|---|
| `WHATSAPP_PHONE` | seu número com DDI, ex.: `+5511999999999` |
| `CALLMEBOT_APIKEY` | a apikey que o CallMeBot enviou |

### 4. Ative o site (GitHub Pages)

**Settings → Pages → Build and deployment:**
- Source: `Deploy from a branch`
- Branch: `main` / pasta `/ (root)` → **Save**

Em 1–2 minutos seu site estará em `https://SEU_USUARIO.github.io/fut-monitor/`.
Abra no celular e adicione à tela inicial, se quiser usar como "app".

### 5. Rode a primeira coleta

**Aba Actions** do repositório → aceite habilitar workflows se for pedido →
workflow **FUT Monitor** → **Run workflow**. Depois disso ele roda sozinho a cada
30 minutos.

### 6. Token para adicionar jogadores pela interface

A página usa a API do GitHub para editar sua watchlist. Crie um token:

1. <https://github.com/settings/personal-access-tokens/new> (fine-grained)
2. **Repository access:** *Only select repositories* → escolha `fut-monitor`
3. **Permissions → Repository permissions:**
   - `Contents`: **Read and write**
   - `Actions`: **Read and write**
4. Gere, copie o token (`github_pat_…`), abra seu site, clique em **⚙ Configurar**
   e preencha usuário, repositório, branch (`main`) e o token.

O token fica salvo apenas no seu navegador. Defina uma validade longa (ou sem
expiração) para não precisar refazer.

---

## Usando

- **Adicionar carta:** cole o link do jogador no fut.gg
  (ex.: `https://www.fut.gg/players/190045-johan-cruyff/26-100853341/`) e clique
  em **+ Adicionar**. A coleta é disparada na hora; em 1–2 min os dados aparecem.
- **Alertas:** abra a carta e escolha:
  - *Avisar quando cair abaixo do alvo* — ideal para comprar barato;
  - *Avisar quando subir acima do alvo* — ideal para vender;
  - *Avisar a cada checagem* — recebe o valor atual a cada coleta;
  - *Sem alertas* — só acompanha no site.
  Os alertas de alvo só disparam quando o preço **cruza** o valor (não repetem a
  cada 30 min enquanto o preço continua do outro lado).
- **Gráfico:** o histórico é acumulado a cada coleta (guarda ~4 meses).

## Ajustes

- **Intervalo:** edite o `cron` em `.github/workflows/monitor.yml`
  (`*/30 * * * *` = 30 min; `0 * * * *` = 1 h). O GitHub pode atrasar alguns
  minutos em horários de pico — é normal.
- **Mercado PC:** troque `PLATFORM: ps5` por `PLATFORM: pc` no mesmo arquivo.
- **Rodar no seu PC (opcional):**
  ```bash
  set WHATSAPP_PHONE=+5511999999999
  set CALLMEBOT_APIKEY=123456
  python collector/collector.py
  ```
  (sem dependências — Python 3.9+ puro).

## Notas e limites

- Preços vêm dos arquivos públicos do fut.gg, atualizados pelo site a cada poucos
  minutos. Cartas **extintas** (sem nenhuma à venda) aparecem sem preço.
- O CallMeBot é um serviço gratuito de terceiros para uso pessoal — se algum dia
  ele falhar, dá para trocar por Telegram/ntfy mexendo só em `collector/notify.py`.
- Uso pessoal e moderado dos dados do fut.gg (1 requisição a cada 30 min é leve).
- O GitHub Actions gratuito é mais que suficiente: cada coleta gasta ~20 s.
