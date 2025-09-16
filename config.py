"""
Minimal configuration management system to make failing tests pass.

This module implements PersonaConfig, ScoringConfig, and AppConfig classes
following TDD Green phase - implementing only what's needed to pass tests.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import json
import yaml
import os
import re
from urllib.parse import urlparse


@dataclass
class PersonaConfig:
    """Persona configuration for AI agent behavior."""
    
    name: str
    target_audience: str
    tone_of_voice: str
    description: str = ""
    content_pillars: List[str] = field(default_factory=list)
    forbidden_topics: List[str] = field(default_factory=list)
    response_style: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate persona configuration."""
        if not self.name or self.name.strip() == "":
            raise ValueError("name is required")
        if not self.target_audience or self.target_audience.strip() == "":
            raise ValueError("target_audience is required")
        if not self.tone_of_voice or self.tone_of_voice.strip() == "":
            raise ValueError("tone_of_voice is required")
    
    def is_valid(self) -> bool:
        """Check if persona configuration is valid."""
        return (bool(self.name and self.name.strip()) and
                bool(self.target_audience and self.target_audience.strip()) and
                bool(self.tone_of_voice and self.tone_of_voice.strip()))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonaConfig':
        """Create PersonaConfig from dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            target_audience=data.get("target_audience", ""),
            tone_of_voice=data.get("tone_of_voice", ""),
            content_pillars=data.get("content_pillars", []),
            forbidden_topics=data.get("forbidden_topics", []),
            response_style=data.get("response_style", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PersonaConfig to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "target_audience": self.target_audience,
            "tone_of_voice": self.tone_of_voice,
            "content_pillars": self.content_pillars,
            "forbidden_topics": self.forbidden_topics,
            "response_style": self.response_style
        }


@dataclass
class ScoringConfig:
    """Scoring configuration for content evaluation."""
    
    metric_weights: Dict[str, float] = field(default_factory=lambda: {
        "engagement_rate": 0.3,
        "recency": 0.25,
        "author_credibility": 0.2,
        "content_relevance": 0.15,
        "viral_potential": 0.1
    })
    time_decay: Dict[str, int] = field(default_factory=lambda: {
        "half_life_hours": 24,
        "max_age_hours": 168
    })
    author_modifiers: Dict[str, float] = field(default_factory=lambda: {
        "verified_boost": 1.2,
        "follower_count_weight": 0.0001,
        "engagement_history_weight": 0.15
    })
    content_modifiers: Dict[str, float] = field(default_factory=lambda: {
        "question_boost": 1.3,
        "media_boost": 1.1,
        "thread_boost": 1.15,
        "original_content_boost": 1.05
    })
    priority_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2
    })
    
    def __post_init__(self):
        """Validate scoring configuration."""
        self.validate_metric_weights()
        self.validate_thresholds()
    
    def validate_metric_weights(self) -> bool:
        """Validate that metric weights sum to approximately 1.0."""
        total = sum(self.metric_weights.values())
        if not (0.99 <= total <= 1.01):  # Allow for small floating point errors
            raise ValueError(f"Metric weights must sum to 1.0, got {total}")
        return True
    
    def validate_thresholds(self) -> bool:
        """Validate that priority thresholds are in descending order."""
        thresholds = self.priority_thresholds
        if "high" in thresholds and "medium" in thresholds and "low" in thresholds:
            if not (thresholds["high"] > thresholds["medium"] > thresholds["low"]):
                raise ValueError("Priority thresholds must be in descending order (high > medium > low)")
        return True
    
    def calculate_score(self, metrics: Dict[str, float]) -> float:
        """Calculate weighted score from metrics."""
        total_score = 0.0
        for metric, weight in self.metric_weights.items():
            if metric in metrics:
                total_score += metrics[metric] * weight
        return total_score
    
    def get_priority_level(self, score: float) -> str:
        """Get priority level based on score."""
        if score >= self.priority_thresholds.get("high", 0.8):
            return "high"
        elif score >= self.priority_thresholds.get("medium", 0.5):
            return "medium"
        elif score >= self.priority_thresholds.get("low", 0.2):
            return "low"
        else:
            return "none"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoringConfig':
        """Create ScoringConfig from dictionary."""
        return cls(
            metric_weights=data.get("metric_weights", {}),
            time_decay=data.get("time_decay", {}),
            author_modifiers=data.get("author_modifiers", {}),
            content_modifiers=data.get("content_modifiers", {}),
            priority_thresholds=data.get("priority_thresholds", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ScoringConfig to dictionary."""
        return {
            "metric_weights": self.metric_weights,
            "time_decay": self.time_decay,
            "author_modifiers": self.author_modifiers,
            "content_modifiers": self.content_modifiers,
            "priority_thresholds": self.priority_thresholds
        }


