import pytest
from brownie import chain, Wei, reverts, Contract, ZERO_ADDRESS

import pytest
import web3

def test_clone_strategy(
    chain, accounts, token, vault, user, standalone_strategy, strategist, amount,
    RELATIVE_APPROX, tweth, gov, trade_factory, utils, ymechs_safe
):
    prepare_trade_factory_role(standalone_strategy, trade_factory, ymechs_safe, utils)
    clone_tx = standalone_strategy.cloneTokemakWeth(vault, strategist, trade_factory, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], standalone_strategy.abi
    )
    vault.addStrategy(cloned_strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})

    # Deposit to the vault
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    utils.move_user_funds_to_vault(user, vault, token, amount)

    # harvest
    chain.sleep(1)
    cloned_strategy.harvest({"from": strategist})
    assert pytest.approx(cloned_strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    assert pytest.approx(tweth.balanceOf(cloned_strategy), rel=RELATIVE_APPROX) == amount

    # tend()
    cloned_strategy.tend({"from": strategist})

def test_clone_of_clone(
    vault, strategy, strategist, trade_factory, ymechs_safe, utils
):
    prepare_trade_factory_role(strategy, trade_factory, ymechs_safe, utils)
    clone_tx = strategy.cloneTokemakWeth(vault, strategist, trade_factory, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], strategy.abi
    )

    predicted_clone_address = utils.mk_contract_address(strategy.address, 2) # 2 in this case because you want to pre-grant role to a clone of a clone
    trade_factory.grantRole(trade_factory.STRATEGY(), predicted_clone_address, {"from": ymechs_safe, "gas_price": "0 gwei"})
    # should not clone a clone
    with reverts():
        cloned_strategy.cloneTokemakWeth(vault, strategist, trade_factory, {"from": strategist})



def test_double_initialize(
    vault, strategy, strategist, trade_factory, ymechs_safe, utils
):
    prepare_trade_factory_role(strategy, trade_factory, ymechs_safe, utils)
    clone_tx = strategy.cloneTokemakWeth(vault, strategist, trade_factory, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], strategy.abi
    )

    # should not be able to call initialize twice
    with reverts("Strategy already initialized"):
        cloned_strategy.initialize(vault, strategist, trade_factory, {"from": strategist})

def prepare_trade_factory_role(strategy, trade_factory, ymechs_safe, utils):
    predicted_clone_address = utils.mk_contract_address(strategy.address, 1) # this will be 1 because you can't clone a clone
    trade_factory.grantRole(trade_factory.STRATEGY(), predicted_clone_address, {"from": ymechs_safe, "gas_price": "0 gwei"})
