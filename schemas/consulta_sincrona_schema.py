from pydantic import BaseModel


class ResponseConsultaSincSC(BaseModel):
    TYPE: str
    MSG: str
    EQUNR: str
    MATNR: str
    SERNR: str
    WERKS: str
    LGORT: str
    STTXU: str
    TYPBZ: str
    SHTXT: str
    LBBSA: str
    STTXT: str
    SERGE: str
    TPLNR: str
    ERDAT: str
    ZGAR_FA: str
    ZGAR_RE: str
    ZSTA_EQ: str
    EQFNR: str
    LAGER: str
    ZVER_AP: str
    ZTIPO: str

    class Config:
        from_attributes = True
        populate_by_name = True
