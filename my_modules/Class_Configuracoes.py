from . import DebugModeTester

import os
import json
import logging


VERSION_DEBUGMODETESTER_COMPATIBLE = "1.0.0"
if (DebugModeTester.__version__ != VERSION_DEBUGMODETESTER_COMPATIBLE):
    raise Exception(f"Versão incompatível: DebugModeTester.__version__ {DebugModeTester.__version__}. Versão compatível: {VERSION_DEBUGMODETESTER_COMPATIBLE}")

__version__ = "1.0.0"


#------------------------------------------------------------------------------------
#                                                                                   -
#                               Class_Configuracoes                                 -
#                                                                                   -
#------------------------------------------------------------------------------------


class Class_Configuracoes:
    """
    Classe para armazenar e carregar configurações de várias classes em um arquivo JSON.
    Principais métodos:
        - set_configuracao -> Define uma configuração;
        - get_configuracao -> Retorna uma configuração, define ela caso não exista;
        - salvar -> Salva todas as configurações no arquivo JSON;
        - carregar -> Carrega todas as configurações do arquivo JSON;
    """
    logger = logging.getLogger(__name__)
    if (DebugModeTester.__debug_mode__):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    def __init__(self, arquivo):
        """
        Cria uma nova instância de Class_Configuracoes com o arquivo especificado.

        Args:
            arquivo (str): O caminho do arquivo JSON para armazenar as configurações.
        """
        self.arquivo = arquivo
        self.configuracoes = {}
        self.carregar()

    def carregar(self):
        """
        Carrega as configurações do arquivo JSON especificado.
        Se o arquivo não existir, cria um novo arquivo vazio.
        """
        try:
            with open(self.arquivo, 'r') as f:
                self.configuracoes = json.load(f)
        except FileNotFoundError:
            self.salvar()
        except:
            self.logger.warning("Erro ao carregar o arquivo de configurações. Será aberto um arquivo vazio.")
            self.configuracoes = json.loads("{}")

    def salvar(self):
        """
        Salva as configurações no arquivo JSON especificado.
        """
        os.makedirs(os.path.dirname(self.arquivo), exist_ok=True)
        with open(self.arquivo, 'w',) as f:
            json.dump(self.configuracoes, f, indent=4)

    def set_configuracao(self,ClasseDaConfiguracao, NomeDaConfiguracao, valor,salvar=True):
        """
        Armazena uma nova configuração para a classe especificada.

        Args:
            - ClasseDaConfiguracao (str): O nome da classe que está escrevendo a configuração.
            - NomeDaConfiguracao (str): A NomeDaConfiguracao da configuração a ser armazenada.
            - valor (any): O valor da configuração a ser armazenada.

        """
        if ClasseDaConfiguracao not in self.configuracoes:
            self.configuracoes[ClasseDaConfiguracao] = {}
        self.configuracoes[ClasseDaConfiguracao][NomeDaConfiguracao] = valor

        if (salvar): self.salvar()

    def get_configuracao(self,ClasseDaConfiguracao, NomeDaConfiguracao, ValueDefault=None):
        """
        Obtém o valor de uma configuração para a classe especificada.
        Caso a configuração não exista, cria ela com o valor ValueDefault.

        Args:
            - ClasseDaConfiguracao (str): O nome da classe que está lendo a configuração. Geralmente self.__class__.__name__
            - NomeDaConfiguracao (str): O nome da configuração a ser obtida.
            - ValueDefault (any): O valor padrão a ser salvo e retornado caso não exista.

        Returns:
            O valor da configuração, ou ValueDefault se a NomeDaConfiguracao ou a ClasseDaConfiguracao não existir.
        """
        if(NomeDaConfiguracao not in self.configuracoes.get(ClasseDaConfiguracao, {})):
            self.set_configuracao(ClasseDaConfiguracao, NomeDaConfiguracao, ValueDefault)
        return self.configuracoes.get(ClasseDaConfiguracao, {})[NomeDaConfiguracao]
