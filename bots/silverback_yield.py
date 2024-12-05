import os

from ape import Contract, chain
from silverback import SilverbackBot


bot = SilverbackBot()

vault = Contract(os.environ["ERC4626_VAULT_ADDRESS"])

one_share = 10 ** vault.decimals()


@bot.on_(chain.blocks)
def update_shareprice(_):
    """
    Conver share to set price unit.
    """
    price = vault.convertToAssets(one_share) / one_share
    # Total number of shares in the vault divide by 
    # the current unit price of a share  = gwei 
    print(f"Price Event: {price}")
