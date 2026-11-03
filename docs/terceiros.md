# Dependências e distribuição

Esta lista descreve dependências; não atribui uma licença ao código do Grafla.

| Componente | Versão direta | Termos indicados pelo projeto |
|---|---|---|
| PyQt6 | 6.12.0 | GPLv3 ou licença comercial do fornecedor |
| Qt (via PyQt6-Qt6) | transitiva, congelada em uv.lock | LGPL/GPL/comercial conforme componente |
| PyQt6-sip | transitiva, congelada em uv.lock | BSD-2-Clause |
| NetworkX | 3.7 | BSD-3-Clause |
| PyInstaller | 6.22.3, build opcional | GPL com exceção de distribuição |

Os pacotes transitivos de build são separados do runtime. O spec inclui a metadata
e os arquivos de licença dos pacotes runtime disponíveis em seus dist-info. Consulte
os textos fornecidos nos pacotes, especialmente antes de distribuir binários.
As licenças dos testes/lint/build não substituem as do aplicativo e do Qt.

Fontes: [PyQt](https://www.riverbankcomputing.com/software/pyqt/),
[Qt](https://www.qt.io/licensing/), [NetworkX](https://networkx.org/),
[PyInstaller](https://pyinstaller.org/). Versões e metadados também estão no PyPI.
