import os

from ape import Contract, chain, networks
from silverback import SilverbackApp

from sqlmodel import SQLModel, Field, create_engine, Session

sqlite_url = os.environ.get("DATABASE_URL")

app = SilverbackApp()

with networks.ethereum.mainnet.use_provider("alchemy"):  # or "infura"
    vault = Contract(os.environ.get("ERC4626_VAULT_ADDRESS"))

one_share = 10 ** vault.decimals()
engine = create_engine(sqlite_url, echo=True)


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    block: str
    sender: str
    owner: str
    assets: int
    shares: int
    timestamp: int
    transaction_hash: str
    transaction_type: str


def create_transaction(log):
    transaction = Transaction(
        block=log.block_number,
        sender=log.sender,
        owner=log.args.owner,
        assets=log.args.assets,
        shares=log.args.shares,
        timestamp=log.timestamp,
        transaction_hash=log.transaction_hash,
        transaction_type="deposit",
    )
    with Session(engine) as session:
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
    return transaction


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@app.on_worker_startup()
def handle_on_worker_startup(state):
    create_db_and_tables()


# Note: Use SQLModel
@app.on_(vault.Deposit)
def update_database_deposit(log):
    """
    Update database with deposit log.
    """
    print(f"Deposit Event: {log}")
    return create_transaction(log)


@app.on_(vault.Withdraw)
def update_database_withdraw(log):
    """
    Update database with withdraw log
    """
    print(f"Withdraw Event: {log}")
    return create_transaction(log)


@app.on_(chain.blocks)
def update_shareprice(_):
    """
    Add price to database (Update database)
    """
    price = vault.convertToShares(one_share) / one_share
    print(f"Price Event: {price}")
