"""
Additional Target Schema Definitions.
Pre-built schemas for common enterprise systems.
"""

from .target_schema import TargetSchema, TargetColumn


# ==================== Tally ERP Customer Schema ====================
TALLY_CUSTOMER_SCHEMA = TargetSchema(
    name="Tally_Customer",
    version="1.0",
    description="Tally ERP Customer/Ledger schema",
    columns=[
        TargetColumn(
            name="ledger_name",
            data_type="string",
            required=True,
            max_length=256,
            description="Party/Ledger name in Tally",
            common_source_names=["name", "party_name", "customer_name", "ledger", "account_name", "firm_name", "company_name"]
        ),
        TargetColumn(
            name="alias",
            data_type="string",
            required=False,
            description="Alias name for the ledger",
            common_source_names=["short_name", "nick_name", "alias", "code"]
        ),
        TargetColumn(
            name="parent_group",
            data_type="string",
            required=True,
            description="Parent group (Sundry Debtors, Sundry Creditors, etc.)",
            allowed_values=["Sundry Debtors", "Sundry Creditors", "Cash-in-Hand", "Bank Accounts"],
            common_source_names=["group", "parent", "category", "type"]
        ),
        TargetColumn(
            name="gstin",
            data_type="string",
            required=False,
            pattern=r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}$",
            description="GST Identification Number",
            common_source_names=["gstin", "gst", "gst_no", "gstno", "gst_number"]
        ),
        TargetColumn(
            name="pan",
            data_type="string",
            required=False,
            pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
            description="PAN Number",
            common_source_names=["pan", "pan_no", "panno", "pan_number"]
        ),
        TargetColumn(
            name="address_line1",
            data_type="string",
            required=False,
            description="Address line 1",
            common_source_names=["address", "address1", "street", "address_line_1"]
        ),
        TargetColumn(
            name="address_line2",
            data_type="string",
            required=False,
            description="Address line 2",
            common_source_names=["address2", "address_line_2", "landmark"]
        ),
        TargetColumn(
            name="city",
            data_type="string",
            required=False,
            common_source_names=["city", "town", "place"]
        ),
        TargetColumn(
            name="state",
            data_type="string",
            required=False,
            common_source_names=["state", "province"]
        ),
        TargetColumn(
            name="pincode",
            data_type="string",
            required=False,
            pattern=r"^\d{6}$",
            common_source_names=["pincode", "pin", "zip", "postal_code"]
        ),
        TargetColumn(
            name="country",
            data_type="string",
            required=False,
            common_source_names=["country"]
        ),
        TargetColumn(
            name="contact_person",
            data_type="string",
            required=False,
            common_source_names=["contact", "contact_name", "contact_person", "poc"]
        ),
        TargetColumn(
            name="phone",
            data_type="phone",
            required=False,
            common_source_names=["phone", "mobile", "contact_no", "phone_no", "tel"]
        ),
        TargetColumn(
            name="email",
            data_type="email",
            required=False,
            common_source_names=["email", "email_id", "mail"]
        ),
        TargetColumn(
            name="opening_balance",
            data_type="float",
            required=False,
            description="Opening balance (positive for debit, negative for credit)",
            common_source_names=["opening", "opening_bal", "ob", "balance"]
        ),
        TargetColumn(
            name="credit_limit",
            data_type="float",
            required=False,
            description="Credit limit for the party",
            common_source_names=["credit_limit", "limit", "cl"]
        ),
    ],
    required_columns=["ledger_name", "parent_group"],
    unique_columns=["ledger_name", "gstin"]
)


