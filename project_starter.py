import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################
#
# Architecture (framework: smolagents)
# ------------------------------------
#   1. orchestrator_agent  - customer-facing coordinator; delegates to the workers below
#                            and writes the customer reply
#   2. inventory_agent     - catalog matching, stock checks, supplier lead times, restocking
#   3. quoting_agent       - pricing, bulk discounts, comparison with historical quotes
#   4. sales_agent         - finalizes orders and records sales transactions
#   5. business_advisor_agent - reviews the financial position after the run and
#                               recommends operational improvements (internal only)
#
# Workers share a per-request "case file" (blackboard pattern): the inventory assessment
# and the quote are attached to the active case, so data handed from one agent to the
# next never has to be re-typed by an LLM and cannot drift.
# All money/stock calculations happen inside deterministic tools; the LLM decides
# which tool to call and writes the explanations.

import json
import re
import uuid

from smolagents import OpenAIServerModel, ToolCallingAgent, tool
from smolagents.models import ChatMessage, MessageRole
from smolagents.monitoring import LogLevel


# Set up and load your env parameters and instantiate your model.

dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

MODEL_ID = os.getenv("AGENT_MODEL_ID", "gpt-4.1-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openai.vocareum.com/v1")

model = OpenAIServerModel(
    model_id=MODEL_ID,
    api_base=OPENAI_BASE_URL,
    api_key=os.getenv("UDACITY_OPENAI_API_KEY"),
    temperature=0.1,
)

# ---------------------------------------------------------------------------
# Business rules (internal - never shown to customers)
# ---------------------------------------------------------------------------

# Our purchase cost from the supplier, as a fraction of the catalog (list) price.
SUPPLIER_COST_RATIO = 0.6

# Restocking is refused if it would push cash below this safety reserve.
MINIMUM_CASH_RESERVE = 2000.0

# Days needed to ship goods we already hold in our own warehouse.
WAREHOUSE_SHIPPING_DAYS = 1

# Bulk discount tiers: (minimum total units in the order, discount rate, label).
BULK_DISCOUNT_TIERS = [
    (10000, 0.15, "15% bulk discount for orders of 10,000+ units"),
    (5000, 0.12, "12% bulk discount for orders of 5,000+ units"),
    (1000, 0.10, "10% bulk discount for orders of 1,000+ units"),
    (500, 0.05, "5% bulk discount for orders of 500+ units"),
]

# Deterministic guardrail for item mapping: paper sizes we do not stock and products we never carry.
# Applied to the customer's wording even if the LLM proposed a catalog match.
UNSTOCKED_SIZE_PATTERN = re.compile(r"\bA(0|1|2|3|5|6)\b", re.IGNORECASE)
NOT_CARRIED_KEYWORDS = ("balloon", "ticket", "cardboard", "poster board frame")

# Quick lookup of the full product catalog by exact item name.
CATALOG = {item["item_name"]: item for item in paper_supplies}

# In-memory registries used to hand work from one agent to the next by id.
ASSESSMENTS: Dict[str, Dict] = {}
QUOTES: Dict[str, Dict] = {}

# The case file for the customer request currently being processed.
ACTIVE_CASE: Dict[str, Union[str, None]] = {
    "case_id": None, "request_date": None, "deadline": None, "assessment_id": None, "quote_id": None,
}


def open_new_case(request_date: str, deadline: str) -> str:
    """Start a fresh case file for a new customer request and return its id."""
    ACTIVE_CASE.update(case_id=new_reference_id("CASE"), request_date=request_date, deadline=deadline,
                       assessment_id=None, quote_id=None)
    return ACTIVE_CASE["case_id"]


def get_active_quote():
    """Return (quote_id, quote) for the active case, or (None, None) if no quote exists yet."""
    quote_id = ACTIVE_CASE.get("quote_id")
    return quote_id, QUOTES.get(quote_id) if quote_id else None


def new_reference_id(prefix: str) -> str:
    """Create a short unique reference id (e.g. 'ASM-3F9A1C') that an LLM cannot guess."""
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


def reset_registries() -> None:
    """Clear the assessment and quote registries (used when the database is re-initialised)."""
    ASSESSMENTS.clear()
    QUOTES.clear()
    ACTIVE_CASE.update(case_id=None, request_date=None, deadline=None, assessment_id=None, quote_id=None)


def trace(agent_name: str, message: str) -> None:
    """Print a one-line progress trace so the run shows which agent is doing what."""
    print(f"    [{agent_name}] {message}")


def normalize_date(date_value: str) -> str:
    """Return the YYYY-MM-DD part of an ISO date string, raising ValueError when invalid."""
    return datetime.fromisoformat(str(date_value).strip().split("T")[0]).strftime("%Y-%m-%d")


def add_days(date_str: str, days: int) -> str:
    """Add a number of days to an ISO date string and return the new ISO date."""
    return (datetime.fromisoformat(date_str) + timedelta(days=days)).strftime("%Y-%m-%d")


def get_min_stock_level(item_name: str) -> int:
    """Return the configured minimum stock level for an item (0 if it is not a stocked item)."""
    result = pd.read_sql(
        "SELECT min_stock_level FROM inventory WHERE item_name = :item_name",
        db_engine,
        params={"item_name": item_name},
    )
    return int(result["min_stock_level"].iloc[0]) if not result.empty else 0


