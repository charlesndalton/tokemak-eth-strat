import pytest


def test_revoke_strategy_from_vault(
    chain, token, vault, strategy, amount, user, gov, RELATIVE_APPROX,
    tokemak_manager, account_with_tokemak_rollover_role, utils
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    vault.revokeStrategy(strategy.address, {"from": gov})
    utils.make_funds_withdrawable_from_tokemak(strategy, amount)
    strategy.harvest()
    assert pytest.approx(token.balanceOf(vault.address), rel=RELATIVE_APPROX) == amount


def test_revoke_strategy_from_strategy(
    chain, token, vault, strategy, amount, gov, user, RELATIVE_APPROX,
    tokemak_manager, account_with_tokemak_rollover_role, utils
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    strategy.setEmergencyExit()
    utils.make_funds_withdrawable_from_tokemak(strategy, amount)
    strategy.harvest()
    assert pytest.approx(token.balanceOf(vault.address), rel=RELATIVE_APPROX) == amount
