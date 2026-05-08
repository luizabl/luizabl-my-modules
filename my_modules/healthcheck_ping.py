from urllib.request import urlopen, Request


#URL_DEST = "http://localhost:8000"
URL_DEST = "http://163.176.139.152:8000"
TOKEN = "851qRBhJ5sKMMnGc47utPZ89Nhb3vL0H"

def Healthcheck_ping(nome_servido:str):
    ''' Envia ping ao servidor de Healthcheck para informar que o serviço está ativo '''
    try:
        req = Request(
            URL_DEST + f"/ping/{nome_servido}?token={TOKEN}",
            data=b"",
        )
        response = urlopen(req, timeout=5)
        return response.read().decode()
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print(Healthcheck_ping("SERVICO_TESTE"))
