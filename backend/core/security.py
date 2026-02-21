from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from core.database import get_db
from models.schema import ClientCompany
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_402_PAYMENT_REQUIRED

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_client_company(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API Key missing"
        )
    
    company = db.query(ClientCompany).filter(ClientCompany.api_key == api_key).first()
    
    if not company:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    if company.credits_remaining <= 0:
        raise HTTPException(
            status_code=HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits. Please top up your account."
        )
    
    # Deduct 1 credit
    company.credits_remaining -= 1
    db.commit()
    db.refresh(company)
    
    return company
