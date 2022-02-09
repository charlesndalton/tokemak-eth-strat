// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

interface ITradeFactoryPositionsHandler {
  struct Trade {
    uint256 _id;
    address _strategy;
    address _tokenIn;
    address _tokenOut;
    uint256 _amountIn;
    uint256 _deadline;
  }

  event TradeCreated(uint256 indexed _id, address _strategy, address _tokenIn, address _tokenOut, uint256 _amountIn, uint256 _deadline);

  event TradesCanceled(address indexed _strategy, uint256[] _ids);

  event TradesSwapperChanged(uint256[] _ids, address _newSwapper);

  event TradesMerged(uint256 indexed _anchorTrade, uint256[] _ids);

  function pendingTradesById(uint256)
    external
    view
    returns (
      uint256 _id,
      address _strategy,
      address _tokenIn,
      address _tokenOut,
      uint256 _amountIn,
      uint256 _deadline
    );

  function pendingTradesIds() external view returns (uint256[] memory _pendingIds);

  function pendingTradesIds(address _strategy) external view returns (uint256[] memory _pendingIds);

  function create(
    address _tokenIn,
    address _tokenOut,
    uint256 _amountIn,
    uint256 _deadline
  ) external returns (uint256 _id);

  function cancelPendingTrades(uint256[] calldata _ids) external;

  function mergePendingTrades(uint256 _anchorTradeId, uint256[] calldata _toMergeIds) external;
}
