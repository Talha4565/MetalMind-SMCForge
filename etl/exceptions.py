"""Custom exceptions for ETL pipeline."""


class ETLException(Exception):
    """Base exception for all ETL errors."""
    pass


class ExtractionError(ETLException):
    """Raised when data extraction fails."""
    pass


class TransformationError(ETLException):
    """Raised when data transformation fails."""
    pass


class LoadError(ETLException):
    """Raised when data loading fails."""
    pass


class ValidationError(ETLException):
    """Raised when data validation fails."""
    pass


class ConfigurationError(ETLException):
    """Raised when configuration is invalid."""
    pass


class PipelineError(ETLException):
    """Raised when pipeline execution fails."""
    pass