def current_stock_of(item_name: str, as_of_date: str) -> int:
    """Wrap get_stock_level() and return the stock level as a plain integer."""
    stock_df = get_stock_level(item_name, as_of_date)
    return int(stock_df["current_stock"].iloc[0] or 0)


def plan_line_fulfillment(item_name: str, quantity: int, request_date: str, deadline: str) -> Dict:
    """
    Decide how (and whether) a single order line can be delivered by the customer's deadline.

    Uses get_stock_level() for the warehouse position and get_supplier_delivery_date() for
    the supplier lead time of any restock that would be needed.

    Returns a dict with a status of AVAILABLE_FROM_STOCK, RESTOCK_REQUIRED or UNAVAILABLE.
    """
    plan = {"item_name": item_name, "quantity": int(quantity)}

    if item_name not in CATALOG:
        plan.update(status="UNAVAILABLE", reason="This product is not part of our catalog.")
        return plan
    if quantity <= 0:
        plan.update(status="UNAVAILABLE", reason="The requested quantity is not valid.")
        return plan

    stock = current_stock_of(item_name, request_date)
    min_level = get_min_stock_level(item_name)
    plan.update(unit_price=CATALOG[item_name]["unit_price"], stock_on_hand=stock)

    warehouse_delivery = add_days(request_date, WAREHOUSE_SHIPPING_DAYS)

    if stock >= quantity:
        if warehouse_delivery > deadline:
            plan.update(
                status="UNAVAILABLE",
                reason=f"Earliest possible delivery is {warehouse_delivery}, after the requested date {deadline}.",
            )
        else:
            plan.update(status="AVAILABLE_FROM_STOCK", restock_quantity=0, delivery_date=warehouse_delivery)
        return plan

    # Not enough stock: order the shortfall plus a buffer back up to the minimum stock level.
    shortfall = quantity - stock
    restock_quantity = shortfall + min_level
    supplier_eta = get_supplier_delivery_date(request_date, restock_quantity)
    delivery_date = max(supplier_eta, warehouse_delivery)

    if delivery_date > deadline:
        plan.update(
            status="UNAVAILABLE",
            reason=(
                f"We cannot have the full quantity ready in time: the earliest possible delivery "
                f"is {delivery_date}, which is after the requested date {deadline}."
            ),
        )
        return plan

    restock_cost = round(restock_quantity * CATALOG[item_name]["unit_price"] * SUPPLIER_COST_RATIO, 2)
    if get_cash_balance(request_date) - restock_cost < MINIMUM_CASH_RESERVE:
        plan.update(
            status="UNAVAILABLE",
            reason="We cannot source this volume in time for the requested date.",
        )
        return plan

    plan.update(status="RESTOCK_REQUIRED", restock_quantity=restock_quantity, delivery_date=delivery_date)
    return plan


def select_bulk_discount(total_units: int):
    """Return (rate, label) for the bulk discount tier matching the total number of units."""
    for min_units, rate, label in BULK_DISCOUNT_TIERS:
        if total_units >= min_units:
            return rate, label
    return 0.0, "No bulk discount (orders of 500+ units qualify for volume pricing)"


def price_lines(lines: List[Dict]) -> Dict:
    """Price a list of {item_name, quantity, unit_price} lines and apply the bulk discount tier."""
    priced_lines = []
    subtotal = 0.0
    for line in lines:
        line_total = round(line["quantity"] * line["unit_price"], 2)
        subtotal += line_total
        priced_lines.append({**line, "line_total": line_total})

    total_units = sum(line["quantity"] for line in lines)
    discount_rate, discount_label = select_bulk_discount(total_units)
    discount_amount = round(subtotal * discount_rate, 2)
    total = round(subtotal - discount_amount, 2)

    # Courtesy rounding (as in our historical quotes): drop the cents on larger orders.
    if total >= 50:
        total = float(int(total))

    return {
        "lines": priced_lines,
        "total_units": total_units,
        "subtotal": round(subtotal, 2),
        "discount_rate": discount_rate,
        "discount_label": discount_label,
        "discount_amount": discount_amount,
        "total": total,
    }


def parse_requested_lines(lines_json: str) -> List[Dict]:
    """Parse the JSON list of requested lines produced by the inventory agent."""
    text_value = lines_json.strip()
    # Accept a JSON list wrapped in markdown code fences.
    text_value = re.sub(r"^```(json)?|```$", "", text_value).strip()
    parsed = json.loads(text_value)
    if isinstance(parsed, dict):
        parsed = parsed.get("lines", [parsed])
    return parsed


"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""


# Tools for inventory agent

@tool
def list_catalog_with_stock(as_of_date: str) -> str:
    """
    List every product in the company catalog with its list price and current stock on hand.
    Use this to translate a customer's wording into exact catalog item names.

    Args:
        as_of_date: Date in YYYY-MM-DD format for the stock snapshot.
    """
    as_of_date = normalize_date(as_of_date)
    stock_snapshot = get_all_inventory(as_of_date)
    trace("Inventory Agent", f"Loaded catalog and stock snapshot as of {as_of_date}")
    rows = []
    for item in paper_supplies:
        name = item["item_name"]
        rows.append(
            f"- {name} | category: {item['category']} | price: ${item['unit_price']:.2f}/unit "
            f"| in stock: {int(stock_snapshot.get(name, 0))}"
        )
    return "Product catalog (exact item names):\n" + "\n".join(rows)


