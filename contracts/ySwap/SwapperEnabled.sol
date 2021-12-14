// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

import '@openzeppelin/contracts/token/ERC20/SafeERC20.sol';
import './ITradeFactoryPositionsHandler.sol';
import './ITradeFactoryExecutor.sol';

interface ISwapperEnabled {
  event TradeFactorySet(address indexed _tradeFactory);

  function tradeFactory() external returns (address _tradeFactory);

  function setTradeFactory(address _tradeFactory) external;

  function createTrade(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _maxSlippage,
    uint256 _deadline
  ) external returns (uint256 _id);

  function executeTrade(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _maxSlippage
  ) external returns (uint256 _receivedAmount);

  function executeTrade(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn
  ) external returns (uint256 _receivedAmount);

  function executeTrade(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _maxSlippage,
    bytes calldata _data
  ) external returns (uint256 _receivedAmount);


  function cancelPendingTrades(uint256[] calldata _pendingTrades) external;
}

/*
 * SwapperEnabled Abstract
 */
abstract contract SwapperEnabled is ISwapperEnabled {
  using SafeERC20 for IERC20;

  address public override tradeFactory;

  constructor(address _tradeFactory) public {
    _setTradeFactory(_tradeFactory);
  }

  // onlyMultisig:
  function _setTradeFactory(address _tradeFactory) internal {
    tradeFactory = _tradeFactory;
    emit TradeFactorySet(_tradeFactory);
  }

  function _createTrade(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _maxSlippage,
    uint256 _deadline
  ) internal returns (uint256 _id) {
    IERC20(_tokenIn).safeIncreaseAllowance(tradeFactory, _amountIn);
    return ITradeFactoryPositionsHandler(tradeFactory).create(_tokenIn, _tokenOut, _amountIn, _maxSlippage, _deadline);
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
  function _cancelPendingTrades(uint256[] calldata _pendingTrades) internal {
    for (uint256 i; i < _pendingTrades.length; i++) {
      _cancelPendingTrade(_pendingTrades[i]);
    }
  }

  function _cancelPendingTrade(uint256 _pendingTradeId) internal {
    (, , , address _tokenIn, , uint256 _amountIn, , ) = ITradeFactoryPositionsHandler(tradeFactory).pendingTradesById(_pendingTradeId);
    IERC20(_tokenIn).safeDecreaseAllowance(tradeFactory, _amountIn);
    ITradeFactoryPositionsHandler(tradeFactory).cancelPending(_pendingTradeId);
  }

  function _tradeFactoryAllowance(address _token) internal view returns (uint256 _allowance) {
    return IERC20(_token).allowance(address(this), tradeFactory);
  }
}