# ==================== Zoho CRM Contact Schema ====================
ZOHO_CONTACT_SCHEMA = TargetSchema(
    name="Zoho_Contact",
    version="1.0",
    description="Zoho CRM Contact schema",
    columns=[
        TargetColumn(
            name="first_name",
            data_type="string",
            required=False,
            max_length=100,
            common_source_names=["first_name", "firstname", "fname", "first"]
        ),
        TargetColumn(
            name="last_name",
            data_type="string",
            required=True,
            max_length=100,
            common_source_names=["last_name", "lastname", "lname", "last", "surname"]
        ),
        TargetColumn(
            name="email",
            data_type="email",
            required=False,
            common_source_names=["email", "email_id", "mail", "email_address"]
        ),
        TargetColumn(
            name="phone",
            data_type="phone",
            required=False,
            common_source_names=["phone", "work_phone", "office_phone", "landline"]
        ),
        TargetColumn(
            name="mobile",
            data_type="phone",
            required=False,
            common_source_names=["mobile", "cell", "mobile_phone", "cell_phone"]
        ),
        TargetColumn(
            name="account_name",
            data_type="string",
            required=False,
            description="Associated company/account name",
            common_source_names=["company", "company_name", "organization", "account", "firm"]
        ),
        TargetColumn(
            name="title",
            data_type="string",
            required=False,
            description="Job title/designation",
            common_source_names=["title", "designation", "job_title", "position"]
        ),
        TargetColumn(
            name="department",
            data_type="string",
            required=False,
            common_source_names=["department", "dept", "division"]
        ),
        TargetColumn(
            name="mailing_street",
            data_type="string",
            required=False,
            common_source_names=["address", "street", "mailing_address"]
        ),
        TargetColumn(
            name="mailing_city",
            data_type="string",
            required=False,
            common_source_names=["city", "mailing_city"]
        ),
        TargetColumn(
            name="mailing_state",
            data_type="string",
            required=False,
            common_source_names=["state", "mailing_state", "province"]
        ),
        TargetColumn(
            name="mailing_zip",
            data_type="string",
            required=False,
            common_source_names=["zip", "pincode", "postal_code", "mailing_zip"]
        ),
        TargetColumn(
            name="mailing_country",
            data_type="string",
            required=False,
            common_source_names=["country", "mailing_country"]
        ),
        TargetColumn(
            name="lead_source",
            data_type="string",
            required=False,
            allowed_values=["Advertisement", "Cold Call", "Employee Referral", "External Referral", 
                          "Online Store", "Partner", "Public Relations", "Trade Show", "Web Form", "Other"],
            common_source_names=["source", "lead_source", "how_did_you_hear"]
        ),
        TargetColumn(
            name="description",
            data_type="string",
            required=False,
            common_source_names=["description", "notes", "comments", "remarks"]
        ),
    ],
    required_columns=["last_name"],
    unique_columns=["email"]
)


