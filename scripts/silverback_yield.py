from silverback import SilverbackApp

from ape import Contract, chain

import os


app = SilverbackApp()

vault = Contract(os.environ("ERC4626_VAULT_ADDRESS"))
one_share = 10 ** vault.decimals()


# Note: Use SQLModel
@app.on_(vault.Deposit)
def update_database_deposit(log):
    """
    Update database with deposit log.
    """
    pass


@app.on_(vault.Withdraw)
def update_database_withdraw(log):
    """
    Update database with withdraw log
    """
    pass


@app.on_(chain.blocks)
def update_shareprice():
    """
    Add price to database (Update database)
    """
    price = vault.convertToShares(one_share) / one_share

