import pytest
from brownie import chain, Wei, reverts, Contract, ZERO_ADDRESS

import pytest


def test_clone_strategy(
    chain, accounts, token, vault, user, standalone_strategy, strategist, amount, RELATIVE_APPROX, tweth, gov
):
  
    clone_tx = standalone_strategy.cloneTokemakWeth(vault, strategist, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], standalone_strategy.abi
    )

    vault.addStrategy(cloned_strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})

    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.sleep(1)
    cloned_strategy.harvest({"from": strategist})
    assert pytest.approx(cloned_strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    assert pytest.approx(tweth.balanceOf(cloned_strategy), rel=RELATIVE_APPROX) == amount

    # tend()
    cloned_strategy.tend({"from": strategist})

def test_clone_of_clone(
    vault, strategy, strategist
):
    clone_tx = strategy.cloneTokemakWeth(vault, strategist, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], strategy.abi
    )

    # should not clone a clone
    with reverts():
         cloned_strategy.cloneTokemakWeth(vault, strategist, {"from": strategist})



def test_double_initialize(
    vault, strategy, strategist
):

    clone_tx = strategy.cloneTokemakWeth(vault, strategist, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], strategy.abi
    )

    # should not be able to call initialize twice
    with reverts("Strategy already initialized"):
        cloned_strategy.initialize(vault, strategist, {"from": strategist})
