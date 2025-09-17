"""
Comprehensive tests for configuration system following TDD Red phase.
These tests will initially fail and drive the implementation of config.py.

Tests cover PersonaConfig, ScoringConfig, and AppConfig classes with
validation, loading, and error handling.
"""

import json
import pytest
import tempfile
import yaml
from pathlib import Path
import os

import config


class TestPersonaConfig:
    """Test the PersonaConfig dataclass."""

    def test_persona_config_creation_with_valid_data(self):
        """Test creating PersonaConfig with valid data."""
        persona = config.PersonaConfig(
            name="TestBot",
            description="Test persona for TDD implementation",
            target_audience="tech enthusiasts",
            tone_of_voice="professional and engaging",
            content_pillars=["artificial intelligence", "software development"],
            forbidden_topics=["politics", "controversial subjects"],
            response_style={
                "max_length": 280,
                "use_emojis": True,
                "include_hashtags": False,
            },
        )
        assert persona.name == "TestBot"
        assert persona.target_audience == "tech enthusiasts"
        assert len(persona.content_pillars) == 2
        assert "politics" in persona.forbidden_topics
        assert persona.response_style["max_length"] == 280

    def test_persona_config_creation_with_minimal_data(self):
        """Test creating PersonaConfig with minimal required data."""
        persona = config.PersonaConfig(
            name="MinimalBot", target_audience="general", tone_of_voice="neutral"
        )
        assert persona.name == "MinimalBot"
        assert persona.description == ""
        assert persona.content_pillars == []
        assert persona.forbidden_topics == []
        assert persona.response_style == {}

    def test_persona_config_validation(self):
        """Test PersonaConfig validation methods."""
        persona = config.PersonaConfig(
            name="TestBot",
            target_audience="tech enthusiasts",
            tone_of_voice="professional",
        )
        assert persona.is_valid() is True

        # Test invalid persona (empty name)
        with pytest.raises(ValueError):
            config.PersonaConfig(
                name="",
                target_audience="tech enthusiasts",
                tone_of_voice="professional",
            )

    def test_persona_config_from_dict(self):
        """Test creating PersonaConfig from dictionary."""
        data = {
            "name": "TestBot",
            "description": "Test persona for TDD implementation",
            "target_audience": "tech enthusiasts",
            "tone_of_voice": "professional and engaging",
            "content_pillars": ["artificial intelligence", "software development"],
            "forbidden_topics": ["politics", "controversial subjects"],
            "response_style": {
                "max_length": 280,
                "use_emojis": True,
                "include_hashtags": False,
            },
        }
        persona = config.PersonaConfig.from_dict(data)
        assert persona.name == "TestBot"
        assert len(persona.content_pillars) == 2

    def test_persona_config_to_dict(self):
        """Test converting PersonaConfig to dictionary."""
        persona = config.PersonaConfig(
            name="TestBot",
            target_audience="tech enthusiasts",
            tone_of_voice="professional",
            content_pillars=["ai", "tech"],
        )
        data = persona.to_dict()
        assert data["name"] == "TestBot"
        assert "content_pillars" in data
        assert len(data["content_pillars"]) == 2


