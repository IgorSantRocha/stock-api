

from fastapi import HTTPException, status
from core.request import RequestClient
from schemas.consulta_sincrona_schema import ResponseConsultaSincSC


class ConsultaSincrona:
    def __init__(self):
        self.url = 'http://192.168.0.214/IntegrationXmlAPI/api/v1/clo/sincrona/'
        self.headers = {
            "Content-Type": 'application/json'}

    async def executar_by_serial(self, serial: str) -> ResponseConsultaSincSC:
        request_data = {'SERGE': serial}

        request = RequestClient(
            method='POST',
            headers=self.headers,
            request_data=request_data,
            url=self.url
        )
        try:
            response = await request.send_api_request()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_424_FAILED_DEPENDENCY,
                detail={
                    "error": f"Erro na consulta síncrona: {e}"
                }
            )
        # desempacoto o JSon do result no schema
        result = ResponseConsultaSincSC(**response)

        return result
