"""
Validation Agent - The "QA Tester"
Validates transformed data against target schema requirements.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import re

from .base_agent import BaseAgent
from ..schemas.target_schema import TargetSchema, GENERIC_CUSTOMER_SCHEMA
from ..schemas.validation_report import ValidationReport, ValidationError, ColumnValidation


class ValidationAgent(BaseAgent):
    """
    Validates transformed data against target schema.
    
    Responsibilities:
    - Check data types match requirements
    - Validate patterns (email, phone, GSTIN)
    - Check required fields
    - Generate quality report
    """
    
    @property
    def name(self) -> str:
        return "Validation Agent"
    
    @property
    def system_prompt(self) -> str:
        # This agent primarily uses local validation, not AI
        return ""
    
    def run(
        self,
        df: pd.DataFrame,
        target_schema: Optional[TargetSchema] = None,
    ) -> ValidationReport:
        """
        Validate transformed data.
        
        Args:
            df: Transformed DataFrame
            target_schema: Target schema to validate against
            
        Returns:
            ValidationReport with errors and quality metrics
        """
        target_schema = target_schema or GENERIC_CUSTOMER_SCHEMA
        
        errors: List[ValidationError] = []
        column_validations: List[ColumnValidation] = []
        
        # Validate each column
        for target_col in target_schema.columns:
            if target_col.name not in df.columns:
                if target_col.required:
                    # Missing required column is an error for all rows
                    for idx in range(len(df)):
                        errors.append(ValidationError(
                            row_index=idx,
                            column=target_col.name,
                            issue=f"Required column '{target_col.name}' is missing",
                            severity="error"
                        ))
                continue
            
            # Validate column data
            col_errors, col_validation = self._validate_column(
                df[target_col.name],
                target_col.name,
                target_col.data_type,
                target_col.pattern,
                target_col.required,
                target_col.allowed_values,
            )
            
            errors.extend(col_errors)
            column_validations.append(col_validation)
        
        # Build report
        total_rows = len(df)
        error_rows = set(e.row_index for e in errors if e.severity == "error")
        warning_rows = set(e.row_index for e in errors if e.severity == "warning") - error_rows
        
        report = ValidationReport(
            status="success",  # Will be updated
            total_rows=total_rows,
            successful_rows=total_rows - len(error_rows),
            failed_rows=len(error_rows),
            warning_rows=len(warning_rows),
            errors=errors,
            column_validations=column_validations,
        )
        
        report.compute_quality_score()
        report.compute_status()
        report.summary = self._generate_summary(report)
        
        return report
    
    def _validate_column(
        self,
        series: pd.Series,
        column_name: str,
        data_type: str,
        pattern: Optional[str],
        required: bool,
        allowed_values: Optional[List[str]],
    ) -> tuple[List[ValidationError], ColumnValidation]:
        """
        Validate a single column.
        
        Returns:
            Tuple of (list of errors, column validation stats)
        """
        errors = []
        valid_count = 0
        invalid_count = 0
        null_count = 0
        
        for idx, value in enumerate(series):
            # Check null
            if pd.isna(value) or value is None or str(value).strip() == "":
                null_count += 1
                if required:
                    errors.append(ValidationError(
                        row_index=idx,
                        column=column_name,
                        issue="Required field is empty",
                        value=str(value) if not pd.isna(value) else None,
                        severity="error"
                    ))
                    invalid_count += 1
                else:
                    valid_count += 1
                continue
            
            value_str = str(value).strip()
            is_valid = True
            
            # Type-specific validation
            if data_type == "email":
                if not self._validate_email(value_str):
                    errors.append(ValidationError(
                        row_index=idx,
                        column=column_name,
                        issue="Invalid email format",
                        value=value_str,
                        severity="error",
                        suggested_fix="Check email format (user@domain.com)"
                    ))
                    is_valid = False
            
            elif data_type == "phone":
                if not self._validate_phone(value_str):
                    errors.append(ValidationError(
                        row_index=idx,
                        column=column_name,
                        issue="Invalid phone number",
                        value=value_str,
                        severity="warning",
                        suggested_fix="Ensure valid phone number format"
                    ))
                    # Phone validation is a warning, not error
            
            elif data_type in ("integer", "float"):
                if not self._validate_numeric(value_str, data_type):
                    errors.append(ValidationError(
                        row_index=idx,
                        column=column_name,
                        issue=f"Invalid {data_type} value",
                        value=value_str,
                        severity="error"
                    ))
                    is_valid = False
            
            elif data_type == "date":
                if not self._validate_date(value_str):
                    errors.append(ValidationError(
                        row_index=idx,
                        column=column_name,
                        issue="Invalid date format",
                        value=value_str,
                        severity="warning"
                    ))
            
            # Pattern validation
            if pattern and is_valid:
                if not re.match(pattern, value_str):
                    errors.append(ValidationError(
                        row_index=idx,
                        column=column_name,
                        issue=f"Value doesn't match required pattern",
                        value=value_str,
                        severity="error"
                    ))
                    is_valid = False
            
            # Allowed values validation
            if allowed_values and is_valid:
                if value_str not in allowed_values:
                    errors.append(ValidationError(
                        row_index=idx,
                        column=column_name,
                        issue=f"Value not in allowed list: {allowed_values[:5]}",
                        value=value_str,
                        severity="error"
                    ))
                    is_valid = False
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        total = len(series)
        validation_rate = valid_count / total if total > 0 else 0.0
        
        return errors, ColumnValidation(
            column_name=column_name,
            valid_count=valid_count,
            invalid_count=invalid_count,
            null_count=null_count,
            validation_rate=validation_rate,
        )
    
    def _validate_email(self, value: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return bool(re.match(pattern, value))
    
    def _validate_phone(self, value: str) -> bool:
        """Basic phone validation."""
        # Remove common formatting
        cleaned = re.sub(r'[\s\-\(\)\+]', '', value)
        # Should be mostly digits
        digits = re.sub(r'\D', '', cleaned)
        return len(digits) >= 8 and len(digits) <= 15
    
    def _validate_numeric(self, value: str, num_type: str) -> bool:
        """Validate numeric values."""
        try:
            if num_type == "integer":
                int(float(value))
            else:
                float(value)
            return True
        except ValueError:
            return False
    
    def _validate_date(self, value: str) -> bool:
        """Basic date validation."""
        try:
            pd.to_datetime(value)
            return True
        except:
            return False
    
    def _generate_summary(self, report: ValidationReport) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Validation {report.status.upper()}",
            f"Total rows: {report.total_rows}",
            f"Successful: {report.successful_rows} ({report.quality_score:.1f}%)",
        ]
        
        if report.failed_rows > 0:
            lines.append(f"Failed: {report.failed_rows}")
        
        if report.warning_rows > 0:
            lines.append(f"Warnings: {report.warning_rows}")
        
        return " | ".join(lines)