class TestScoringConfig:
    """Test the ScoringConfig dataclass."""

    def test_scoring_config_creation_with_valid_data(self):
        """Test creating ScoringConfig with valid data."""
        scoring = config.ScoringConfig(
            metric_weights={
                "engagement_rate": 0.3,
                "recency": 0.25,
                "author_credibility": 0.2,
                "content_relevance": 0.15,
                "viral_potential": 0.1,
            },
            time_decay={"half_life_hours": 24, "max_age_hours": 168},
            author_modifiers={
                "verified_boost": 1.2,
                "follower_count_weight": 0.0001,
                "engagement_history_weight": 0.15,
            },
            content_modifiers={
                "question_boost": 1.3,
                "media_boost": 1.1,
                "thread_boost": 1.15,
                "original_content_boost": 1.05,
            },
            priority_thresholds={"high": 0.8, "medium": 0.5, "low": 0.2},
        )
        assert scoring.metric_weights["engagement_rate"] == 0.3
        assert scoring.time_decay["half_life_hours"] == 24
        assert scoring.author_modifiers["verified_boost"] == 1.2
        assert scoring.priority_thresholds["high"] == 0.8

    def test_scoring_config_creation_with_defaults(self):
        """Test creating ScoringConfig with default values."""
        scoring = config.ScoringConfig()
        assert isinstance(scoring.metric_weights, dict)
        assert isinstance(scoring.time_decay, dict)
        assert isinstance(scoring.author_modifiers, dict)
        assert isinstance(scoring.content_modifiers, dict)
        assert isinstance(scoring.priority_thresholds, dict)

    def test_scoring_config_metric_weights_validation(self):
        """Test ScoringConfig metric weights validation."""
        # Valid weights that sum to 1.0
        valid_weights = {
            "engagement_rate": 0.4,
            "recency": 0.3,
            "author_credibility": 0.3,
        }
        scoring = config.ScoringConfig(metric_weights=valid_weights)
        assert scoring.validate_metric_weights() is True

        # Invalid weights that don't sum to 1.0
        invalid_weights = {"engagement_rate": 0.5, "recency": 0.7}  # Sums to 1.2
        with pytest.raises(ValueError):
            config.ScoringConfig(metric_weights=invalid_weights)

    def test_scoring_config_threshold_validation(self):
        """Test ScoringConfig threshold validation."""
        # Valid thresholds in descending order
        valid_thresholds = {"high": 0.8, "medium": 0.5, "low": 0.2}
        scoring = config.ScoringConfig(priority_thresholds=valid_thresholds)
        assert scoring.validate_thresholds() is True

        # Invalid thresholds (not in descending order)
        invalid_thresholds = {"high": 0.5, "medium": 0.8, "low": 0.2}
        with pytest.raises(ValueError):
            config.ScoringConfig(priority_thresholds=invalid_thresholds)

    def test_scoring_config_from_dict(self):
        """Test creating ScoringConfig from dictionary."""
        data = {
            "metric_weights": {
                "engagement_rate": 0.3,
                "recency": 0.25,
                "author_credibility": 0.2,
                "content_relevance": 0.15,
                "viral_potential": 0.1,
            },
            "time_decay": {"half_life_hours": 24, "max_age_hours": 168},
            "priority_thresholds": {"high": 0.8, "medium": 0.5, "low": 0.2},
        }
        scoring = config.ScoringConfig.from_dict(data)
        assert scoring.metric_weights["engagement_rate"] == 0.3
        assert scoring.time_decay["half_life_hours"] == 24

    def test_scoring_config_calculate_score(self):
        """Test ScoringConfig score calculation method."""
        scoring = config.ScoringConfig(
            metric_weights={"engagement_rate": 0.5, "recency": 0.5}
        )
        metrics = {"engagement_rate": 0.8, "recency": 0.6}
        score = scoring.calculate_score(metrics)
        assert score == 0.7  # (0.8 * 0.5) + (0.6 * 0.5)

    def test_scoring_config_get_priority_level(self):
        """Test ScoringConfig priority level determination."""
        scoring = config.ScoringConfig(
            priority_thresholds={"high": 0.8, "medium": 0.5, "low": 0.2}
        )
        assert scoring.get_priority_level(0.9) == "high"
        assert scoring.get_priority_level(0.6) == "medium"
        assert scoring.get_priority_level(0.3) == "low"
        assert scoring.get_priority_level(0.1) == "none"


class TestAppConfig:
    """Test the main AppConfig class."""

    def test_app_config_creation_with_valid_data(self):
        """Test creating AppConfig with valid data."""
        persona = config.PersonaConfig(
            name="TestBot",
            target_audience="tech enthusiasts",
            tone_of_voice="professional",
        )
        scoring = config.ScoringConfig()

        app_config = config.AppConfig(
            persona=persona,
            scoring=scoring,
            api={
                "base_url": "http://localhost:3000",
                "timeout": 30,
                "rate_limit": {"requests_per_minute": 60, "burst_limit": 10},
            },
            logging={"level": "INFO", "format": "json", "file_path": "logs/app.log"},
            processing={
                "batch_size": 50,
                "max_concurrent_requests": 5,
                "retry_attempts": 3,
                "retry_delay": 1.0,
            },
        )
        assert app_config.persona.name == "TestBot"
        assert app_config.api["base_url"] == "http://localhost:3000"
        assert app_config.logging["level"] == "INFO"
        assert app_config.processing["batch_size"] == 50

    def test_app_config_creation_with_defaults(self):
        """Test creating AppConfig with default values."""
        app_config = config.AppConfig()
        assert isinstance(app_config.persona, config.PersonaConfig)
        assert isinstance(app_config.scoring, config.ScoringConfig)
        assert isinstance(app_config.api, dict)
        assert isinstance(app_config.logging, dict)
        assert isinstance(app_config.processing, dict)

    def test_app_config_validation(self):
        """Test AppConfig validation."""
        valid_config = config.AppConfig()
        assert valid_config.validate() is True

        # Test with invalid persona - the validation happens during PersonaConfig construction
        with pytest.raises(ValueError):
            config.PersonaConfig(name="", target_audience="", tone_of_voice="")

    def test_app_config_environment_override(self):
        """Test AppConfig environment variable override."""
        os.environ["API_BASE_URL"] = "http://override.com"
        os.environ["LOG_LEVEL"] = "DEBUG"

        app_config = config.AppConfig()
        app_config.apply_environment_overrides()

        assert app_config.api["base_url"] == "http://override.com"
        assert app_config.logging["level"] == "DEBUG"

        # Clean up environment variables
        del os.environ["API_BASE_URL"]
        del os.environ["LOG_LEVEL"]

    def test_app_config_merge_configs(self):
        """Test AppConfig merging multiple configurations."""
        base_config = config.AppConfig()
        override_config = {"api": {"timeout": 60}, "logging": {"level": "DEBUG"}}

        merged = base_config.merge(override_config)
        assert merged.api["timeout"] == 60
        assert merged.logging["level"] == "DEBUG"