@tool
def check_item_stock(item_name: str, as_of_date: str) -> str:
    """
    Check the stock level of one catalog item on a given date.

    Args:
        item_name: Exact catalog item name, e.g. 'Glossy paper'.
        as_of_date: Date in YYYY-MM-DD format.
    """
    as_of_date = normalize_date(as_of_date)
    if item_name not in CATALOG:
        return f"'{item_name}' is not an exact catalog item name. Use list_catalog_with_stock first."
    stock = current_stock_of(item_name, as_of_date)
    min_level = get_min_stock_level(item_name)
    trace("Inventory Agent", f"Stock check: {item_name} = {stock} units")
    return f"{item_name}: {stock} units in stock on {as_of_date} (minimum stock level: {min_level})."


@tool
def check_supplier_delivery(quantity: int, order_date: str) -> str:
    """
    Estimate when the supplier would deliver a replenishment order of the given size.

    Args:
        quantity: Number of units that would be ordered from the supplier.
        order_date: Date the supplier order would be placed, YYYY-MM-DD.
    """
    eta = get_supplier_delivery_date(normalize_date(order_date), int(quantity))
    return f"A supplier order of {quantity} units placed on {order_date} would arrive on {eta}."


@tool
def assess_order_availability(request_date: str, delivery_deadline: str, requested_lines_json: str) -> str:
    """
    Assess every requested line of a customer order against stock, supplier lead times and the
    customer's delivery deadline. The assessment is saved to the shared case file, where the
    quoting agent picks it up.

    Args:
        request_date: Date of the customer's request, YYYY-MM-DD.
        delivery_deadline: Date the customer needs the goods by, YYYY-MM-DD.
        requested_lines_json: JSON list of objects with keys "requested" (customer wording),
            "item_name" (exact catalog name, or null if we do not carry it) and "quantity"
            (integer, in catalog units, e.g. sheets). Example:
            [{"requested": "200 sheets A4 glossy", "item_name": "Glossy paper", "quantity": 200},
             {"requested": "100 balloons", "item_name": null, "quantity": 100}]
    """
    # The case file (set by the orchestrator) is authoritative for dates.
    request_date = ACTIVE_CASE.get("request_date") or normalize_date(request_date)
    deadline = ACTIVE_CASE.get("deadline") or normalize_date(delivery_deadline)
    try:
        requested_lines = parse_requested_lines(requested_lines_json)
    except (ValueError, TypeError) as error:
        return f"Could not read requested_lines_json ({error}). Provide a valid JSON list."

    assessed_lines = []
    for line in requested_lines:
        requested_text = str(line.get("requested") or line.get("item_name") or "item")
        item_name = line.get("item_name")
        try:
            quantity = int(float(line.get("quantity") or 0))
        except (TypeError, ValueError):
            quantity = 0

        not_carried_reason = None
        if UNSTOCKED_SIZE_PATTERN.search(requested_text):
            not_carried_reason = "We only stock this paper in standard A4/letter size; this paper size is not carried."
        elif any(keyword in requested_text.lower() for keyword in NOT_CARRIED_KEYWORDS):
            not_carried_reason = "We do not carry this product."

        if not_carried_reason:
            plan = {"item_name": None, "quantity": quantity, "status": "UNAVAILABLE", "reason": not_carried_reason}
        elif not item_name:
            plan = {
                "item_name": None,
                "quantity": quantity,
                "status": "UNAVAILABLE",
                "reason": "We do not carry this product.",
            }
        else:
            plan = plan_line_fulfillment(item_name, quantity, request_date, deadline)
        plan["requested"] = requested_text
        assessed_lines.append(plan)

    assessment_id = new_reference_id("ASM")
    ASSESSMENTS[assessment_id] = {
        "request_date": request_date,
        "deadline": deadline,
        "lines": assessed_lines,
    }
    ACTIVE_CASE["assessment_id"] = assessment_id
    ACTIVE_CASE["quote_id"] = None

    report_lines = [f"Assessment {assessment_id} (request {request_date}, deadline {deadline}):"]
    for plan in assessed_lines:
        label = f"{plan['requested']} -> {plan['item_name'] or 'not carried'} x {plan['quantity']}"
        if plan["status"] == "UNAVAILABLE":
            report_lines.append(f"- {label}: UNAVAILABLE. {plan['reason']}")
        else:
            report_lines.append(
                f"- {label}: {plan['status']} (stock {plan['stock_on_hand']}, "
                f"deliverable by {plan['delivery_date']})"
            )
    trace("Inventory Agent", f"Created {assessment_id}: " + ", ".join(
        f"{p['item_name'] or p['requested']}={p['status']}" for p in assessed_lines))
    return "\n".join(report_lines)


