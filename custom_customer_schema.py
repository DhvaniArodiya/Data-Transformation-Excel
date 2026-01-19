"""
Custom Target Schema for Customer Data with Enriched Columns
Schema includes all original columns plus:
- full_name: Combination of First Name + Last Name
- age_at_current: Calculated age as of 2025-12-31
"""

from src.schemas.target_schema import TargetSchema, TargetColumn


CUSTOM_CUSTOMER_SCHEMA = TargetSchema(
    name="Custom_Customer_Enhanced",
    version="1.0",
    description="Customer data with full_name and age_at_current computed columns",
    columns=[
        # Original column: First Name
        TargetColumn(
            name="First Name",
            data_type="string",
            required=True,
            description="Customer's first name",
            common_source_names=["first_name", "firstname", "fname", "first"]
        ),
        # Original column: Last Name
        TargetColumn(
            name="Last Name",
            data_type="string",
            required=True,
            description="Customer's last name",
            common_source_names=["last_name", "lastname", "lname", "last", "surname"]
        ),
        # Original column: Gender
        TargetColumn(
            name="Gender",
            data_type="string",
            required=False,
            description="Customer's gender",
            common_source_names=["gender", "sex"]
        ),
        # Original column: Country
        TargetColumn(
            name="Country",
            data_type="string",
            required=False,
            description="Customer's country",
            common_source_names=["country", "nation"]
        ),
        # Original column: Age
        TargetColumn(
            name="Age",
            data_type="integer",
            required=False,
            description="Customer's age at the time in the Date column",
            common_source_names=["age"]
        ),
        # Original column: Date
        TargetColumn(
            name="Date",
            data_type="date",
            required=False,
            description="Reference date for the record",
            common_source_names=["date", "record_date", "ref_date"]
        ),
        # Original column: Id
        TargetColumn(
            name="Id",
            data_type="integer",
            required=True,
            description="Unique customer identifier",
            common_source_names=["id", "customer_id", "cust_id"]
        ),
        # NEW COLUMN: full_name (computed)
        TargetColumn(
            name="full_name",
            data_type="string",
            required=True,
            description="Full name computed from First Name + Last Name",
            common_source_names=["full_name", "fullname", "name"],
            transformation_hint="CONCATENATE: 'First Name' + ' ' + 'Last Name'"
        ),
        # NEW COLUMN: age_at_current (computed)
        TargetColumn(
            name="age_at_current",
            data_type="integer",
            required=True,
            description="Age as of 2025-12-31 (current date), calculated from Date column and original Age",
            common_source_names=["age_at_current", "current_age"],
            transformation_hint="COMPUTE: Age + years_between(Date, '2025-12-31')"
        ),
    ],
    required_columns=["First Name", "Last Name", "Id", "full_name", "age_at_current"],
    unique_columns=["Id"]
)
