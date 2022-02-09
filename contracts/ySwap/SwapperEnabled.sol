// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

import '@openzeppelin/contracts/token/ERC20/SafeERC20.sol';

import './TradeFactory.sol';

/*
 * SwapperEnabled Abstract
 */
abstract contract SwapperEnabled {
  using SafeERC20 for IERC20;

  address public tradeFactory;

  constructor(address _tradeFactory) public {
    _setTradeFactory(_tradeFactory);
  }

  // onlyMultisig:
  event TradeFactorySet(address indexed _tradeFactory);
  function _setTradeFactory(address _tradeFactory) internal {
    tradeFactory = _tradeFactory;
    emit TradeFactorySet(_tradeFactory);
  }

  // onlyMultisig or internal use:
  function _createTrade(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _deadline
  ) internal returns (uint256 _id) {
    IERC20(_tokenIn).safeIncreaseAllowance(tradeFactory, _amountIn);
    return ITradeFactoryPositionsHandler(tradeFactory).create(_tokenIn, _tokenOut, _amountIn, _deadline);
  }

  function _executeTrade(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _maxSlippage
  ) internal returns (uint256 _receivedAmount) {
    IERC20(_tokenIn).safeIncreaseAllowance(tradeFactory, _amountIn);
    return ITradeFactoryExecutor(tradeFactory).execute(_tokenIn, _tokenOut, _amountIn, _maxSlippage, '');
  }

  function _executeTrade(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _maxSlippage,
    bytes calldata _data
  ) internal returns (uint256 _receivedAmount) {
    IERC20(_tokenIn).safeIncreaseAllowance(tradeFactory, _amountIn);
    return ITradeFactoryExecutor(tradeFactory).execute(_tokenIn, _tokenOut, _amountIn, _maxSlippage, _data);
  }

  // onlyStrategist or multisig:
  function _cancelPendingTrades(uint256[] calldata _tradesIds) internal {
    for (uint256 i; i < _tradesIds.length; i++) {
      (, , address _tokenIn, , uint256 _amountIn, ) = ITradeFactoryPositionsHandler(tradeFactory).pendingTradesById(_tradesIds[i]);
      IERC20(_tokenIn).safeDecreaseAllowance(tradeFactory, _amountIn);
    }
    ITradeFactoryPositionsHandler(tradeFactory).cancelPendingTrades(_tradesIds);
  }

  function _tradeFactoryAllowance(address _token) internal view returns (uint256 _allowance) {
    return IERC20(_token).allowance(address(this), tradeFactory);
  }
}
