import sys
import os
import warnings

__version__ = "1.0.0"

#------------------------------------------------------------------------------------
#                                                                                   -
#                           Identifica o path do programa                           -
#                                                                                   -
#------------------------------------------------------------------------------------
# O programa quando é gerado um .exe ele descompacta os dados do programa em uma pasta temporária do windows
# Esse trenho do programa permite definir as pastas dos arquivos do programa sem se preocupar se ele tá rodando
# como um executável ou se ele tá rodando como um script

# É onde estão os arquivos de dados do programa que são modificados a medida que se usa o programa, como Banco de Dados, CSV etc
# Essa é a pasta onde fica o arquivo .exe
# Por exemplo, se o programa processar um arquivo e depois gravar um dados.csv para o usuário, esse arquivo deve ser guardado nesse path
application_path    = None

# É onde estão os arquivos de funcionamento da mecânica do programa, que NÃO são modificados a medida que se usa o programa.
# Como, módulos, GUI etc
# Ou seja, qualquer modificação nos arquivos nesse pasta serão apagadas ao fechar o .exe
app_data_temp_path  = None

def we_are_in_jupyter():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter

if (we_are_in_jupyter()):
    application_path = os.path.realpath("")
    app_data_temp_path = os.path.realpath("")
elif getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    app_data_temp_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    app_data_temp_path = os.path.dirname(os.path.abspath(sys.argv[0]))

# Identifica se o programa está executando em debug mode (VSCode, por exemplo) ou em modo de execução (Python)
def is_debug_mode():
    return sys.gettrace() is not None
__debug_mode__ = is_debug_mode()

if (we_are_in_jupyter()):
    __debug_mode__ = True

if (not is_debug_mode()):
    warnings.filterwarnings('ignore')
