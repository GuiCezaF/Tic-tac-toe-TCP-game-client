# Cliente Tic-Tac-Toe (Pygame)

Cliente gráfico em [Pygame](https://www.pygame.org/) para jogar **velha** contra outro jogador em rede. Conecta por **TCP** a um servidor que fala **NDJSON** (uma linha JSON por mensagem), pareia jogadores em fila e sincroniza o tabuleiro.

> **Servidor:** este repositório é só o cliente. É necessário um servidor compatível com o protocolo descrito abaixo (por exemplo o projeto *tic-tac-toe-server* correspondente).

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Como executar](#como-executar)
- [Uso da interface](#uso-da-interface)
- [Protocolo de rede (resumo)](#protocolo-de-rede-resumo)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Build de executáveis e CI](#build-de-executáveis-e-ci)
- [Licença](#licença)

---

## Funcionalidades

- Tela inicial com **nome do jogador** e **endereço do servidor** (IP ou hostname).
- Conexão na porta **5001** por padrão (configurável no servidor via `TICTACTOE_PORT`).
- Pareamento automático: aguarda oponente, depois inicia a partida (X começa).
- Tabuleiro 3×3 com cliques; só envia jogada na sua vez.
- Mensagens de fim de partida, incluindo **nome do vencedor** quando o servidor envia `winner_name`.
- **Jogar novamente** (reconecta com o mesmo nome/host) ou **voltar ao menu**.
- Tratamento de erros do servidor, desconexão do oponente e falha de rede.

---

## Requisitos

- **Python** ≥ 3.12 (instalação “standalone”: só o interpretador oficial + `pip`)
- **pygame** ≥ 2.5 (instalado automaticamente pelos comandos abaixo)
- Servidor do jogo acessível na rede (mesma máquina ou outro host)

Pode usar **uma** destas formas de gerir o projeto:

| Abordagem | O que é |
|-----------|---------|
| **[uv](https://docs.astral.sh/uv/)** | Instala dependências e roda comandos num ambiente isolado, sem precisar ativar `venv` manualmente. |
| **Python standalone** | `python` + `venv` + `pip` (fluxo clássico: criar ambiente virtual, ativar, instalar, executar). |

**PyInstaller** (executáveis) é opcional; instruções em [docs/build.md](docs/build.md) com **uv** e **pip**.

---

## Instalação

Clone o repositório e entre na pasta (comum aos dois fluxos):

```bash
git clone <url-do-repositório>
cd tic-ta-toe-client
```

### Opção A — com uv

Cria/atualiza o ambiente e instala dependências conforme `pyproject.toml`:

```bash
uv sync
```

Ambiente de desenvolvimento (inclui PyInstaller):

```bash
uv sync --extra dev
```

### Opção B — Python standalone (`venv` + `pip`)

Use o mesmo `python` ≥ 3.12 em todo o fluxo (`python3` no Linux se for o nome do executável).

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

**Windows (PowerShell ou CMD):**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

Com PyInstaller (grupo opcional `dev`):

```bash
pip install -e ".[dev]"
```

> Com o ambiente virtual **ativado**, `python` e `pip` passam a ser os da `.venv`.

---

## Como executar

O **servidor** do jogo deve estar rodando antes de conectar.

### Com uv

Na raiz do repositório (não é obrigatório ativar `venv`):

```bash
uv run python main.py
```

Equivalentes:

```bash
uv run python -m tic_tac_toe_client
uv run tic-tac-toe-client
```

### Com Python standalone

Ative a `.venv` (se ainda não estiver ativa) e execute na raiz do projeto:

**Linux / macOS:**

```bash
source .venv/bin/activate
python main.py
```

**Windows:**

```powershell
.\.venv\Scripts\activate
python main.py
```

Outras entradas (com o pacote já instalado com `pip install -e .`):

```bash
python -m tic_tac_toe_client
tic-tac-toe-client
```

(`tic-tac-toe-client` só funciona se o `Scripts` / `bin` da `.venv` estiver no `PATH` — o que ocorre após `activate`.)

---

## Uso da interface

1. **Nome:** identificação enviada ao servidor no `join` (aparece como vencedor quando aplicável).
2. **IP ou host:** endereço da máquina onde o servidor escuta (ex.: `127.0.0.1` em testes locais).
3. **Tab** alterna entre os campos; **Enter** ou o botão **Conectar** inicia a conexão.
4. Durante a partida, clique nas células vazias **somente quando for a sua vez**.
5. Ao terminar (vitória, empate ou desconexão), use **Jogar novamente** ou **Voltar ao menu**.

---

## Protocolo de rede (resumo)

| Direção | Mensagens principais |
|--------|----------------------|
| Cliente → servidor | `join` (primeira mensagem), depois `move` com `row` e `col` (0–2) |
| Servidor → cliente | `waiting`, `game_start` (com `role` e `state`), `state`, `error`, `opponent_disconnected` |

- Texto **UTF-8**, **uma linha JSON** terminada em `\n` por mensagem.
- Tabuleiro: `0` vazio, `1` X, `2` O.

Para o contrato completo, consulte a documentação do seu servidor (ex.: `INTEGRACAO_FRONT.md` no repositório do servidor).

---

## Estrutura do projeto

```
tic_tac_toe_client/     # pacote Python instalável
  application/          # loop principal, eventos, integração rede + UI
  models/               # estado local da partida (GameModel)
  network/              # TCP + NDJSON (ServerConnection)
  ui/                   # desenho Pygame (menu, tabuleiro, overlay)
  utils/                # utilitários (ex.: drenagem de fila)
  settings.py           # tamanho da janela e paleta de cores
main.py                 # entrada para scripts e PyInstaller
tic-tac-toe-client.spec # configuração PyInstaller
```

---

## Build de executáveis e CI

Guia completo: **[docs/build.md](docs/build.md)** (Linux, Windows, GitHub Actions).

Resumo **local**:

- **uv:** `uv sync --extra dev` → `uv run pyinstaller tic-tac-toe-client.spec`
- **Python standalone:** `pip install -e ".[dev]"` (com `venv` ativo) → `pyinstaller tic-tac-toe-client.spec`

O binário sai em `dist/` (`tic-tac-toe-client` no Linux, `tic-tac-toe-client.exe` no Windows).

**GitHub:** ao **publicar** um Release, o workflow anexa `.tar.gz` (Linux) e `.zip` (Windows) aos assets.

---

## Licença

Este projeto está licenciado sob a **Licença MIT**. Veja o arquivo [LICENSE](LICENSE).
