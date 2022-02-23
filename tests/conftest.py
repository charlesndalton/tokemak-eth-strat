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
    token.transfer(user, amount, {"from": weth_whale, "gas_price": "0"})
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
    address = "0xA86e412109f77c45a3BC1c5870b880492Fb86A14"
    yield Contract(address)

@pytest.fixture
def tokemak_eth_pool():
    address = "0xD3D13a578a53685B4ac36A1Bab31912D2B2A2F36"
    yield Contract(address)

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
def tokemak_multisig(accounts):
    # this account should be the owner of the eth pool
    yield accounts.at("0x90b6c61b102ea260131ab48377e143d6eb3a9d4b", force=True)

@pytest.fixture
def weth_amount(user, weth):
    weth_amount = 10 ** weth.decimals()
    user.transfer(weth, weth_amount)
    yield weth_amount


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian, management, {"from": gov})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    yield vault


@pytest.fixture
def trade_factory():
    yield Contract("0x99d8679bE15011dEAD893EB4F5df474a4e6a8b29")

@pytest.fixture
def ymechs_safe():
    yield Contract("0x2C01B4AD51a67E2d8F02208F54dF9aC4c0B778B6")


# @pytest.fixture
# def sushi_swapper(trade_factory, ymechs_safe):
#     swapper =  Contract("0x55dcee9332848AFcF660CE6a2116D83Dd7a71B60")
#     trade_factory.addSwappers([swapper], {"from": ymechs_safe})
#
#     yield swapper

@pytest.fixture(scope="module")
def sushiswap_router(Contract):
    yield Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")

@pytest.fixture(scope="module")
def multicall_swapper(interface):
    yield interface.MultiCallOptimizedSwapper(
        #"0xceB202F25B50e8fAF212dE3CA6C53512C37a01D2"
        "0xB2F65F254Ab636C96fb785cc9B4485cbeD39CDAA"
    )

@pytest.fixture
def strategy(strategist, keeper, vault, trade_factory, Strategy, gov, ymechs_safe):
    strategy = strategist.deploy(Strategy, vault, trade_factory)
    strategy.setKeeper(keeper, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})


    trade_factory.grantRole(trade_factory.STRATEGY(), strategy, {"from": ymechs_safe, "gas_price": "0 gwei"})
    yield strategy

# strategy with no debt allocation
@pytest.fixture
def standalone_strategy(strategist, keeper, vault, trade_factory, Strategy, gov):
    strategy = strategist.deploy(Strategy, vault, trade_factory)
    strategy.setKeeper(keeper)
    yield strategy

@pytest.fixture(scope="session")
def RELATIVE_APPROX():
    yield 1e-5

@pytest.fixture
def tokemak_weth_pool():
    yield Contract("0xD3D13a578a53685B4ac36A1Bab31912D2B2A2F36")

@pytest.fixture
def utils(chain, tokemak_manager, account_with_tokemak_rollover_role):
    return Utils(chain, tokemak_manager, account_with_tokemak_rollover_role)

class Utils:
    def __init__(self, chain, tokemak_manager, account_with_tokemak_rollover_role):
        self.chain = chain
        self.tokemak_manager = tokemak_manager
        self.account_with_tokemak_rollover_role = account_with_tokemak_rollover_role

    def mock_one_day_passed(self):
        self.chain.sleep(3600 * 24)
        cycle_duration = self.tokemak_manager.getCycleDuration()
        self.chain.mine(cycle_duration + 100)
        self.tokemak_manager.completeRollover("DmTzdi7eC9SM5FaZCzaMpfwpuTt2gXZircVsZUA3DPXWqv", {"from": self.account_with_tokemak_rollover_role})

    def make_funds_withdrawable_from_tokemak(self, strategy, amount):
        strategy.requestWithdrawal(amount)

        # Tokemak has 1 day timelock for withdrawals
        self.mock_one_day_passed()

    def move_user_funds_to_vault(self, user, vault, token, amount):
        token.approve(vault.address, amount, {"from": user})
        vault.deposit(amount, {"from": user})
        assert token.balanceOf(vault.address) == amount
