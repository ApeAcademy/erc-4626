# @version 0.3.7

interface IERC4626:
    def asset() -> address: view
    def totalAssets() -> uint256: view
    def totalSupply() -> uint256: view
    def decimals() -> uint8: view
    def balanceOf(account: address) -> uint256: view