@dataclass
class AppConfig:
    """Main application configuration."""
    
    persona: Optional[PersonaConfig] = None
    scoring: Optional[ScoringConfig] = None
    api: Dict[str, Any] = field(default_factory=lambda: {
        "base_url": "http://localhost:3000",
        "timeout": 30,
        "rate_limit": {
            "requests_per_minute": 60,
            "burst_limit": 10
        }
    })
    logging: Dict[str, Any] = field(default_factory=lambda: {
        "level": "INFO",
        "format": "json",
        "file_path": "logs/app.log"
    })
    processing: Dict[str, Any] = field(default_factory=lambda: {
        "batch_size": 20,
        "max_concurrent_requests": 3,
        "retry_attempts": 3,
        "retry_delay": 1.0
    })
    
    def __post_init__(self):
        """Initialize default configurations and validate."""
        if self.persona is None:
            self.persona = PersonaConfig(
                name="DefaultBot",
                target_audience="general",
                tone_of_voice="neutral"
            )
        if self.scoring is None:
            self.scoring = ScoringConfig()
        
        self._validate_api_config()
        self._validate_processing_config()
    
    def _validate_api_config(self):
        """Validate API configuration."""
        if "base_url" in self.api:
            url = self.api["base_url"]
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid API base URL format: {url}")
        
        if "timeout" in self.api and self.api["timeout"] <= 0:
            raise ValueError("Timeout must be positive")
    
    def _validate_processing_config(self):
        """Validate processing configuration."""
        if "batch_size" in self.processing and self.processing["batch_size"] <= 0:
            raise ValueError("Batch size must be positive")
    
    def validate(self) -> bool:
        """Validate entire configuration."""
        try:
            if not self.persona.is_valid():
                raise ValueError("Invalid persona configuration")
            self.scoring.validate_metric_weights()
            self.scoring.validate_thresholds()
            self._validate_api_config()
            self._validate_processing_config()
            return True
        except Exception:
            return False
    
    def apply_environment_overrides(self):
        """Apply environment variable overrides."""
        if "API_BASE_URL" in os.environ:
            self.api["base_url"] = os.environ["API_BASE_URL"]
        if "LOG_LEVEL" in os.environ:
            self.logging["level"] = os.environ["LOG_LEVEL"]
        if "BATCH_SIZE" in os.environ:
            try:
                self.processing["batch_size"] = int(os.environ["BATCH_SIZE"])
            except ValueError:
                pass
    
    def merge(self, other_config: Dict[str, Any]) -> 'AppConfig':
        """Merge with another configuration dictionary."""
        # Create a copy of current config
        merged_data = self.to_dict()
        
        # Merge other config
        for key, value in other_config.items():
            if key in merged_data and isinstance(merged_data[key], dict) and isinstance(value, dict):
                merged_data[key].update(value)
            else:
                merged_data[key] = value
        
        return AppConfig.from_dict(merged_data)
    
    @classmethod
    def from_file(cls, file_path: str) -> 'AppConfig':
        """Load configuration from file."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Determine file format
        suffix = path.suffix.lower()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif suffix == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {suffix}")
        
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {file_path}: {e}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {file_path}", e.doc, e.pos)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create AppConfig from dictionary."""
        # Create persona config
        persona_data = data.get("persona", {})
        if not persona_data.get("name") or not persona_data.get("target_audience") or not persona_data.get("tone_of_voice"):
            if not persona_data:
                # Use defaults if no persona data provided
                persona = PersonaConfig(
                    name="DefaultBot",
                    target_audience="general", 
                    tone_of_voice="neutral"
                )
            else:
                # Missing required fields
                raise ValueError("Persona configuration missing required fields")
        else:
            persona = PersonaConfig.from_dict(persona_data)
        
        # Create scoring config
        scoring_data = data.get("scoring", {})
        scoring = ScoringConfig.from_dict(scoring_data)
        
        # Get other config sections
        api_config = data.get("api", data.get("app_config", {}).get("api", {}))
        logging_config = data.get("logging", data.get("app_config", {}).get("logging", {}))
        processing_config = data.get("processing", data.get("app_config", {}).get("processing", {}))
        
        return cls(
            persona=persona,
            scoring=scoring,
            api=api_config,
            logging=logging_config,
            processing=processing_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert AppConfig to dictionary."""
        return {
            "persona": self.persona.to_dict() if self.persona else {},
            "scoring": self.scoring.to_dict() if self.scoring else {},
            "api": self.api,
            "logging": self.logging,
            "processing": self.processing
        }