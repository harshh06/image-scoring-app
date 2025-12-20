# backend/tests/test_api.py

import pytest
from io import BytesIO
from PIL import Image

from app.models import ImageScore


class TestRootEndpoint:
    """Tests for basic endpoints."""
    
    def test_root_returns_200(self, client):
        """Root endpoint should be accessible."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_health_check_with_model(self, client_with_model):
        """Health check should pass when model is loaded."""
        response = client_with_model.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True


class TestUploadImage:
    """Tests for /api/upload-image/ endpoint."""
    
    def create_test_tiff(self, filename="test.tif"):
        """Helper to create a test TIFF file."""
        img = Image.new('RGB', (224, 224), color='red')
        buffer = BytesIO()
        img.save(buffer, format='TIFF')
        buffer.seek(0)
        buffer.name = filename  # Important: Add filename attribute
        return buffer
    
    def test_upload_valid_tiff(self, client_with_model, test_db):
        """Should accept and process valid TIFF file."""
        tiff_file = self.create_test_tiff("S-1234-10X_Image001.tif")
        files = {"file": (tiff_file.name, tiff_file, "image/tiff")}
        
        response = client_with_model.post("/api/upload-image/", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "scores" in data
        assert "display_url" in data
        
        # Check database was updated
        record = test_db.query(ImageScore).first()
        assert record is not None
        assert record.filename == "S-1234-10X_Image001.tif"
    
    def test_upload_non_tiff_rejected(self, client_with_model):
        """Should reject non-TIFF files."""
        # Create a JPG file
        img = Image.new('RGB', (100, 100))
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        buffer.name = "test.jpg"
        
        files = {"file": ("test.jpg", buffer, "image/jpeg")}
        response = client_with_model.post("/api/upload-image/", files=files)
        
        assert response.status_code == 400
        assert "Only .tif files supported" in response.json()["detail"]
    
    def test_upload_duplicate_file_returns_cached(self, client_with_model, test_db):
        """Re-uploading same file should return DB record without re-inference."""
        # First upload
        tiff_file1 = self.create_test_tiff("duplicate.tif")
        files1 = {"file": ("duplicate.tif", tiff_file1, "image/tiff")}
        response1 = client_with_model.post("/api/upload-image/", files=files1)
        assert response1.status_code == 200
        original_scores = response1.json()["scores"]
        
        # Second upload (should retrieve from DB)
        tiff_file2 = self.create_test_tiff("duplicate.tif")
        files2 = {"file": ("duplicate.tif", tiff_file2, "image/tiff")}
        response2 = client_with_model.post("/api/upload-image/", files=files2)
        assert response2.status_code == 200
        cached_scores = response2.json()["scores"]
        
        # Scores should be identical (not re-inferred)
        assert original_scores == cached_scores
        
        # Should only have 1 DB record
        count = test_db.query(ImageScore).count()
        assert count == 1
    
    def test_upload_without_model_fails(self, client_without_model):
        """Should return 503 if model not loaded."""
        tiff_file = self.create_test_tiff("test.tif")
        files = {"file": ("test.tif", tiff_file, "image/tiff")}
        
        response = client_without_model.post("/api/upload-image/", files=files)
        
        assert response.status_code == 503
        assert "Model not loaded" in response.json()["detail"]


class TestUpdateScore:
    """Tests for /api/scores/{db_id} endpoint."""
    
    def test_update_existing_score(self, client, test_db):
        """Should update scores in database."""
        # Create a test record
        record = ImageScore(
            filename="test.tif",
            serial_number="S-1234-01",
            sample_id="S-1234",
            score_architecture=1.0,
            score_atrophy=1.0,
            score_complexes=1.0,
            score_fibrosis=1.0,
            score_total=4.0
        )
        test_db.add(record)
        test_db.commit()
        test_db.refresh(record)
        
        # Update fibrosis score
        payload = {"Fibrosis": 3.5}
        response = client.put(f"/api/scores/{record.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["new_total"] == 6.5  # 1+1+1+3.5
        
        # Verify in database
        test_db.refresh(record)
        assert record.score_fibrosis == 3.5
        assert record.score_total == 6.5
    
    def test_update_nonexistent_record(self, client):
        """Should return 404 for non-existent record."""
        payload = {"Fibrosis": 2.0}
        response = client.put("/api/scores/99999", json=payload)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_multiple_scores(self, client, test_db):
        """Should update multiple scores at once."""
        record = ImageScore(
            filename="multi.tif",
            serial_number="S-5678-01",
            sample_id="S-5678",
            score_architecture=1.0,
            score_atrophy=1.0,
            score_complexes=1.0,
            score_fibrosis=1.0,
            score_total=4.0
        )
        test_db.add(record)
        test_db.commit()
        test_db.refresh(record)
        
        # Update all scores
        payload = {
            "Pancreatic Architecture": 3.0,
            "Glandular Atrophy": 2.5,
            "Pseudotubular Complexes": 2.0,
            "Fibrosis": 3.5
        }
        response = client.put(f"/api/scores/{record.id}", json=payload)
        
        assert response.status_code == 200
        assert response.json()["new_total"] == 11.0