from ape import project, networks, Contract
from decimal import Decimal
from datetime import datetime, timedelta
import sqlite3


def main():
    # Create the database and table if they don't exist
    create_database()

    # List of ERC-4626 vault addresses to analyze
    vault_addresses = [
        "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e",
        # Add more vault addresses
    ]

    # Time period for yield calculation (e.g., 30 days)
    days_ago = 30

    # Use the Ethereum mainnet provider with archive access
    with networks.ethereum.mainnet.use_provider("alchemy"):  # or "infura"
        for address in vault_addresses:
            vault = Contract(address)
            calculate_yield(vault, days_ago)


def calculate_yield(vault, days_ago):
    # Get the underlying asset and its decimals
    try:
        asset_address = vault.asset()
        asset = Contract(asset_address)
        decimals = asset.decimals()
    except Exception as e:
        print(f"Error fetching asset information for vault {vault.address}: {e}")
        return

    # Fetch current total assets and total supply adjusted for decimals
    try:
        total_assets = vault.totalAssets() / (10 ** decimals)
        total_supply = vault.totalSupply() / (10 ** decimals)
    except Exception as e:
        print(f"Error fetching current data for vault {vault.address}: {e}")
        return

    if total_supply == 0:
        print(f"Vault {vault.address}: No shares have been issued yet.")
        return

    current_aps = Decimal(total_assets) / Decimal(total_supply)

    # Fetch historical asset per share
    initial_aps = get_historical_aps(vault, days_ago, decimals)

    if initial_aps == 0:
        print(f"Vault {vault.address}: Unable to fetch historical data.")
        return

    # Calculate real yield
    real_yield = ((current_aps - initial_aps) / initial_aps) * 100

    # Insert data into the database
    insert_yield_data(
        vault_address=vault.address,
        asset_address=asset.address,
        days_ago=days_ago,
        initial_aps=float(initial_aps),
        current_aps=float(current_aps),
        real_yield=float(real_yield)
    )

    print(f"Vault: {vault.address}")
    print(f"Real Yield over {days_ago} days: {real_yield:.2f}%\n")


def get_historical_aps(vault, days_ago, decimals):
    # Calculate the target timestamp
    target_date = datetime.utcnow() - timedelta(days=days_ago)
    target_timestamp = int(target_date.timestamp())

    # Get the block number at the target timestamp
    block_number = get_block_number_at_timestamp(target_timestamp)
    if block_number is None:
        return 0

    # Fetch historical totalAssets and totalSupply at that block
    try:
        total_assets = vault.totalAssets(block_identifier=block_number) / (10 ** decimals)
        total_supply = vault.totalSupply(block_identifier=block_number) / (10 ** decimals)
    except Exception as e:
        print(f"Error fetching historical data for vault {vault.address}: {e}")
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


if __name__ == "__main__":
    main()