@tool
def prepare_stock_for_quote() -> str:
    """
    Make sure enough stock exists for every line of the current case's quote by placing supplier
    replenishment orders (stock_orders transactions) where needed. The reorder quantity
    covers the shortfall plus a buffer back to the item's minimum stock level.
    """
    quote_id, quote = get_active_quote()
    if quote is None:
        return "No quote exists for the current request yet; the quoting agent must create one first."
    if quote["status"] == "fulfilled":
        return f"{quote_id} is already fulfilled; no stock preparation needed."

    order_date = quote["request_date"]
    messages = []
    for line in quote["lines"]:
        item_name = line["item_name"]
        stock = current_stock_of(item_name, order_date)
        if stock >= line["quantity"]:
            messages.append(f"- {item_name}: {stock} in stock, no reorder needed.")
            continue

        reorder_quantity = line["quantity"] - stock + get_min_stock_level(item_name)
        cost = round(reorder_quantity * line["unit_price"] * SUPPLIER_COST_RATIO, 2)
        cash = get_cash_balance(order_date)
        if cash - cost < MINIMUM_CASH_RESERVE:
            messages.append(f"- {item_name}: reorder of {reorder_quantity} refused (cash reserve).")
            continue

        eta = get_supplier_delivery_date(order_date, reorder_quantity)
        transaction_id = create_transaction(item_name, "stock_orders", reorder_quantity, cost, order_date)
        trace("Inventory Agent", f"Restocked {reorder_quantity} x {item_name} (txn {transaction_id}, ETA {eta})")
        messages.append(f"- {item_name}: ordered {reorder_quantity} units from supplier, arriving {eta}.")

    quote["status"] = "stock_prepared"
    return f"Stock preparation for {quote_id}:\n" + "\n".join(messages)


@tool
def review_reorder_needs(as_of_date: str) -> str:
    """
    Review all stocked items and list those below their minimum stock level, with a suggested
    reorder quantity and supplier ETA. Read-only: does not place orders.

    Args:
        as_of_date: Date in YYYY-MM-DD format.
    """
    as_of_date = normalize_date(as_of_date)
    stock_snapshot = get_all_inventory(as_of_date)
    stocked_items = pd.read_sql("SELECT item_name, min_stock_level FROM inventory", db_engine)
    low_items = []
    for _, row in stocked_items.iterrows():
        stock = int(stock_snapshot.get(row["item_name"], 0))
        if stock < row["min_stock_level"]:
            suggested = int(row["min_stock_level"]) * 2 - stock
            eta = get_supplier_delivery_date(as_of_date, suggested)
            low_items.append(f"- {row['item_name']}: {stock} < min {row['min_stock_level']}; "
                             f"suggest ordering {suggested} (ETA {eta})")
    return "Items below minimum stock:\n" + ("\n".join(low_items) if low_items else "None - all stocked items are healthy.")


# Tools for quoting agent

@tool
def find_similar_past_quotes(search_terms: List[str]) -> str:
    """
    Search historical quotes for similar requests to benchmark pricing and discount wording.

    Args:
        search_terms: One to three short keywords, e.g. ["cardstock"] or ["glossy", "ceremony"].
    """
    matches = [m for m in search_quote_history(search_terms, limit=8) if (m["total_amount"] or 0) > 0][:5]
    # Fall back to single-term searches if the combined search is too narrow.
    if not matches and len(search_terms) > 1:
        for term in search_terms:
            matches = [m for m in search_quote_history([term], limit=5) if (m["total_amount"] or 0) > 0][:3]
            if matches:
                break
    trace("Quoting Agent", f"Found {len(matches)} historical quotes for {search_terms}")
    if not matches:
        return "No similar historical quotes found."
    summaries = []
    for match in matches:
        summaries.append(
            f"- ${match['total_amount']} | {match['order_size']} {match['event_type']} order "
            f"({match['job_type']}): {str(match['quote_explanation'])[:220]}"
        )
    return "Similar historical quotes:\n" + "\n".join(summaries)


@tool
def create_quote() -> str:
    """
    Build a priced quote from the inventory assessment in the current case file. Only lines that
    can be delivered on time are quoted; bulk discounts are applied automatically by total units.
    Returns the quote reference plus the full price breakdown.
    """
    assessment_id = ACTIVE_CASE.get("assessment_id")
    assessment = ASSESSMENTS.get(assessment_id) if assessment_id else None
    if assessment is None:
        return "No inventory assessment exists for the current request; the inventory agent must assess it first."

    # Idempotency: return the existing quote if this assessment was already quoted.
    for existing_id, existing in QUOTES.items():
        if existing["assessment_id"] == assessment_id:
            return (f"Quote {existing_id} already exists for {assessment_id}: total ${existing['total']:.2f}, "
                    f"{existing['discount_label']}, delivery {existing['delivery_date']}.")

    quotable = [
        {"item_name": p["item_name"], "quantity": p["quantity"], "unit_price": p["unit_price"],
         "delivery_date": p["delivery_date"]}
        for p in assessment["lines"] if p["status"] != "UNAVAILABLE"
    ]
    excluded = [p for p in assessment["lines"] if p["status"] == "UNAVAILABLE"]
    excluded_text = "\n".join(f"- {p['requested']}: {p['reason']}" for p in excluded) or "- none"

    if not quotable:
        return ("No quote created: none of the requested items can be supplied by the deadline.\n"
                f"Excluded lines:\n{excluded_text}")

    pricing = price_lines(quotable)
    delivery_date = max(line["delivery_date"] for line in quotable)
    quote_id = new_reference_id("Q")
    ACTIVE_CASE["quote_id"] = quote_id
    QUOTES[quote_id] = {
        "assessment_id": assessment_id,
        "request_date": assessment["request_date"],
        "deadline": assessment["deadline"],
        "delivery_date": delivery_date,
        "status": "open",
        "excluded": excluded,
        **pricing,
    }

    line_text = "\n".join(
        f"- {l['item_name']}: {l['quantity']} x ${l['unit_price']:.2f} = ${l['line_total']:.2f}"
        for l in pricing["lines"]
    )
    trace("Quoting Agent", f"Created {quote_id}: total ${pricing['total']:.2f} ({pricing['discount_label']})")
    return (
        f"Quote {quote_id}\n{line_text}\n"
        f"Subtotal: ${pricing['subtotal']:.2f}\n"
        f"Discount: {pricing['discount_label']} (-${pricing['discount_amount']:.2f})\n"
        f"Total: ${pricing['total']:.2f}\n"
        f"Estimated delivery: {delivery_date} (requested by {assessment['deadline']})\n"
        f"Excluded lines:\n{excluded_text}"
    )


