import brownie
from brownie import Contract
import pytest


def test_operation(
    chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, 
    tokemak_manager, account_with_tokemak_rollover_role, utils
):
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

    utils.make_funds_withdrawable_from_tokemak(utils, strategy, amount, chain, tokemak_manager, account_with_tokemak_rollover_role)

    # withdrawal
    vault.withdraw({"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )

# emergency exit test commented out for now as we don't have an emergency exit path other than waiting for funds

# def test_emergency_exit(
#     chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
# ):
#     # Deposit to the vault
#     token.approve(vault.address, amount, {"from": user})
#     vault.deposit(amount, {"from": user})
#     chain.sleep(1)
#     strategy.harvest()
#     assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

#     # set emergency and exit
#     strategy.setEmergencyExit()
#     chain.sleep(1)
#     strategy.harvest()
#     assert strategy.estimatedTotalAssets() < amount

# commented out profitable harvest because we'll be claiming rewards manually so no profits reported by strategy

# def test_profitable_harvest(
#     chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
# ):
#     # Deposit to the vault
#     token.approve(vault.address, amount, {"from": user})
#     vault.deposit(amount, {"from": user})
#     assert token.balanceOf(vault.address) == amount

#     # Harvest 1: Send funds through the strategy
#     chain.sleep(1)
#     strategy.harvest()
#     assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

#     # TODO: Add some code before harvest #2 to simulate earning yield

#     # Harvest 2: Realize profit
#     chain.sleep(1)
#     strategy.harvest()
#     chain.sleep(3600 * 6)  # 6 hrs needed for profits to unlock
#     chain.mine(1)
#     profit = token.balanceOf(vault.address)  # Profits go to vault
#     # TODO: Uncomment the lines below
#     # assert token.balanceOf(strategy) + profit > amount
#     # assert vault.pricePerShare() > before_pps


def test_change_debt(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX,
    tokemak_manager, account_with_tokemak_rollover_role, utils
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    half = int(amount / 2)
    sixty_percent = int(amount * .6)
    fourty_percent = int(amount * .4)

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 10_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # In order to pass this tests, you will need to implement prepareReturn.
    # TODO: uncomment the following lines.
    vault.updateStrategyDebtRatio(strategy.address, 6_000, {"from": gov})

    utils.make_funds_withdrawable_from_tokemak(utils, strategy, fourty_percent, chain, tokemak_manager, account_with_tokemak_rollover_role)

    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == sixty_percent


def test_sweep(gov, vault, strategy, token, user, amount, toke_token, toke_whale):
    # Strategy want token doesn't work
    token.transfer(strategy, amount, {"from": user})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})

    # TODO: If you add protected tokens to the strategy.
    # Protected token doesn't work
    # with brownie.reverts("!protected"):
    #     strategy.sweep(strategy.protectedToken(), {"from": gov})

    toke_amount = 10 * (10 ** 18)

    before_balance = toke_token.balanceOf(gov)
    toke_token.transfer(strategy, toke_amount, {"from": toke_whale})
    assert toke_whale.address != strategy.want()
    assert toke_token.balanceOf(user) == 0
    strategy.sweep(toke_token, {"from": gov})
    assert toke_token.balanceOf(gov) == toke_amount + before_balance


def test_triggers(
    chain, gov, vault, strategy, token, amount, user, weth, weth_amout, strategist
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest()

    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)
