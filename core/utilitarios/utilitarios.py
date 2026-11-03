import sys, os

from PyQt6.QtGui import QColor

def interpolar_cor(c1: QColor, c2: QColor, alpha: float) -> QColor:
    r = int(c1.red() + alpha * (c2.red() - c1.red()))
    g = int(c1.green() + alpha * (c2.green() - c1.green()))
    b = int(c1.blue() + alpha * (c2.blue() - c1.blue()))
    return QColor(r, g, b)

def resource_path(relative_path):
    """
    Retorna o caminho absoluto de um recurso, funcionando tanto no PyInstaller (--onefile)
    quanto no modo desenvolvimento (PyCharm).
    """
    if hasattr(sys, '_MEIPASS'):
        # Quando empacotado pelo PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Quando rodando no PyCharm ou direto como .py
        base_path = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(base_path, "..", ".."))  # Sobe para a raiz do projeto
        return os.path.join(project_root, relative_path)