# Gerar e publicar o instalador do Grafla

O arquivo para instalar o app é `Grafla-2.1.0-Windows-x64-Setup.exe`.
Ele instala o Grafla para o usuário atual, cria um atalho no menu Iniciar e inclui
um desinstalador. O atalho na área de trabalho é opcional. Quem instalar o app não
precisa ter Python, uv ou Inno Setup.

## Gerar no seu Windows

Use Windows de 64 bits (x64). O instalador Windows precisa ser gerado no Windows.

### 1. Instalar as ferramentas

Abra o PowerShell e execute:

```powershell
winget install --id astral-sh.uv --exact
winget install --id JRSoftware.InnoSetup --exact
```

O uv prepara o Python e as dependências. O Inno Setup monta o instalador.
Se não usar winget, instale o [uv](https://docs.astral.sh/uv/getting-started/installation/)
e o [Inno Setup 6](https://jrsoftware.org/isdl.php) pelos sites oficiais.
Após instalar, feche o PowerShell e abra outro para atualizar os comandos disponíveis.

### 2. Baixar uma cópia limpa do Grafla

Isso mantém os ajustes dos seus outros projetos intactos. No novo PowerShell:

```powershell
Set-Location $env:USERPROFILE
git clone https://github.com/ShardGem/Grafla.git Grafla-build
Set-Location .\Grafla-build
```

Se essa pasta já existir de uma tentativa anterior, entre nela e rode
`git pull --ff-only origin main` antes de continuar.

### 3. Gerar o instalador

Dentro da pasta `Grafla-build`, execute:

```powershell
uv sync --frozen --extra build --python 3.12
uv run python .\tools\criar_instalador.py
```

O primeiro comando prepara o ambiente. O segundo gera o aplicativo, testa a
abertura e as exportações e monta o instalador. Aguarde aparecer **Instalador pronto**.

Se o Inno Setup estiver em outra pasta, informe o caminho do compilador:

```powershell
uv run python .\tools\criar_instalador.py --iscc "C:\caminho\Inno Setup 6\ISCC.exe"
```

### 4. Encontrar e testar o arquivo

Abra a pasta do resultado:

```powershell
explorer .\dist\installer
```

O arquivo será `Grafla-2.1.0-Windows-x64-Setup.exe`. Execute-o, siga o assistente
e abra o Grafla pelo menu Iniciar. A versão usada no nome do arquivo vem de
`src/grafla/__init__.py`.

## Publicar no GitHub

1. Abra [Releases → criar release](https://github.com/ShardGem/Grafla/releases/new).
2. Em **Choose a tag**, digite **v2.1.0** e escolha **Create new tag**. Em **Target**,
   mantenha **main**, a branch usada nos comandos acima.
3. Em **Release title**, escreva **Grafla 2.1.0**.
4. Na área **Attach binaries**, arraste o arquivo `Grafla-2.1.0-Windows-x64-Setup.exe`.
5. Escreva uma descrição curta e clique em **Publish release**.

Sugestão de descrição:

> Primeira versão pública do Grafla.
>
> Editor de grafos com física, análise de caminhos e exportação de imagens.
>
> Para instalar no Windows, baixe o arquivo Setup.exe e siga o assistente.

Quem acessar a release encontrará o instalador em **Assets**.

## Gerar pelo GitHub Actions

Quando o Actions estiver disponível para a conta:

1. Abra [Actions](https://github.com/ShardGem/Grafla/actions).
2. Selecione **Testes e instalador do Grafla**.
3. Clique em **Run workflow**, mantenha a branch **main** e confirme.
4. Aguarde os testes e o job **desktop** terminarem com sucesso.
5. Abra a execução e vá até **Artifacts**, no fim da página.
6. Baixe **Grafla-Windows-Instalador** e extraia o ZIP baixado pelo GitHub.
7. O `Setup.exe` estará dentro dele. Anexe esse arquivo à release.

O Actions também disponibiliza **Grafla-Windows-Portatil**, com o aplicativo e
toda a pasta `_internal`. O instalador oferece o assistente de instalação;
o portátil é aberto depois de extrair a pasta inteira.

## Falha antes de começar

Na execução [#12](https://github.com/ShardGem/Grafla/actions/runs/43602794930/job/132470957721),
o GitHub informou que a conta estava bloqueada por um problema de cobrança.
Nenhum teste ou build chegou a iniciar. O job `desktop` foi pulado, por isso
essa execução não possui um instalador para baixar.

Resolva a pendência em [Settings → Billing and licensing](https://github.com/settings/billing)
e depois execute o workflow novamente. Enquanto isso, o procedimento local acima
permite gerar o arquivo no seu computador.
