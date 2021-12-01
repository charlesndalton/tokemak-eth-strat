import pytest
from brownie import config
from brownie import Contract


@pytest.fixture
def gov(accounts):
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


@pytest.fixture
def token():
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # this should be the address of the ERC-20 used by the strategy/vault (wETH)
    yield Contract(token_address)


@pytest.fixture
def amount(accounts, token, user, weth_whale):
    amount = 10 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate the weth whale to use its funds.
    token.transfer(user, amount, {"from": weth_whale})
    yield amount


@pytest.fixture
def weth():
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    yield Contract(token_address)

@pytest.fixture
def tweth():
    token_address = "0xD3D13a578a53685B4ac36A1Bab31912D2B2A2F36"
    yield Contract(token_address)

@pytest.fixture
def toke_token():
    token_address = "0x2e9d63788249371f1DFC918a52f8d799F4a38C94"
    yield Contract(token_address)

@pytest.fixture
def tokemak_manager():
    token_address = "0xA86e412109f77c45a3BC1c5870b880492Fb86A14"
    yield Contract(token_address)

@pytest.fixture
def weth_whale(accounts):
    # AAVE wETH pool
    yield accounts.at("0x030bA81f1c18d280636F32af80b9AAd02Cf0854e", force=True)

@pytest.fixture
def toke_whale(accounts):
    # tokemak treasury
    yield accounts.at("0x8b4334d4812c530574bd4f2763fcd22de94a969b", force=True)

@pytest.fixture
def account_with_tokemak_rollover_role(accounts):
    # this account should have the role to allow them to call the Tokemak rollover contract
    yield accounts.at("0x9e0bcE7ec474B481492610eB9dd5D69EB03718D5", force=True)

@pytest.fixture
def weth_amout(user, weth):
    weth_amout = 10 ** weth.decimals()
    user.transfer(weth, weth_amout)
    yield weth_amout


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian, management)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    yield vault

@pytest.fixture
def clone_strategy(vault, strategy, strategist):
    clone_tx = strategy.cloneTokemakWeth(vault, strategist, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], strategy.abi
    )
    yield cloned_strategy

@pytest.fixture
def strategy(strategist, keeper, vault, Strategy, gov):
    strategy = strategist.deploy(Strategy, vault)
    strategy.setKeeper(keeper)
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    yield strategy


@pytest.fixture(scope="session")
def RELATIVE_APPROX():
    yield 1e-5

@pytest.fixture
def utils():
    return Utils

class Utils:
    @staticmethod
    def mock_one_day_passed(chain, tokemak_manager, account_with_tokemak_rollover_role):
        chain.sleep(3600 * 24)
        # current cycle duration is 6200 blocks; can be found here:
        # https://etherscan.io/address/0xa86e412109f77c45a3bc1c5870b880492fb86a14#readProxyContract
        chain.mine(6300)
        tokemak_manager.completeRollover("DmTzdi7eC9SM5FaZCzaMpfwpuTt2gXZircVsZUA3DPXWqv", {"from": account_with_tokemak_rollover_role})
    
    @staticmethod
    def make_funds_withdrawable_from_tokemak(self, strategy, amount, chain, tokemak_manager, account_with_tokemak_rollover_role):
        strategy.requestWithdrawal(amount)

        # Tokemak has 1 day timelock for withdrawals
        self.mock_one_day_passed(chain, tokemak_manager, account_with_tokemak_rollover_role)