class TestConfigFileLoading:
    """Test configuration file loading functionality."""

    @pytest.fixture
    def sample_config_data(self):
        """Sample configuration data for testing."""
        return {
            "persona": {
                "name": "TestBot",
                "description": "Test persona for TDD implementation",
                "target_audience": "tech enthusiasts",
                "tone_of_voice": "professional and engaging",
                "content_pillars": ["artificial intelligence", "software development"],
                "forbidden_topics": ["politics", "controversial subjects"],
            },
            "scoring": {
                "metric_weights": {
                    "engagement_rate": 0.3,
                    "recency": 0.25,
                    "author_credibility": 0.2,
                    "content_relevance": 0.15,
                    "viral_potential": 0.1,
                },
                "priority_thresholds": {"high": 0.8, "medium": 0.5, "low": 0.2},
            },
            "app_config": {
                "api": {"base_url": "http://localhost:3000", "timeout": 30},
                "logging": {"level": "INFO", "format": "json"},
            },
        }

    def test_load_config_from_yaml_file(self, sample_config_data):
        """Test loading configuration from YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_config_data, f)
            temp_file_path = f.name

        try:
            app_config = config.AppConfig.from_file(temp_file_path)
            assert app_config.persona.name == "TestBot"
            assert app_config.scoring.metric_weights["engagement_rate"] == 0.3
            assert app_config.api["base_url"] == "http://localhost:3000"
        finally:
            os.unlink(temp_file_path)

    def test_load_config_from_json_file(self, sample_config_data):
        """Test loading configuration from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_config_data, f)
            temp_file_path = f.name

        try:
            app_config = config.AppConfig.from_file(temp_file_path)
            assert app_config.persona.name == "TestBot"
            assert app_config.scoring.metric_weights["engagement_rate"] == 0.3
        finally:
            os.unlink(temp_file_path)

    def test_load_config_from_fixture_file(self):
        """Test loading configuration from fixture file."""
        fixtures_path = Path(__file__).parent / "fixtures" / "sample_config.yaml"
        app_config = config.AppConfig.from_file(str(fixtures_path))

        assert app_config.persona.name == "TestBot"
        assert app_config.persona.target_audience == "tech enthusiasts"
        assert app_config.scoring.metric_weights["engagement_rate"] == 0.3
        assert app_config.api["base_url"] == "http://localhost:3000"

    def test_load_config_file_not_found(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(FileNotFoundError):
            config.AppConfig.from_file("non_existent_config.yaml")

    def test_load_config_invalid_yaml(self):
        """Test loading configuration from invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file_path = f.name

        try:
            with pytest.raises(yaml.YAMLError):
                config.AppConfig.from_file(temp_file_path)
        finally:
            os.unlink(temp_file_path)

    def test_load_config_invalid_json(self):
        """Test loading configuration from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json content}')
            temp_file_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                config.AppConfig.from_file(temp_file_path)
        finally:
            os.unlink(temp_file_path)

    def test_load_config_missing_required_fields(self):
        """Test loading configuration with missing required fields."""
        incomplete_config = {"persona": {"name": "TestBot"}}  # Missing required fields

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(incomplete_config, f)
            temp_file_path = f.name

        try:
            with pytest.raises(ValueError):
                config.AppConfig.from_file(temp_file_path)
        finally:
            os.unlink(temp_file_path)

    def test_load_config_unsupported_file_type(self):
        """Test loading configuration from unsupported file type."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("some text content")
            temp_file_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                config.AppConfig.from_file(temp_file_path)
        finally:
            os.unlink(temp_file_path)


class TestConfigValidation:
    """Test configuration validation functionality."""

    def test_validate_persona_required_fields(self):
        """Test validation of persona required fields."""
        # Missing name
        with pytest.raises(ValueError, match="name is required"):
            config.PersonaConfig(
                name="", target_audience="tech", tone_of_voice="professional"
            )

        # Missing target_audience
        with pytest.raises(ValueError, match="target_audience is required"):
            config.PersonaConfig(
                name="TestBot", target_audience="", tone_of_voice="professional"
            )

        # Missing tone_of_voice
        with pytest.raises(ValueError, match="tone_of_voice is required"):
            config.PersonaConfig(
                name="TestBot", target_audience="tech", tone_of_voice=""
            )

    def test_validate_scoring_weights_sum(self):
        """Test validation of scoring metric weights sum."""
        # Weights don't sum to 1.0
        invalid_weights = {"engagement": 0.6, "recency": 0.5}  # Sums to 1.1
        with pytest.raises(ValueError, match="Metric weights must sum to 1.0"):
            config.ScoringConfig(metric_weights=invalid_weights)

    def test_validate_scoring_threshold_order(self):
        """Test validation of scoring threshold ordering."""
        # Thresholds not in descending order
        invalid_thresholds = {"high": 0.5, "medium": 0.8, "low": 0.2}
        with pytest.raises(
            ValueError, match="Priority thresholds must be in descending order"
        ):
            config.ScoringConfig(priority_thresholds=invalid_thresholds)

    def test_validate_api_url_format(self):
        """Test validation of API URL format."""
        invalid_api_config = {"base_url": "not-a-valid-url", "timeout": 30}
        with pytest.raises(ValueError, match="Invalid API base URL format"):
            config.AppConfig(api=invalid_api_config)

    def test_validate_positive_numeric_values(self):
        """Test validation of positive numeric values."""
        # Negative timeout
        invalid_api_config = {"base_url": "http://localhost:3000", "timeout": -1}
        with pytest.raises(ValueError, match="Timeout must be positive"):
            config.AppConfig(api=invalid_api_config)

        # Zero batch size
        invalid_processing_config = {"batch_size": 0, "max_concurrent_requests": 5}
        with pytest.raises(ValueError, match="Batch size must be positive"):
            config.AppConfig(processing=invalid_processing_config)


class TestConfigDefaults:
    """Test configuration default values."""

    def test_persona_config_defaults(self):
        """Test PersonaConfig default values."""
        persona = config.PersonaConfig(
            name="TestBot", target_audience="general", tone_of_voice="neutral"
        )
        assert persona.description == ""
        assert persona.content_pillars == []
        assert persona.forbidden_topics == []
        assert persona.response_style == {}

    def test_scoring_config_defaults(self):
        """Test ScoringConfig default values."""
        scoring = config.ScoringConfig()
        assert scoring.metric_weights is not None
        assert scoring.time_decay is not None
        assert scoring.author_modifiers is not None
        assert scoring.content_modifiers is not None
        assert scoring.priority_thresholds is not None

    def test_app_config_defaults(self):
        """Test AppConfig default values."""
        app_config = config.AppConfig()
        assert app_config.api["base_url"] == "http://localhost:3000"
        assert app_config.api["timeout"] == 30
        assert app_config.logging["level"] == "INFO"
        assert app_config.processing["batch_size"] == 20
        assert app_config.processing["max_concurrent_requests"] == 3


class TestConfigSerialization:
    """Test configuration serialization and deserialization."""

    def test_config_to_dict_and_back(self):
        """Test converting config to dict and back."""
        original_config = config.AppConfig(
            persona=config.PersonaConfig(
                name="TestBot",
                target_audience="tech enthusiasts",
                tone_of_voice="professional",
            ),
            scoring=config.ScoringConfig(),
        )

        # Convert to dict and back
        config_dict = original_config.to_dict()
        restored_config = config.AppConfig.from_dict(config_dict)

        assert restored_config.persona.name == original_config.persona.name
        assert (
            restored_config.persona.target_audience
            == original_config.persona.target_audience
        )

    def test_config_json_serialization(self):
        """Test JSON serialization of configuration."""
        app_config = config.AppConfig()
        config_dict = app_config.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(config_dict)
        assert isinstance(json_str, str)

        # Should be able to deserialize back
        deserialized = json.loads(json_str)
        restored_config = config.AppConfig.from_dict(deserialized)
        assert isinstance(restored_config, config.AppConfig)
