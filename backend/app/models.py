# backend/app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base  # Import Base from your database.py, don't create a new one!

class ImageScore(Base):
    __tablename__ = "image_scores"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # File Metadata
    filename = Column(String, index=True)      # e.g., "S-3602-10X_Image001.tif"
    serial_number = Column(String, index=True) # e.g., "S-3602-01" (Unique ID)
    sample_id = Column(String, index=True)     # e.g., "S-3602"    (Group ID)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # This automatically updates whenever you overwrite a row
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # The 4 Specific Pathology Scores
    score_architecture = Column(Float)
    score_atrophy = Column(Float)
    score_complexes = Column(Float)
    score_fibrosis = Column(Float)
    
    # Total Score
    score_total = Column(Float)

    def __repr__(self):
        return f"<ImageScore(id={self.id}, serial='{self.serial_number}', total={self.score_total})>"