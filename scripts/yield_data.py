from fastapi import FastAPI, HTTPException
from ape import project, networks, Contract
from decimal import Decimal
from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict
import sqlite3
import uvicorn


app = FastAPI(title="Vault Yields API")

database = "vault_yields.db"


@app.on_event("startup")
def startup_event():
    create_database()


class YieldBase(BaseModel):
    vault_address: str
    asset_address: str | None = None
    days_ago: int
    initial_aps: float
    current_aps: float
    real_yield: float


class YieldCreate(YieldBase):
    """
    Same as YieldBase
    """


class FetchYield(BaseModel):
    """
    Fetch the yield from ERC-4626.
    """
    vault_address: str
    num_days: int


class YieldInDB(YieldBase):
    id: int
    timestamp: datetime
    model_config: ConfigDict = ConfigDict(from_attributes=True)


def get_db_conn():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn


def create_yield(yield_data: YieldCreate) -> YieldInDB:
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO yields (
            vault_address,
            assett_address,
            days_ago,
            initial_aps,
            current_aps,
            real_yield,
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            yield_data.vault_address,
            yield_data.asset_address,
            yield_data.days_ago,
            yield_data.initial_aps,
            yield_data.current_aps,
            yield_data.real_yield,
        )
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return get_yield(new_id)


def get_yield(yield_id: int) -> YieldInDB | None:
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM yields WHERE id = ?", (yield_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return YieldInDB(**row)
    return None


def get_all_yields() -> list[YieldInDB]:
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM yields")
    rows = cursor.fetchall()
    conn.close()
    return [YieldInDB(**row) for row in rows]


def delete_yield(yield_id: int) -> bool:
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM yields WHERE id = ?", (yield_id,))
    conn.commit()
    affected_rows = cursor.rowcount
    conn.close()
    return affected_rows > 0


def fetch_yield(vault_address: str, num_days: int):
    """
    Get the yield for a vault address within a time period in days.

    Args:
        vault_address (str): The vault address you want to inspect.
        num_days (int): The time period to get the real yield.
    """
    # List of ERC-4626 vault addresses to analyze
    vault_addresses = [
        "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e",
        # Add more vault addresses
    ]

    # Time period for yield calculation (e.g., 30 days)
    days_ago = 365

    # Use the Ethereum mainnet provider with archive access
    with networks.ethereum.mainnet.use_provider("alchemy"):  # or "infura"
        vault = Contract(vault_address)
        calculate_yield(vault, num_days)


def calculate_yield(vault, days_ago):
    # Get the underlying asset and its decimals
    current_aps = 0
    try:
        asset_address = vault.symbol.contract.address
        asset = Contract(asset_address)
        decimals = asset.decimals()
    except Exception as e:
        print(f"Error fetching asset information for vault {vault.address}: {e}")
        return

    # Fetch current total assets and total supply adjusted for decimals
    try:
        total_assets = asset.balanceOf(vault.address) / (10 ** decimals)
        total_supply = vault.totalSupply() / (10 ** decimals)
    except Exception as e:
        print(f"Error fetching current data for vault {vault.address}: {e}")
        return

    if total_assets == 0:
        try:
            total_assets = vault.tokenPrice() / (10 ** decimals)
            current_aps = Decimal(total_assets)
        except Exception as e:
            print("Error fetching historical data for vault {vault.address}: {e}")
            print("No attribute 'tokenPrice' in vault.")
            return 0

    if total_supply == 0:
        print(f"Vault {vault.address}: No shares have been issued yet.")
        return

    if current_aps == 0:
        current_aps = Decimal(total_assets) / Decimal(total_supply)

    # Fetch historical asset per share
    initial_aps = get_historical_aps(vault, days_ago)

    if initial_aps == 0:
        print(f"Vault {vault.address}: Unable to fetch historical data.")
        return

    # Calculate real yield
    real_yield = ((current_aps - initial_aps) / initial_aps) * 100

    # Insert data into the database
    insert_yield_data(
        vault_address=vault.address,
        asset_address=asset_address,
        days_ago=days_ago,
        initial_aps=float(initial_aps),
        current_aps=float(current_aps),
        real_yield=float(real_yield)
    )

    print(f"Vault: {vault.address}")
    print(f"Real Yield over {days_ago} days: {real_yield:.2f}%\n")