# Tools for ordering agent

@tool
def get_quote_details() -> str:
    """
    Show the stored details and status of the current case's quote before finalizing it.
    """
    quote_id, quote = get_active_quote()
    if quote is None:
        return "No quote exists for the current request."
    lines = "\n".join(f"- {l['item_name']}: {l['quantity']} units, ${l['line_total']:.2f}" for l in quote["lines"])
    return (f"{quote_id} status={quote['status']}, total=${quote['total']:.2f}, "
            f"delivery {quote['delivery_date']}\n{lines}")


@tool
def finalize_sale() -> str:
    """
    Finalize the order for the current case's quote: verify stock for each line and record a
    'sales' transaction per line at the quoted (discounted) price. Lines without sufficient stock
    are not sold and are reported back. Run this only after the inventory agent has prepared stock.
    """
    quote_id, quote = get_active_quote()
    if quote is None:
        return "No quote exists for the current request, so there is nothing to finalize."
    if quote["status"] == "fulfilled":
        return f"{quote_id} was already fulfilled."

    sale_date = quote["request_date"]
    sold_lines, unsold_lines = [], []
    for line in quote["lines"]:
        if current_stock_of(line["item_name"], sale_date) >= line["quantity"]:
            sold_lines.append(line)
        else:
            unsold_lines.append(line)

    if not sold_lines:
        return (f"Sale NOT completed for {quote_id}: insufficient stock for all lines. "
                "Ask the inventory agent to run prepare_stock_for_quote first.")

    # Re-price the lines actually sold so the invoice matches what ships.
    final_pricing = price_lines(sold_lines)
    discount_factor = (final_pricing["total"] / final_pricing["subtotal"]) if final_pricing["subtotal"] else 1.0

    transaction_ids = []
    for line in final_pricing["lines"]:
        line_revenue = round(line["line_total"] * discount_factor, 2)
        transaction_ids.append(
            create_transaction(line["item_name"], "sales", line["quantity"], line_revenue, sale_date)
        )

    order_number = f"SO-{transaction_ids[0]:05d}"
    quote.update(status="fulfilled", final_total=final_pricing["total"], order_number=order_number)
    trace("Sales Agent", f"Order {order_number} recorded: ${final_pricing['total']:.2f} "
          f"(txns {transaction_ids}); cash now ${get_cash_balance(sale_date):,.2f}")

    unsold_text = "\n".join(f"- {l['item_name']}: could not be allocated" for l in unsold_lines) or "- none"
    sold_text = "\n".join(f"- {l['item_name']}: {l['quantity']} units" for l in final_pricing["lines"])
    return (
        f"SALE COMPLETED. Order {order_number} for {quote_id}.\n{sold_text}\n"
        f"Invoice total: ${final_pricing['total']:.2f} ({final_pricing['discount_label']})\n"
        f"Delivery date: {quote['delivery_date']}\nNot fulfilled:\n{unsold_text}"
    )


# Tools for business advisor agent (internal reporting only)

@tool
def get_financial_report(as_of_date: str) -> str:
    """
    Produce the company financial report (cash, inventory value, total assets, low-stock items
    and top-selling products) as of a date. Internal use only.

    Args:
        as_of_date: Date in YYYY-MM-DD format.
    """
    report = generate_financial_report(normalize_date(as_of_date))
    low_stock = [
        f"{i['item_name']} ({int(i['stock'])})" for i in report["inventory_summary"]
        if i["stock"] < get_min_stock_level(i["item_name"])
    ]
    top = [f"{p['item_name']}: {int(p['total_units'] or 0)} units, ${p['total_revenue']:.2f}"
           for p in report["top_selling_products"] if p["item_name"]]
    return (
        f"Financial report as of {report['as_of_date']}\n"
        f"Cash balance: ${report['cash_balance']:,.2f}\n"
        f"Inventory value: ${report['inventory_value']:,.2f}\n"
        f"Total assets: ${report['total_assets']:,.2f}\n"
        f"Stocked items below minimum level: {', '.join(low_stock) or 'none'}\n"
        f"Top sellers: {'; '.join(top) or 'none'}"
    )


