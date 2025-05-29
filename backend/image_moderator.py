# image_moderator.py
import asyncio
import hashlib
import time
from datetime import datetime
from typing import List
import logging
import numpy as np
from PIL import Image
import io

from models import ModerationResult, ModerationCategory

logger = logging.getLogger(__name__)

class ImageModerator:
    """
    Image moderation engine that analyzes images for harmful content.
    
    This is a mock implementation for demonstration purposes.
    In production, you would integrate with services like:
    - AWS Rekognition
    - Google Cloud Vision AI
    - Azure Content Moderator
    - Custom ML models
    """
    
    def __init__(self):
        self.categories = [
            "violence",
            "nudity", 
            "hate_symbols",
            "self_harm",
            "extremist_content",
            "illegal_drugs",
            "weapons",
            "harassment"
        ]
        
        # Mock patterns for demonstration
        self._risk_patterns = {
            "violence": ["blood", "weapon", "fight", "gore"],
            "nudity": ["explicit", "nude", "sexual"],
            "hate_symbols": ["swastika", "confederate", "hate"],
            "self_harm": ["cutting", "suicide", "harm"],
            "extremist_content": ["terrorist", "radical", "extremist"],
            "illegal_drugs": ["cocaine", "heroin", "meth"],
            "weapons": ["gun", "knife", "explosive"],
            "harassment": ["bullying", "threat", "intimidation"]
        }
        
    async def moderate_image(self, image: Image.Image, image_hash: str) -> ModerationResult:
        """
        Analyze an image for harmful content.
        
        Args:
            image: PIL Image object
            image_hash: SHA256 hash of the image
            
        Returns:
            ModerationResult with analysis results
        """
        start_time = time.time()
        
        try:
            # Convert image to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Analyze image (this is a mock implementation)
            categories = await self._analyze_image_content(image)
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(categories)
            
            # Determine if image is safe (threshold of 0.7)
            is_safe = risk_score < 0.6
            
            processing_time = int((time.time() - start_time) * 1000)
            
            result = ModerationResult(
                is_safe=is_safe,
                risk_score=risk_score,
                categories=categories,
                image_hash=image_hash,
                analyzed_at=datetime.utcnow(),
                processing_time_ms=processing_time
            )
            
            logger.info(f"Image analysis completed: {image_hash}, safe: {is_safe}, risk: {risk_score:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_hash}: {str(e)}")
            raise
    
    async def _analyze_image_content(self, image: Image.Image) -> List[ModerationCategory]:
        """
        Mock image analysis function.
        
        In production, this would use actual ML models or cloud services.
        For demonstration, we'll use simple heuristics based on image properties.
        """
        
        # Add small delay to simulate processing
        await asyncio.sleep(0.1)
        
        categories = []
        
        # Get image properties for mock analysis
        width, height = image.size
        pixel_data = np.array(image)
        
        # Mock analysis based on image characteristics
        for category in self.categories:
            confidence, detected = self._mock_category_analysis(category, pixel_data, width, height)
            
            categories.append(ModerationCategory(
                name=category,
                confidence=confidence,
                detected=detected
            ))
        
        return categories
    
    def _mock_category_analysis(self, category: str, pixel_data: np.ndarray, width: int, height: int) -> tuple[float, bool]:
        """
        Mock analysis for a specific category.
        
        This generates semi-realistic scores based on image properties.
        In production, you'd use trained ML models.
        """
        
        # Calculate some basic image statistics
        mean_brightness = np.mean(pixel_data)
        color_variance = np.var(pixel_data)
        aspect_ratio = width / height
        
        # Mock scoring based on category and image properties
        base_score = 0.1  # Base false positive rate
        
        if category == "violence":
            # Higher score for darker images with high contrast
            score = base_score + (1.0 - mean_brightness / 255.0) * 0.3 + min(color_variance / 10000, 0.4)
        elif category == "nudity":
            # Mock scoring based on skin tone detection (simplified)
            skin_tone_score = self._detect_skin_tones(pixel_data)
            score = base_score + skin_tone_score * 0.5
        elif category == "hate_symbols":
            # Random low score (would use symbol detection in production)
            score = base_score + np.random.random() * 0.2
        elif category == "self_harm":
            # Low random score
            score = base_score + np.random.random() * 0.15
        elif category == "extremist_content":
            # Very low score
            score = base_score + np.random.random() * 0.1
        elif category == "illegal_drugs":
            # Low random score
            score = base_score + np.random.random() * 0.2
        elif category == "weapons":
            # Slightly higher for darker images
            score = base_score + (1.0 - mean_brightness / 255.0) * 0.2
        else:  # harassment
            score = base_score + np.random.random() * 0.1
        
        # Add some randomness to make it more realistic
        score += np.random.normal(0, 0.05)
        score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
        
        # Detection threshold
        detected = score > 0.5
        
        return score, detected
    
    def _detect_skin_tones(self, pixel_data: np.ndarray) -> float:
        """
        Mock skin tone detection.
        
        In production, this would use proper skin detection algorithms.
        """
        # Simple heuristic: look for pixels in typical skin tone ranges
        # This is a very simplified approach
        r, g, b = pixel_data[:, :, 0], pixel_data[:, :, 1], pixel_data[:, :, 2]
        
        # Define skin tone ranges (very simplified)
        skin_mask = (
            (r > 95) & (g > 40) & (b > 20) &
            (r > g) & (r > b) & 
            ((r - g) > 15) & ((r - b) > 15)
        )
        
        skin_percentage = np.sum(skin_mask) / skin_mask.size
        return min(skin_percentage * 2, 1.0)  # Scale up and cap at 1.0
    
    def _calculate_risk_score(self, categories: List[ModerationCategory]) -> float:
        """
        Calculate overall risk score from individual category scores.
        """
        if not categories:
            return 0.0
        
        # Weight categories by severity
        category_weights = {
            "violence": 1.0,
            "nudity": 0.8,
            "hate_symbols": 1.0,
            "self_harm": 1.0,
            "extremist_content": 1.0,
            "illegal_drugs": 0.7,
            "weapons": 0.9,
            "harassment": 0.6
        }
        
        weighted_scores = []
        for category in categories:
            weight = category_weights.get(category.name, 0.5)
            weighted_scores.append(category.confidence * weight)
        
        # Use max score approach (any high-risk category triggers high overall risk)
        max_weighted_score = max(weighted_scores) if weighted_scores else 0.0
        
        # Also consider average to smooth out false positives
        avg_weighted_score = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0.0
        
        # Combine max and average (70% max, 30% average)
        overall_score = 0.7 * max_weighted_score + 0.3 * avg_weighted_score
        
        return min(overall_score, 1.0)