# ==================== Sales Invoice Schema ====================
SALES_INVOICE_SCHEMA = TargetSchema(
    name="Sales_Invoice",
    version="1.0",
    description="Generic Sales Invoice Line Item schema",
    columns=[
        TargetColumn(
            name="invoice_number",
            data_type="string",
            required=True,
            common_source_names=["invoice_no", "inv_no", "bill_no", "invoice", "invoice_number"]
        ),
        TargetColumn(
            name="invoice_date",
            data_type="date",
            required=True,
            common_source_names=["date", "invoice_date", "bill_date", "inv_date"]
        ),
        TargetColumn(
            name="customer_name",
            data_type="string",
            required=True,
            common_source_names=["customer", "party", "buyer", "sold_to", "customer_name", "bill_to"]
        ),
        TargetColumn(
            name="item_name",
            data_type="string",
            required=True,
            common_source_names=["item", "product", "description", "particulars", "item_name", "goods"]
        ),
        TargetColumn(
            name="hsn_code",
            data_type="string",
            required=False,
            pattern=r"^\d{4,8}$",
            common_source_names=["hsn", "hsn_code", "sac", "sac_code"]
        ),
        TargetColumn(
            name="quantity",
            data_type="float",
            required=True,
            common_source_names=["qty", "quantity", "units", "nos"]
        ),
        TargetColumn(
            name="unit",
            data_type="string",
            required=False,
            allowed_values=["Nos", "Pcs", "Kg", "Gm", "Ltr", "Mtr", "Box", "Doz", "Set"],
            common_source_names=["unit", "uom", "unit_of_measure"]
        ),
        TargetColumn(
            name="rate",
            data_type="float",
            required=True,
            common_source_names=["rate", "price", "unit_price", "mrp"]
        ),
        TargetColumn(
            name="amount",
            data_type="float",
            required=True,
            common_source_names=["amount", "total", "value", "line_total"]
        ),
        TargetColumn(
            name="discount",
            data_type="float",
            required=False,
            common_source_names=["discount", "disc", "discount_amount"]
        ),
        TargetColumn(
            name="taxable_value",
            data_type="float",
            required=False,
            common_source_names=["taxable", "taxable_value", "net_amount"]
        ),
        TargetColumn(
            name="cgst_rate",
            data_type="float",
            required=False,
            common_source_names=["cgst_rate", "cgst%", "cgst_percent"]
        ),
        TargetColumn(
            name="cgst_amount",
            data_type="float",
            required=False,
            common_source_names=["cgst", "cgst_amount", "cgst_amt"]
        ),
        TargetColumn(
            name="sgst_rate",
            data_type="float",
            required=False,
            common_source_names=["sgst_rate", "sgst%", "sgst_percent"]
        ),
        TargetColumn(
            name="sgst_amount",
            data_type="float",
            required=False,
            common_source_names=["sgst", "sgst_amount", "sgst_amt"]
        ),
        TargetColumn(
            name="igst_rate",
            data_type="float",
            required=False,
            common_source_names=["igst_rate", "igst%", "igst_percent"]
        ),
        TargetColumn(
            name="igst_amount",
            data_type="float",
            required=False,
            common_source_names=["igst", "igst_amount", "igst_amt"]
        ),
        TargetColumn(
            name="total_amount",
            data_type="float",
            required=True,
            common_source_names=["grand_total", "invoice_total", "net_payable", "total_amount"]
        ),
    ],
    required_columns=["invoice_number", "invoice_date", "customer_name", "item_name", "quantity", "rate", "amount", "total_amount"],
    unique_columns=["invoice_number"]
)


# ==================== Employee Schema ====================
EMPLOYEE_SCHEMA = TargetSchema(
    name="Employee",
    version="1.0",
    description="HR Employee data schema",
    columns=[
        TargetColumn(
            name="employee_id",
            data_type="string",
            required=True,
            common_source_names=["emp_id", "employee_id", "employee_code", "emp_code", "id"]
        ),
        TargetColumn(
            name="first_name",
            data_type="string",
            required=True,
            common_source_names=["first_name", "fname", "firstname"]
        ),
        TargetColumn(
            name="last_name",
            data_type="string",
            required=False,
            common_source_names=["last_name", "lname", "lastname", "surname"]
        ),
        TargetColumn(
            name="email",
            data_type="email",
            required=False,
            common_source_names=["email", "work_email", "official_email"]
        ),
        TargetColumn(
            name="phone",
            data_type="phone",
            required=False,
            common_source_names=["phone", "mobile", "contact"]
        ),
        TargetColumn(
            name="department",
            data_type="string",
            required=False,
            common_source_names=["department", "dept", "division"]
        ),
        TargetColumn(
            name="designation",
            data_type="string",
            required=False,
            common_source_names=["designation", "title", "position", "job_title"]
        ),
        TargetColumn(
            name="date_of_joining",
            data_type="date",
            required=False,
            common_source_names=["doj", "joining_date", "date_of_joining", "start_date"]
        ),
        TargetColumn(
            name="date_of_birth",
            data_type="date",
            required=False,
            common_source_names=["dob", "birth_date", "date_of_birth", "birthday"]
        ),
        TargetColumn(
            name="pan",
            data_type="string",
            required=False,
            pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
            common_source_names=["pan", "pan_no"]
        ),
        TargetColumn(
            name="uan",
            data_type="string",
            required=False,
            pattern=r"^\d{12}$",
            description="Universal Account Number (PF)",
            common_source_names=["uan", "pf_no", "pf_number"]
        ),
        TargetColumn(
            name="bank_account",
            data_type="string",
            required=False,
            common_source_names=["account_no", "bank_account", "acc_no"]
        ),
        TargetColumn(
            name="ifsc_code",
            data_type="string",
            required=False,
            pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$",
            common_source_names=["ifsc", "ifsc_code"]
        ),
        TargetColumn(
            name="salary",
            data_type="float",
            required=False,
            common_source_names=["salary", "ctc", "basic", "gross"]
        ),
    ],
    required_columns=["employee_id", "first_name"],
    unique_columns=["employee_id", "email", "pan"]
)