@tool
def get_sales_activity_summary() -> str:
    """
    Summarize the quoting activity of this session: how many quotes were issued and fulfilled,
    revenue, discounts granted and the most common reasons customer lines were declined.
    """
    fulfilled = [q for q in QUOTES.values() if q["status"] == "fulfilled"]
    declined_reasons: Dict[str, int] = {}
    declined_items: Dict[str, int] = {}
    for assessment in ASSESSMENTS.values():
        for line in assessment["lines"]:
            if line["status"] == "UNAVAILABLE":
                reason = line["reason"].split(",")[0][:80]
                declined_reasons[reason] = declined_reasons.get(reason, 0) + 1
                declined_items[line["requested"]] = declined_items.get(line["requested"], 0) + 1
    revenue = sum(q.get("final_total", 0) for q in fulfilled)
    discounts = sum(q["discount_amount"] for q in fulfilled)
    return json.dumps({
        "requests_assessed": len(ASSESSMENTS),
        "quotes_issued": len(QUOTES),
        "orders_fulfilled": len(fulfilled),
        "revenue_from_orders": round(revenue, 2),
        "discounts_granted": round(discounts, 2),
        "supplier_cost_ratio": SUPPLIER_COST_RATIO,
        "declined_line_reasons": declined_reasons,
        "declined_items": dict(sorted(declined_items.items(), key=lambda kv: -kv[1])[:10]),
    }, indent=2)


# Set up your agents and create an orchestration agent that will manage them.

INVENTORY_INSTRUCTIONS = """You are the Inventory Agent of Beaver's Choice Paper Company.
Your job: map customer wording to exact catalog items, check stock and supplier lead times,
and replenish stock. You never price orders and never record sales.

When asked to ASSESS a request:
1. Call list_catalog_with_stock with the request date given in the task to see exact item names.
2. Keep each line's "requested" text close to the customer's wording (include sizes such as A3/A4/A5).
   Map each requested product to ONE exact catalog item name, converting units to catalog units:
   1 ream = 500 sheets; "packets/boxes of N" = packets x N. Mapping rules:
   - Plain/white/printer/printing/copy paper -> "Standard copy paper"; "A4 paper"/"A4 white paper" -> "A4 paper".
   - "A4 glossy" -> "Glossy paper", "A4 matte" -> "Matte paper", "A4 recycled" -> "Recycled paper".
   - Any cardstock (white, colored, heavy, recycled) -> "Cardstock". Colorful/assorted colored paper -> "Colored paper".
   - Poster boards / posters 24x36 -> "Large poster paper (24x36 inches)"; colorful poster paper -> "Poster paper".
   - Streamers -> "Party streamers"; washi tape -> "Decorative adhesive tape (washi tape)"; napkins -> "Paper napkins";
     paper cups -> "Paper cups"; paper plates -> "Paper plates"; flyers -> "Flyers"; envelopes -> "Envelopes".
   - Our papers come only in standard letter/A4 size: A3 or A5 sized paper is NOT carried (item_name null).
   - Products not in the catalog (balloons, tickets, cardboard, etc.) -> item_name null. Never invent names.
3. Call assess_order_availability ONCE with ALL lines (including unavailable ones). It saves the
   assessment to the shared case file.
4. Report the per-line result exactly as the tool returned it.

When asked to PREPARE STOCK: call ONLY prepare_stock_for_quote() (do not re-assess) and report the result.
"""

QUOTING_INSTRUCTIONS = """You are the Quoting Agent of Beaver's Choice Paper Company.
The inventory assessment for the current request is already in the shared case file.
1. Call find_similar_past_quotes with 1-2 keywords for the main product or event to benchmark.
2. Call create_quote() once. Prices and discounts are computed by the tool; never change them.
3. Report every priced line, subtotal, the discount applied with its reason, total,
   estimated delivery date, the excluded lines with their reasons, and one sentence explaining how the
   price compares with similar past orders (e.g. consistent with past bulk discounts). If create_quote says no quote
   could be created, say "NO QUOTE" clearly and list the excluded lines with reasons. Never mention
   costs, margins or the company's cash position.
"""

SALES_INSTRUCTIONS = """You are the Sales Agent of Beaver's Choice Paper Company.
The quote for the current request is in the shared case file. Call finalize_sale() once to record the sale.
Return the order number, items sold, invoice total and delivery date, plus any lines not fulfilled.
If the tool says stock is insufficient, report that clearly.
"""

REPLY_WRITER_INSTRUCTIONS = """You are the customer service voice of Beaver's Choice Paper Company.
Write a polite, concise reply to the customer using ONLY the facts provided. Include:
- the order number (if an order was placed) and a line for each item supplied: quantity, catalog product,
  unit price and line total; then subtotal, discount (and why it applies) and the total;
- the confirmed delivery date and whether it meets the requested date;
- every requested item that could not be supplied, each with its reason in plain language,
  and an offer to help with alternatives (e.g. a later delivery date or a similar product we carry).
Never reveal internal information: no cash balances, supplier costs, margins, stock counts, reorder
activity, internal reference ids (ASM-..., Q-..., CASE-...), tool or agent names, or error messages.
Do not ask the customer to confirm: orders in this channel are placed directly. Sign off as
"Beaver's Choice Paper Company - Customer Service". Plain text only, no markdown tables."""

