// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

import './TradeFactoryPositionsHandler.sol';
import './TradeFactoryExecutor.sol';

interface ITradeFactory is ITradeFactoryExecutor, ITradeFactoryPositionsHandler {}
