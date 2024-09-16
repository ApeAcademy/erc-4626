import pytest
from ape import Contract


@pytest.fixture(scope="session")
def owner(accounts):
    return accounts[0]

@pytest.fixture(scope="session")
def receiver(accounts):
    return accounts[1]
@pytest.fixture(scope="session")
def asset():
    return Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F")  # DAI Ethereum Mainnet
@pytest.fixture(scope="session")
def token(owner, project, asset):
    return owner.deploy(project.Token, asset)

