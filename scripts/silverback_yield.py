from silverback import SilverbackApp

from ape import Contract, chain, networks

import os


app = SilverbackApp()

with networks.ethereum.mainnet.use_provider("alchemy"):  # or "infura"
    vault = Contract(os.environ.get("ERC4626_VAULT_ADDRESS"))
one_share = 10 ** vault.decimals()


# Note: Use SQLModel
@app.on_(vault.Deposit)
def update_database_deposit(log):
    """
    Update database with deposit log.
    """
    print(f"Deposit Event: {log}")


@app.on_(vault.Withdraw)
def update_database_withdraw(log):
    """
    Update database with withdraw log
    """
    breakpoint()
    print(f"Withdraw Event: {log}")


@app.on_(chain.blocks)
def update_shareprice(_):
    """
    Add price to database (Update database)
    """
    price = vault.convertToShares(one_share) / one_share
    print(f"Price Event: {price}")