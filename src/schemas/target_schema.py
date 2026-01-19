"""
Target Schema Definition.
Defines enterprise target schemas for transformation.
"""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class TargetColumn(BaseModel):
    """Definition of a column in the target schema."""
    name: str = Field(description="Column name in target")
    data_type: Literal["string", "integer", "float", "date", "boolean", "email", "phone"] = Field(
        default="string"
    )
    required: bool = Field(default=False, description="Whether this column is mandatory")
    max_length: Optional[int] = Field(default=None, description="Maximum character length")
    pattern: Optional[str] = Field(default=None, description="Regex pattern for validation")
    allowed_values: Optional[List[str]] = Field(default=None, description="Enum values if applicable")
    description: Optional[str] = Field(default=None)
    
    # Hints for the AI planner
    common_source_names: List[str] = Field(
        default_factory=list,
        description="Common variations of this column name in source files"
    )
    transformation_hint: Optional[str] = Field(
        default=None,
        description="Hint for computed columns, e.g., 'CONCATENATE: col1, col2' or 'COMPUTE: date1 - date2'"
    )


class TargetSchema(BaseModel):
    """
    Complete target schema definition.
    This defines what the output should look like.
    """
    name: str = Field(description="Schema name, e.g., 'TallyERP_Customer'")
    version: str = Field(default="1.0")
    description: Optional[str] = None
    
    columns: List[TargetColumn] = Field(default_factory=list)
    
    # Validation rules
    unique_columns: List[str] = Field(
        default_factory=list,
        description="Columns that must have unique values"
    )
    required_columns: List[str] = Field(
        default_factory=list,
        description="Columns that are mandatory"
    )
    
    def get_column(self, name: str) -> Optional[TargetColumn]:
        """Get a column by name."""
        for col in self.columns:
            if col.name.lower() == name.lower():
                return col
        return None
    
    def get_required_columns(self) -> List[TargetColumn]:
        """Get all required columns."""
        return [c for c in self.columns if c.required]


# Pre-defined enterprise schemas
GENERIC_CUSTOMER_SCHEMA = TargetSchema(
    name="Generic_Customer",
    version="1.0",
    description="Generic customer/contact schema",
    columns=[
        TargetColumn(
            name="first_name",
            data_type="string",
            required=True,
            max_length=100,
            common_source_names=["fname", "first", "first_name", "firstname", "name", "cust_name", "customer_name"]
        ),
        TargetColumn(
            name="last_name",
            data_type="string",
            required=False,
            max_length=100,
            common_source_names=["lname", "last", "last_name", "lastname", "surname"]
        ),
        TargetColumn(
            name="email",
            data_type="email",
            required=False,
            pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            common_source_names=["email", "email_id", "mail", "e-mail", "emailid"]
        ),
        TargetColumn(
            name="phone",
            data_type="phone",
            required=False,
            common_source_names=["phone", "mobile", "contact", "mobile_no", "phone_no", "mob", "cell"]
        ),
        TargetColumn(
            name="address",
            data_type="string",
            required=False,
            common_source_names=["address", "addr", "street", "location", "address1"]
        ),
        TargetColumn(
            name="city",
            data_type="string",
            required=False,
            common_source_names=["city", "town", "district"]
        ),
        TargetColumn(
            name="state",
            data_type="string",
            required=False,
            common_source_names=["state", "province", "region"]
        ),
        TargetColumn(
            name="pincode",
            data_type="string",
            required=False,
            pattern=r"^\d{6}$",
            common_source_names=["pincode", "pin", "zip", "postal_code", "zipcode"]
        ),
        TargetColumn(
            name="country",
            data_type="string",
            required=False,
            common_source_names=["country", "nation"]
        ),
        TargetColumn(
            name="gstin",
            data_type="string",
            required=False,
            pattern=r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$",
            common_source_names=["gstin", "gst", "gst_no", "gstno", "gst_number"]
        ),
    ],
    required_columns=["first_name"],
    unique_columns=["email", "gstin"]
)


def get_schema(name: str) -> Optional[TargetSchema]:
    """Get a pre-defined schema by name."""
    schemas = {
        "generic_customer": GENERIC_CUSTOMER_SCHEMA,
    }
    
    # First check local schemas
    if name.lower() in schemas:
        return schemas[name.lower()]
    
    # Then check global registry (for custom schemas)
    try:
        from .additional_schemas import SCHEMA_REGISTRY
        return SCHEMA_REGISTRY.get(name.lower())
    except:
        return None
