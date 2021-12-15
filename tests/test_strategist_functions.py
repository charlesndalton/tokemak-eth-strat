import brownie
from brownie import Contract
import pytest

def test_request_withdrawal(
    chain, vault, strategy, strategist, amount, token, user, tweth, 
    tokemak_weth_pool, utils, RELATIVE_APPROX
):
    amount_to_withdraw = amount / 2

    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    strategy.harvest()

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    assert pytest.approx(tweth.balanceOf(strategy.address), rel=RELATIVE_APPROX) == amount

    (block_number_when_withdrawable, requested_withdraw_amount) = tokemak_weth_pool.requestedWithdrawals(strategy.address)

    assert pytest.approx(requested_withdraw_amount, rel=RELATIVE_APPROX) == 0

    strategy.requestWithdrawal(amount_to_withdraw)

    (block_number_when_withdrawable, requested_withdraw_amount) = tokemak_weth_pool.requestedWithdrawals(strategy.address)

    assert pytest.approx(requested_withdraw_amount, rel=RELATIVE_APPROX) == amount_to_withdraw

    utils.mock_one_day_passed()

    assert chain.height > block_number_when_withdrawable

# at the moment, not adding any test for 'claimRewards,' given that it is just a wrapper of tokemak function and there's an off-chain step which is hard to mock

def test_sell_rewards(
    chain, strategy, toke_token, strategist, toke_whale, weth, RELATIVE_APPROX
):
    amount_of_toke_to_sell = 100
    amount_of_weth_in_strategy_before_sale = weth.balanceOf(strategy.address)

    assert pytest.approx(toke_token.balanceOf(strategy.address), rel=RELATIVE_APPROX) == 0

    toke_token.transfer(strategy, amount_of_toke_to_sell, {"from": toke_whale})

    assert pytest.approx(toke_token.balanceOf(strategy.address), rel=RELATIVE_APPROX) == amount_of_toke_to_sell

    strategy.sellRewards({"from": strategist})
    chain.mine()
    amount_of_weth_in_strategy_after_sale = weth.balanceOf(strategy.address)

    assert pytest.approx(toke_token.balanceOf(strategy.address), rel=RELATIVE_APPROX) == 0

    assert amount_of_weth_in_strategy_before_sale < amount_of_weth_in_strategy_after_sale


