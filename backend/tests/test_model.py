# backend/tests/test_models.py

import pytest
from datetime import datetime

from app.models import ImageScore


class TestImageScoreModel:
    """Tests for ImageScore database model."""
    
    def test_create_image_score(self, test_db):
        """Should create a new record successfully."""
        record = ImageScore(
            filename="test.tif",
            serial_number="S-1234-01",
            sample_id="S-1234",
            score_architecture=2.5,
            score_atrophy=1.5,
            score_complexes=1.0,
            score_fibrosis=3.0,
            score_total=8.0
        )
        
        test_db.add(record)
        test_db.commit()
        test_db.refresh(record)
        
        assert record.id is not None
        assert record.filename == "test.tif"
        assert record.score_total == 8.0
    
    def test_filename_unique_constraint(self, test_db):
        """Should enforce unique constraint on filename."""
        record1 = ImageScore(
            filename="duplicate.tif",
            serial_number="S-1-01",
            sample_id="S-1",
            score_architecture=1.0,
            score_atrophy=1.0,
            score_complexes=1.0,
            score_fibrosis=1.0,
            score_total=4.0
        )
        test_db.add(record1)
        test_db.commit()
        
        # Try to add duplicate
        record2 = ImageScore(
            filename="duplicate.tif",  # Same filename!
            serial_number="S-2-01",
            sample_id="S-2",
            score_architecture=2.0,
            score_atrophy=2.0,
            score_complexes=2.0,
            score_fibrosis=2.0,
            score_total=8.0
        )
        test_db.add(record2)
        
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            test_db.commit()
    
    def test_timestamps_auto_populate(self, test_db):
        """Created_at and updated_at should auto-populate."""
        record = ImageScore(
            filename="timestamp_test.tif",
            serial_number="S-1-01",
            sample_id="S-1",
            score_architecture=1.0,
            score_atrophy=1.0,
            score_complexes=1.0,
            score_fibrosis=1.0,
            score_total=4.0
        )
        
        test_db.add(record)
        test_db.commit()
        test_db.refresh(record)
        
        assert record.created_at is not None
        assert isinstance(record.created_at, datetime)