# Schemas module
from .transformation_plan import TransformationPlan, ColumnMapping, Transformation, Enrichment
from .validation_report import ValidationReport, ValidationError, ColumnValidation
from .source_schema import SourceSchemaAnalysis, ColumnAnalysis, StructuralIssue
from .target_schema import TargetSchema, TargetColumn, GENERIC_CUSTOMER_SCHEMA, get_schema
from .detected_table import (
    TableBoundary,
    DetectedTable,
    MetadataSection,
    MultiTableAnalysis,
    TableMatch,
    TableMatchingResult,
)
from .additional_schemas import (
    TALLY_CUSTOMER_SCHEMA,
    ZOHO_CONTACT_SCHEMA,
    SALES_INVOICE_SCHEMA,
    EMPLOYEE_SCHEMA,
    SCHEMA_REGISTRY,
    get_all_schemas,
    get_schema_by_name,
)

__all__ = [
    # Transformation Plan
    "TransformationPlan",
    "ColumnMapping", 
    "Transformation",
    "Enrichment",
    # Validation
    "ValidationReport",
    "ValidationError",
    "ColumnValidation",
    # Source Schema
    "SourceSchemaAnalysis",
    "ColumnAnalysis",
    "StructuralIssue",
    # Target Schema
    "TargetSchema",
    "TargetColumn",
    "GENERIC_CUSTOMER_SCHEMA",
    "get_schema",
    # Detected Table
    "TableBoundary",
    "DetectedTable",
    "MetadataSection",
    "MultiTableAnalysis",
    "TableMatch",
    "TableMatchingResult",
    # Additional Schemas
    "TALLY_CUSTOMER_SCHEMA",
    "ZOHO_CONTACT_SCHEMA",
    "SALES_INVOICE_SCHEMA",
    "EMPLOYEE_SCHEMA",
    "SCHEMA_REGISTRY",
    "get_all_schemas",
    "get_schema_by_name",
]
