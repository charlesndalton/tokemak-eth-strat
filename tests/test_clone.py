import pytest
from brownie import chain, Wei, reverts, Contract, ZERO_ADDRESS
import test_operation
import pytest


def test_clone_strategy(
    clone_strategy, chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
):
    clone_tx = strategy.cloneTokemakWeth(vault, strategist, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], strategy.abi
    )

    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # tend()
    strategy.tend()

def test_clone_of_clone(
    clone_strategy, vault, strategy, strategist
):
    clone_tx = strategy.cloneTokemakWeth(vault, strategist, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], strategy.abi
    )

    # should not clone a clone
    with reverts():
         cloned_strategy.cloneTokemakWeth(vault, strategist, {"from": strategist})



def test_double_initialize(
    clone_strategy, vault, strategy, strategist
):

    clone_tx = strategy.cloneTokemakWeth(vault, strategist, {"from": strategist})
    cloned_strategy = Contract.from_abi(
        "Strategy", clone_tx.events["Cloned"]["clone"], strategy.abi
    )

    # should not be able to call initialize twice
    with reverts("Strategy already initialized"):
        cloned_strategy.initialize(vault, strategist, {"from": strategist})
