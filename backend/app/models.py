# backend/app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Define the base class for declarative models
Base = declarative_base()

class ImageEntry(Base):
    """
    SQLAlchemy Model for storing extracted image data and scoring results.
    """
    __tablename__ = 'images'
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Extraction Metadata
    serial_number = Column(String, index=True, nullable=False, unique=True)
    pdf_filename = Column(String, nullable=False)
    image_storage_path = Column(String, nullable=False) # Local or S3 path to the original image file
    
    # The 4 Scoring Parameters (use Float for numerical scores)
    score_param1 = Column(Float, nullable=False)
    score_param2 = Column(Float, nullable=False)
    score_param3 = Column(Float, nullable=False)
    score_param4 = Column(Float, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ImageEntry(id={self.id}, serial='{self.serial_number}', score1={self.score_param1})>"