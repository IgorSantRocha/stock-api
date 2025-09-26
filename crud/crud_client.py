from crud.baseAsync import CRUDBase
from models.client_model import Client
from schemas.client_schema import ClientCreateSC, ClientUpdateSC


class CRUDClient(CRUDBase[Client, ClientCreateSC, ClientUpdateSC]):
    pass


client_crud = CRUDClient(Client)