MONTH_DATE_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2}),?\s+(\d{4})", re.IGNORECASE)


def extract_request_date(request_text: str) -> str:
    """Read the '(Date of request: YYYY-MM-DD)' suffix added by the test harness (today if missing)."""
    match = re.search(r"Date of request:\s*(\d{4}-\d{2}-\d{2})", request_text)
    return match.group(1) if match else datetime.now().strftime("%Y-%m-%d")


def extract_delivery_deadline(request_text: str, request_date: str) -> str:
    """Find the customer's requested delivery date ('by April 15, 2025'); default: request date + 7 days."""
    for month, day, year in MONTH_DATE_PATTERN.findall(request_text):
        try:
            candidate = datetime.strptime(f"{month} {day} {year}", "%B %d %Y").strftime("%Y-%m-%d")
        except ValueError:
            continue
        if candidate >= request_date:
            return candidate
    return add_days(request_date, 7)


class OrchestratorAgent:
    """
    Customer-facing orchestrator. It owns the workflow for every request:

      1. open a case file (request date + deadline parsed deterministically)
      2. delegate ASSESS to the inventory agent
      3. delegate QUOTE to the quoting agent        (only if something can be supplied)
      4. delegate PREPARE STOCK to the inventory agent
      5. delegate FINALIZE to the sales agent
      6. write the customer reply with the LLM from the verified case-file facts

    The control flow is explicit code (not free-form LLM planning) so money-moving steps run
    exactly once and in the right order; guardrails re-run a step's tool directly if a worker
    agent finishes without performing it.
    """

    name = "orchestrator_agent"

    def __init__(self, inventory_agent, quoting_agent, sales_agent, llm_model):
        self.inventory_agent = inventory_agent
        self.quoting_agent = quoting_agent
        self.sales_agent = sales_agent
        self.llm_model = llm_model

    def delegate(self, agent: ToolCallingAgent, task: str) -> str:
        """Run a worker agent on a task and return its answer as text (errors are captured)."""
        trace("Orchestrator", f"-> {agent.name}: {task.splitlines()[0][:90]}")
        try:
            return str(agent.run(task, reset=True))
        except Exception as error:
            trace("Orchestrator", f"{agent.name} failed: {error}")
            return f"(agent error: {error})"

    def handle_request(self, request_text: str) -> str:
        """Process one customer request end-to-end and return the customer-facing reply."""
        request_date = extract_request_date(request_text)
        deadline = extract_delivery_deadline(request_text, request_date)
        case_id = open_new_case(request_date, deadline)
        trace("Orchestrator", f"Opened {case_id} (request {request_date}, deadline {deadline})")

        # Step 1 - inventory assessment (retry once if the agent did not save one).
        assess_task = (f"ASSESS this customer request.\nRequest date: {request_date}\n"
                       f"Delivery deadline: {deadline}\nCustomer request:\n{request_text}")
        assessment_notes = self.delegate(self.inventory_agent, assess_task)
        if not ACTIVE_CASE["assessment_id"]:
            assessment_notes = self.delegate(self.inventory_agent, assess_task)
        assessment = ASSESSMENTS.get(ACTIVE_CASE["assessment_id"] or "")
        if assessment is None:
            return ("Thank you for your request. We could not process it automatically; a member of our "
                    "sales team will contact you shortly.")

        # Step 2 - quote, only when at least one line can be supplied.
        pricing_notes = ""
        if any(line["status"] != "UNAVAILABLE" for line in assessment["lines"]):
            pricing_notes = self.delegate(
                self.quoting_agent,
                "Create the quote for the current request and explain the pricing versus similar past orders.\n"
                f"Customer request (for choosing history search keywords):\n{request_text}")
            if not ACTIVE_CASE["quote_id"]:
                trace("Orchestrator", "Guardrail: quoting agent did not create a quote; creating it directly.")
                create_quote()

        # Steps 3 & 4 - prepare stock, then finalize the sale.
        quote_id, quote = get_active_quote()
        if quote is not None:
            self.delegate(self.inventory_agent, "PREPARE STOCK for the current quote.")
            if quote["status"] == "open":
                trace("Orchestrator", "Guardrail: stock not prepared by inventory agent; preparing directly.")
                prepare_stock_for_quote()
            self.delegate(self.sales_agent, "Finalize the sale for the current quote.")
            if quote["status"] != "fulfilled":
                trace("Orchestrator", "Guardrail: sale not finalized by sales agent; finalizing directly.")
                finalize_sale()

        # Step 5 - customer reply.
        return self.write_customer_reply(request_text, assessment, quote, pricing_notes)

    def build_case_facts(self, assessment: Dict, quote) -> str:
        """Summarize the verified case-file facts the reply writer is allowed to use."""
        facts = [f"Requested delivery date: {assessment['deadline']}"]
        if quote is not None and quote["status"] == "fulfilled":
            facts.append(f"Order placed. Order number: {quote['order_number']}")
            for line in quote["lines"]:
                facts.append(f"Supplied: {line['quantity']} x {line['item_name']} at ${line['unit_price']:.2f} "
                             f"= ${line['line_total']:.2f}")
            facts.append(f"Subtotal: ${quote['subtotal']:.2f}")
            facts.append(f"Discount: {quote['discount_label']} (-${quote['discount_amount']:.2f})")
            if quote.get("final_total") is not None and quote["final_total"] != quote["total"]:
                facts.append(f"Total charged: ${quote['final_total']:.2f}")
            else:
                facts.append(f"Total charged: ${quote['total']:.2f}")
            facts.append(f"Delivery date: {quote['delivery_date']}")
        else:
            facts.append("No order could be placed.")
        for line in assessment["lines"]:
            if line["status"] == "UNAVAILABLE":
                facts.append(f"NOT supplied: {line['requested']} - {line['reason']}")
        return "\n".join(facts)

    def write_customer_reply(self, request_text, assessment, quote, pricing_notes) -> str:
        """Use the LLM to turn the verified facts into a customer reply (template fallback on error)."""
        facts = self.build_case_facts(assessment, quote)
        prompt = (f"{REPLY_WRITER_INSTRUCTIONS}\n\nCustomer request:\n{request_text}\n\n"
                  f"Verified facts:\n{facts}\n\nPricing notes from the quoting team (use for the discount "
                  f"rationale only):\n{pricing_notes[:1500]}")
        try:
            message = ChatMessage(role=MessageRole.USER, content=[{"type": "text", "text": prompt}])
            reply = self.llm_model.generate([message]).content
            if reply and reply.strip():
                return reply.strip()
        except Exception as error:
            trace("Orchestrator", f"Reply writer failed ({error}); using template reply.")
        return ("Thank you for your request.\n" + facts +
                "\n\nBeaver's Choice Paper Company - Customer Service")


