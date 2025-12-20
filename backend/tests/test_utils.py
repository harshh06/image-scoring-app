# backend/tests/test_utils.py

import pytest
import torch
import numpy as np
from PIL import Image
from io import BytesIO

from app.utils import (
    get_model,
    predict_scores,
    generate_thumbnail_and_metadata,
    MAX_SCORES,
    MODEL_TRANSFORMS
)


class TestGetModel:
    """Tests for model architecture creation."""
    
    def test_model_architecture(self):
        """Model should have correct output size."""
        model = get_model()
        assert model.fc.out_features == 4  # 4 pathology scores
    
    def test_model_is_resnet18(self):
        """Model should be based on ResNet18."""
        model = get_model()
        # ResNet18 has 18 layers, check layer4 exists
        assert hasattr(model, 'layer4')
    
    def test_model_eval_mode(self, mock_model):
        """Model should be in eval mode for inference."""
        mock_model.eval()
        assert not mock_model.training


class TestPredictScores:
    """Tests for AI inference logic."""
    
    def test_predict_scores_output_format(self, mock_model):
        """Predictions should return all 5 required keys."""
        # Create a dummy RGB image
        img = Image.new('RGB', (224, 224), color='red')
        
        scores = predict_scores(img, mock_model)
        
        assert "Pancreatic Architecture" in scores
        assert "Glandular Atrophy" in scores
        assert "Pseudotubular Complexes" in scores
        assert "Fibrosis" in scores
        assert "Total" in scores
    
    def test_scores_within_valid_range(self, mock_model):
        """All scores should be between 0 and their max values."""
        img = Image.new('RGB', (224, 224), color='blue')
        
        scores = predict_scores(img, mock_model)
        
        # Architecture: 0-4
        assert 0 <= scores["Pancreatic Architecture"] <= 4.0
        # Atrophy: 0-3
        assert 0 <= scores["Glandular Atrophy"] <= 3.0
        # Complexes: 0-3
        assert 0 <= scores["Pseudotubular Complexes"] <= 3.0
        # Fibrosis: 0-4
        assert 0 <= scores["Fibrosis"] <= 4.0
    
    def test_scores_are_rounded_to_quarter(self, mock_model):
        """Scores should be rounded to nearest 0.25."""
        img = Image.new('RGB', (224, 224), color='green')
        
        scores = predict_scores(img, mock_model)
        
        for key, value in scores.items():
            if key != "Total":
                # Check if it's divisible by 0.25
                assert (value * 4) % 1 == 0, f"{key} = {value} not rounded to 0.25"
    
    def test_total_score_is_sum(self, mock_model):
        """Total should equal sum of individual scores."""
        img = Image.new('RGB', (224, 224), color='yellow')
        
        scores = predict_scores(img, mock_model)
        
        expected_total = (
            scores["Pancreatic Architecture"] +
            scores["Glandular Atrophy"] +
            scores["Pseudotubular Complexes"] +
            scores["Fibrosis"]
        )
        
        assert abs(scores["Total"] - expected_total) < 0.01


class TestGenerateThumbnailAndMetadata:
    """Tests for filename parsing and thumbnail generation."""
    
    def test_parse_standard_filename(self):
        """Should correctly parse S-XXXX-10X_ImageXXX format."""
        # Create a dummy TIFF in memory
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='TIFF')
        file_bytes = buffer.getvalue()
        
        result = generate_thumbnail_and_metadata(
            file_bytes, 
            "S-3602-10X_Image001_ch00.tif"
        )
        
        assert result["sample_id"] == "S-3602"
        assert result["serial_number"] == "S-3602-01"
    
    def test_parse_filename_with_large_image_number(self):
        """Should extract last 2 digits from image number."""
        img = Image.new('RGB', (100, 100), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='TIFF')
        file_bytes = buffer.getvalue()
        
        result = generate_thumbnail_and_metadata(
            file_bytes,
            "S-4500-10X_Image0123_ch00.tif"
        )
        
        assert result["serial_number"] == "S-4500-23"
    
    def test_thumbnail_is_base64(self):
        """Thumbnail should be a valid base64 data URL."""
        img = Image.new('RGB', (1000, 1000), color='green')
        buffer = BytesIO()
        img.save(buffer, format='TIFF')
        file_bytes = buffer.getvalue()
        
        result = generate_thumbnail_and_metadata(
            file_bytes,
            "test.tif"
        )
        
        assert result["display_url"].startswith("data:image/png;base64,")
    
    def test_thumbnail_is_resized(self):
        """Thumbnail should be smaller than original."""
        # Create large image
        img = Image.new('RGB', (2000, 2000), color='purple')
        buffer = BytesIO()
        img.save(buffer, format='TIFF')
        file_bytes = buffer.getvalue()
        
        result = generate_thumbnail_and_metadata(file_bytes, "large.tif")
        
        # Decode base64 to check size
        import base64
        base64_data = result["display_url"].split(",")[1]
        decoded = base64.b64decode(base64_data)
        thumb_img = Image.open(BytesIO(decoded))
        
        # Should be 400x400 or smaller
        assert thumb_img.width <= 400
        assert thumb_img.height <= 400
    
    def test_handles_unknown_filename_format(self):
        """Should gracefully handle unparseable filenames."""
        img = Image.new('RGB', (100, 100), color='black')
        buffer = BytesIO()
        img.save(buffer, format='TIFF')
        file_bytes = buffer.getvalue()
        
        result = generate_thumbnail_and_metadata(
            file_bytes,
            "weird_filename.tif"
        )
        
        # Should not crash, should use defaults
        assert result["sample_id"] == "UNKNOWN"
        assert result["serial_number"].endswith("-00")