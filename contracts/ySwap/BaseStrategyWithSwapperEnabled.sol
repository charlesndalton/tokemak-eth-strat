// SPDX-License-Identifier: MIT

pragma solidity 0.6.12;

import {
    BaseStrategy
} from "@yearnvaults/contracts/BaseStrategy.sol";
import './SwapperEnabled.sol';

abstract contract BaseStrategyWithSwapperEnabled is BaseStrategy, SwapperEnabled {
    uint256 constant defaultMaxSlippage = 100; // default of 1%

    constructor(address _vault, address _tradeFactory) BaseStrategy(_vault) SwapperEnabled(_tradeFactory) public {
    }

    // SwapperEnabled onlyGovernance methods
    function setTradeFactory(address _tradeFactory) external override onlyGovernance {
        _setTradeFactory(_tradeFactory);
    }
    
    function createTrade(
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn,
        uint256 _maxSlippage,
        uint256 _deadline
    ) external override onlyGovernance returns (uint256 _id) {
        return _createTrade(_tokenIn, _tokenOut, _amountIn, _maxSlippage, _deadline);
    }
    
    function executeTrade(
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn,
        uint256 _maxSlippage
    ) external override returns (uint256 _receivedAmount) {
        return _executeTrade(_tokenIn, _tokenOut, _amountIn, _maxSlippage);
    }
    
    function executeTrade(
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn
    ) public override returns (uint256 _receivedAmount) {
        return _executeTrade(_tokenIn, _tokenOut, _amountIn, defaultMaxSlippage);
    }
    
    function executeTrade(
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn,
        uint256 _maxSlippage,
        bytes calldata _data
    ) external override returns (uint256 _receivedAmount) {
        return _executeTrade(_tokenIn, _tokenOut, _amountIn, _maxSlippage, _data);
    }
    
    function cancelPendingTrades(uint256[] calldata _pendingTrades) external override onlyAuthorized {
        _cancelPendingTrades(_pendingTrades);
    }
}