def build_agents() -> Dict:
    """Create the orchestrator, the three worker agents and the business advisor agent (5 agents)."""
    inventory_agent = ToolCallingAgent(
        tools=[list_catalog_with_stock, check_item_stock, check_supplier_delivery,
               assess_order_availability, prepare_stock_for_quote, review_reorder_needs],
        model=model,
        name="inventory_agent",
        description="Inventory specialist: catalog mapping, stock checks, supplier lead times and restocking.",
        instructions=INVENTORY_INSTRUCTIONS,
        max_steps=8,
        max_tool_threads=1,
        verbosity_level=LogLevel.OFF,
    )
    quoting_agent = ToolCallingAgent(
        tools=[find_similar_past_quotes, create_quote],
        model=model,
        name="quoting_agent",
        description="Pricing specialist: quotes with bulk discounts benchmarked against historical quotes.",
        instructions=QUOTING_INSTRUCTIONS,
        max_steps=5,
        max_tool_threads=1,
        verbosity_level=LogLevel.OFF,
    )
    sales_agent = ToolCallingAgent(
        tools=[get_quote_details, finalize_sale],
        model=model,
        name="sales_agent",
        description="Sales specialist: finalizes quotes into orders and records sales transactions.",
        instructions=SALES_INSTRUCTIONS,
        max_steps=4,
        max_tool_threads=1,
        verbosity_level=LogLevel.OFF,
    )
    orchestrator_agent = OrchestratorAgent(inventory_agent, quoting_agent, sales_agent, model)
    business_advisor_agent = ToolCallingAgent(
        tools=[get_financial_report, get_sales_activity_summary, review_reorder_needs],
        model=model,
        name="business_advisor_agent",
        instructions=("You are the internal Business Advisor of Beaver's Choice Paper Company. Analyse the "
                      "financial report and sales activity, then give 3-5 concrete, prioritized recommendations "
                      "to improve revenue and operational efficiency (assortment, pricing, stock policy). "
                      "Ground every recommendation in the numbers you retrieved."),
        max_steps=5,
        max_tool_threads=1,
        verbosity_level=LogLevel.OFF,
    )
    return {
        "orchestrator": orchestrator_agent,
        "inventory": inventory_agent,
        "quoting": quoting_agent,
        "sales": sales_agent,
        "advisor": business_advisor_agent,
    }


def handle_customer_request(orchestrator_agent: OrchestratorAgent, request_text: str) -> str:
    """Send one customer request through the orchestrator and return the customer-facing reply."""
    try:
        return orchestrator_agent.handle_request(request_text)
    except Exception as error:  # Never leak internal errors to the customer.
        print(f"    [Orchestrator] internal error: {error}")
        return ("Thank you for your request. We were unable to complete your order automatically; "
                "a member of our sales team will contact you shortly.")


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():

    print("Initializing Database...")
    init_database(db_engine)
    reset_registries()
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############

    agents = build_agents()
    orchestrator_agent = agents["orchestrator"]

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        response = handle_customer_request(orchestrator_agent, request_with_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)

    # Internal review by the business advisor agent (not customer-facing).
    print("\n===== BUSINESS ADVISOR RECOMMENDATIONS =====")
    try:
        advice = agents["advisor"].run(
            f"Review the business as of {final_date} and recommend improvements.", reset=True
        )
        print(advice)
        with open("business_advisor_report.md", "w") as advisor_file:
            advisor_file.write(f"# Business Advisor Recommendations ({final_date})\n\n{advice}\n")
    except Exception as error:
        print(f"Business advisor unavailable: {error}")

    return results


if __name__ == "__main__":
    results = run_test_scenarios()