def get_historical_aps(vault, days_ago):
    # Get the underlying asset
    try:
        asset_address = vault.symbol.contract.address
        asset = Contract(asset_address)
        decimals = asset.decimals()
    except Exception as e:
        print(f"Error fetching asset information for vault {vault.address}: {e}")
        return

    # Calculate the target timestamp
    target_date = datetime.utcnow() - timedelta(days=days_ago)
    target_timestamp = int(target_date.timestamp())

    # Get the block number at the target timestamp
    block_number = get_block_number_at_timestamp(target_timestamp)
    if block_number is None:
        return 0

    # Fetch historical totalAssets and totalSupply at that block
    try:
        total_assets = asset.balanceOf(vault.address, block_identifier=block_number) / (10 ** decimals)
        total_supply = vault.totalSupply(block_identifier=block_number) / (10 ** decimals)
    except Exception as e:
        print(f"Error fetching historical data for vault {vault.address}: {e}")
        return 0

    if total_assets == 0:
        try:
            total_assets = vault.tokenPrice(block_identifier=block_number) / (10 ** decimals)
            return Decimal(total_assets)
        except Exception as e:
            print("Error fetching historical data for vault {vault.address}: {e}")
            print("No attribute 'tokenPrice' in vault.")
            return 0

    if total_supply == 0:
        return 0

    return Decimal(total_assets) / Decimal(total_supply)


def get_block_number_at_timestamp(target_timestamp):
    provider = networks.provider

    latest_block = provider.get_block('latest')
    earliest_block = provider.get_block(0)

    if target_timestamp > latest_block.timestamp:
        print("Target timestamp is in the future.")
        return None

    # Binary search to find the closest block
    low = earliest_block.number
    high = latest_block.number

    while low <= high:
        mid = (low + high) // 2
        mid_block = provider.get_block(mid)
        mid_timestamp = mid_block.timestamp

        if mid_timestamp < target_timestamp:
            low = mid + 1
        elif mid_timestamp > target_timestamp:
            high = mid - 1
        else:
            # Exact match found
            return mid_block.number

    # No exact match, return the closest block before the target timestamp
    return high


def create_database():
    """
    Create the sqlite database to store yield data.
    """
    # Connect to the SQLite database (it will be created if it doesn't exist)
    conn = sqlite3.connect('vault_yields.db')
    cursor = conn.cursor()

    # Create a table to store yield data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS yields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vault_address TEXT NOT NULL,
            asset_address TEXT NOT NULL,
            days_ago INTEGER NOT NULL,
            initial_aps REAL NOT NULL,
            current_aps REAL NOT NULL,
            real_yield REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def insert_yield_data(vault_address, asset_address, days_ago, initial_aps, current_aps, real_yield):
    """
    Insert yield data into sqlite database
    """
    conn = sqlite3.connect('vault_yields.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO yields (vault_address, asset_address, days_ago, initial_aps, current_aps, real_yield)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (vault_address, asset_address, days_ago, initial_aps, current_aps, real_yield))

    conn.commit()
    conn.close()


def read_yield_data():
    """
    Reads yield data from sqlite database
    """
    conn = sqlite3.connect('vault_yields.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM yields')
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    conn.close()


def calculate_average_yield():
    """
    Calculates average yield among all vaults.
    """
    conn = sqlite3.connect('vault_yields.db')
    cursor = conn.cursor()

    cursor.execute('SELECT AVG(real_yield) FROM yields')
    average_yield = cursor.fetchone()[0]

    print(f"Average Real Yield: {average_yield:.2f}%")

    conn.close()


@app.post("/yields/", response_model=dict)
def create_yield_endpoint(yield_data: FetchYield):
    fetch_yield(yield_data.vault_address, yield_data.num_days)
    return {"request": "success"}


@app.get("/yields/{yield_id}", response_model=YieldInDB)
def read_yield(yield_id: int):
    db_yield = get_yield(yield_id)
    if db_yield is None:
        raise HTTPException(status_code=404, detail="Yield not found")
    return db_yield.dict()


@app.get("/yields/", response_model=list[YieldInDB])
def read_all_yields():
    yields = get_all_yields()
    return yields


@app.delete("/yields/{yield_id}")
def remove_yield(yield_id: int):
    success = delete_yield(yield_id)
    if not success:
        raise HTTPException(status_code=404, detail="Yield not found")
    return {"message": "Yield deleted successfully"}


if __name__ == "__main__":
    uvicorn.run("yield_data:app", host="0.0.0.0", port=8000, reload=True)

