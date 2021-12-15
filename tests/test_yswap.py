from brownie import Contract, Wei
from eth_abi import encode_abi
import pytest


def test_yswap(
    chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX,
    tokemak_manager, account_with_tokemak_rollover_role, utils, toke_token,
    toke_whale, trade_factory, sushi_swapper, ymechs_safe
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.sleep(1)
    strategy.harvest({"from": strategist})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount


    toke_token.transfer(strategy, Wei("200 ether"), {"from": toke_whale})
    strategy.sellRewards({"from": strategist})

    print(f"Executing trades...")
    for id in trade_factory.pendingTradesIds(strategy):
        trade = trade_factory.pendingTradesById(id).dict()
        token_in = trade["_tokenIn"]
        token_out = trade["_tokenOut"]
        print(f"Executing trade {id}, tokenIn: {token_in} -> tokenOut {token_out}")


        path = [toke_token.address, token.address]
        trade_data = encode_abi(["address[]"], [path])
        trade_factory.execute["uint256, address, uint, bytes"](id, sushi_swapper.address, Wei("0.1 ether"), trade_data, {"from": ymechs_safe})
