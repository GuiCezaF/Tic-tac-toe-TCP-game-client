# Build de executáveis (Linux e Windows)

Os binários são gerados com [PyInstaller](https://pyinstaller.org/) a partir de [`main.py`](../main.py) e do arquivo [`tic-tac-toe-client.spec`](../tic-tac-toe-client.spec).

## Pré-requisitos

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) **ou** ambiente virtual com `pip`

## Build local — Linux

No diretório do repositório.

**Com uv:**

```bash
uv sync --extra dev
uv run pyinstaller tic-tac-toe-client.spec
```

**Com Python standalone** (`venv` ativo e `pip install -e ".[dev]"` já executado):

```bash
pyinstaller tic-tac-toe-client.spec
```

O executável fica em `dist/tic-tac-toe-client`. Para distribuir:

```bash
chmod +x dist/tic-tac-toe-client
tar czvf tic-tac-toe-client-linux-x64.tar.gz -C dist tic-tac-toe-client
```

## Build local — Windows

Na pasta do projeto.

**Com uv:**

```powershell
uv sync --extra dev
uv run pyinstaller tic-tac-toe-client.spec
```

**Com Python standalone** (`.venv` ativo, dependências dev instaladas):

```powershell
pyinstaller tic-tac-toe-client.spec
```

O executável fica em `dist\tic-tac-toe-client.exe`. Opcionalmente compacte em ZIP para envio.

> **Nota:** o binário só roda no mesmo sistema operacional em que foi gerado (ELF no Linux, `.exe` no Windows).

## Build automático no GitHub (novo release)

1. Faça commit e push do código (incluindo [`.github/workflows/release-binaries.yml`](../.github/workflows/release-binaries.yml)).
2. No repositório: **Releases** → **Create a new release**.
3. Crie uma tag (ex.: `v0.1.0`) e publique o release (**Publish release**).

O workflow **Release binaries** compila em `ubuntu-latest` e `windows-latest` e anexa ao release:

- `tic-tac-toe-client-linux-x64.tar.gz`
- `tic-tac-toe-client-windows-x64.zip`

Se o workflow falhar, verifique a aba **Actions** e os logs do job.

## Permissões

O `GITHUB_TOKEN` padrão já permite anexar assets ao release deste repositório. Não é obrigatório configurar secret adicional para esse fluxo.