# ==================== Superstore Order Schema ====================
SUPERSTORE_ORDER_SCHEMA = TargetSchema(
    name="Superstore_Order",
    version="1.0",
    description="Superstore order schema with computed address and shipping days",
    columns=[
        TargetColumn(
            name="order_id",
            data_type="string",
            required=True,
            description="Unique order identifier",
            common_source_names=["order_id", "order_no", "order_number"]
        ),
        TargetColumn(
            name="order_date",
            data_type="date",
            required=True,
            description="Date the order was placed",
            common_source_names=["order_date", "date", "order_dt"]
        ),
        TargetColumn(
            name="ship_date",
            data_type="date",
            required=True,
            description="Date the order was shipped",
            common_source_names=["ship_date", "shipping_date", "shipped_date"]
        ),
        TargetColumn(
            name="shipping_days",
            data_type="integer",
            required=True,
            description="Days between order and shipping (computed: ship_date - order_date)",
            common_source_names=["shipping_days", "delivery_days", "days_to_ship"],
            transformation_hint="COMPUTE: ship_date - order_date"
        ),
        TargetColumn(
            name="full_address",
            data_type="string",
            required=True,
            description="Complete address (computed: city + state + country)",
            common_source_names=["full_address", "address", "complete_address"],
            transformation_hint="CONCATENATE: city, state, country WITH ', '"
        ),
        TargetColumn(
            name="city",
            data_type="string",
            required=False,
            common_source_names=["city", "town"]
        ),
        TargetColumn(
            name="state",
            data_type="string",
            required=False,
            common_source_names=["state", "province", "region"]
        ),
        TargetColumn(
            name="country",
            data_type="string",
            required=False,
            common_source_names=["country", "nation"]
        ),
        TargetColumn(
            name="customer_name",
            data_type="string",
            required=True,
            common_source_names=["customer_name", "customer", "name", "buyer"]
        ),
        TargetColumn(
            name="product_name",
            data_type="string",
            required=True,
            common_source_names=["product_name", "product", "item", "item_name"]
        ),
        TargetColumn(
            name="category",
            data_type="string",
            required=False,
            common_source_names=["category", "product_category", "type"]
        ),
        TargetColumn(
            name="sales",
            data_type="float",
            required=True,
            common_source_names=["sales", "amount", "revenue", "total"]
        ),
        TargetColumn(
            name="quantity",
            data_type="integer",
            required=True,
            common_source_names=["quantity", "qty", "units"]
        ),
        TargetColumn(
            name="profit",
            data_type="float",
            required=False,
            common_source_names=["profit", "margin", "earnings"]
        ),
    ],
    required_columns=["order_id", "order_date", "ship_date", "shipping_days", "full_address", "customer_name", "product_name", "sales", "quantity"],
    unique_columns=[]
)


# ==================== Schema Registry ====================
SCHEMA_REGISTRY = {
    "generic_customer": None,  # Will import from target_schema.py
    "tally_customer": TALLY_CUSTOMER_SCHEMA,
    "zoho_contact": ZOHO_CONTACT_SCHEMA,
    "sales_invoice": SALES_INVOICE_SCHEMA,
    "employee": EMPLOYEE_SCHEMA,
    "superstore_order": SUPERSTORE_ORDER_SCHEMA,
}


def get_all_schemas():
    """Get all available schemas."""
    from .target_schema import GENERIC_CUSTOMER_SCHEMA
    SCHEMA_REGISTRY["generic_customer"] = GENERIC_CUSTOMER_SCHEMA
    return SCHEMA_REGISTRY


def get_schema_by_name(name: str):
    """Get a schema by name."""
    from .target_schema import GENERIC_CUSTOMER_SCHEMA
    SCHEMA_REGISTRY["generic_customer"] = GENERIC_CUSTOMER_SCHEMA
    return SCHEMA_REGISTRY.get(name.lower())
