// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

interface ITradeFactoryExecutor {
  event SyncTradeExecuted(
    address indexed _strategy,
    address indexed _swapper,
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _maxSlippage,
    bytes _data,
    uint256 _receivedAmount
  );

  event AsyncTradeExecuted(uint256 indexed _id, uint256 _receivedAmount);

  event AsyncTradesMatched(
    uint256 indexed _firstTradeId,
    uint256 indexed _secondTradeId,
    uint256 _consumedFirstTrade,
    uint256 _consumedSecondTrade
  );

  event AsyncOTCTradesExecuted(uint256[] _ids, uint256 _rateTokenInToOut);

  event AsyncTradeExpired(uint256 indexed _id);

  event SwapperAndTokenEnabled(address indexed _swapper, address _token);

  function execute(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _maxSlippage,
    bytes calldata _data
  ) external returns (uint256 _receivedAmount);

  function execute(
    uint256 _id,
    address _swapper,
    uint256 _minAmountOut,
    bytes calldata _data
  ) external returns (uint256 _receivedAmount);

  function expire(uint256 _id) external returns (uint256 _freedAmount);

  function execute(uint256[] calldata _ids, uint256 _rateTokenInToOut) external;

  function execute(
    uint256 _firstTradeId,
    uint256 _secondTradeId,
    uint256 _consumedFirstTrade,
    uint256 _consumedSecondTrade
  ) external;
}
