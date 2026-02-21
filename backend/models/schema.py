from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class ClientCompany(Base):
    __tablename__ = "client_companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    api_key = Column(String, unique=True, index=True)
    credits_remaining = Column(Integer, default=100)

    scans = relationship("ScanRecord", back_populates="company")

class ScanRecord(Base):
    __tablename__ = "scan_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float)
    classification_label = Column(String)
    company_id = Column(Integer, ForeignKey("client_companies.id"))

    company = relationship("ClientCompany", back_populates="scans")
