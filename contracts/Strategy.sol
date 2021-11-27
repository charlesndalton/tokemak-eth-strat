// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import {
    BaseStrategy,
    StrategyParams
} from "@yearnvaults/contracts/BaseStrategy.sol";
import {
    SafeERC20,
    SafeMath,
    IERC20,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

// Import interfaces for many popular DeFi projects, or add your own!
//import "../interfaces/<protocol>/<Interface>.sol";

import "../interfaces/ISwap.sol";
import "../interfaces/tokemak/ILiquidityEthPool.sol";

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    ILiquidityEthPool private tokemakEthPool =
        ILiquidityEthPool(0xD3D13a578a53685B4ac36A1Bab31912D2B2A2F36);

    // From Tokemak docs: tABC tokens represent your underlying claim to the assets
    // you deposited into the token reactor, available to be redeemed 1:1 at any time
    IERC20 internal constant tWETH =
        IERC20(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);

    IERC20 internal constant TOKE =
        IERC20(0x2e9d63788249371f1DFC918a52f8d799F4a38C94);

    // Uniswap router to do TOKE->WETH
    ISwap internal constant router =
        ISwap(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);

    constructor(address _vault) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        // maxReportDelay = 6300;
        // profitFactor = 100;
        // debtThreshold = 0;
        want.safeApprove(address(tokemakEthPool), -1);
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external view override returns (string memory) {
        return "StrategyTokemakETH";
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        // 1 tWETH = 1 WETH *guaranteed*
        return twethBalance().add(wantBalance());
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        // How much do we owe to the vault?
        uint256 totalDebt = vault.strategies(address(this)).totalDebt;

        // Sell TOKE for `want`
        _sellRewards();

        uint256 totalAssets = estimatedTotalAssets();

        if (totalAssets >= totalDebt) {
            _profit = totalAssets.sub(totalDebt);
            _loss = 0;
        } else {
            _profit = 0;
            _loss = totalDebt.sub(totalAssets);
        }

        uint256 liquidAssets = wantBalance();

        _debtPayment = Math.min(_debtOutstanding, liquidAssets);

        // TODO: implement some asynchronous logic that frees up assets from Tokemak
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        // TODO: Do something to invest excess `want` tokens (from the Vault) into your positions
        // NOTE: Try to adjust positions so that `_debtOutstanding` can be freed up on *next* harvest (not immediately)

        uint256 wantBalance = wantBalance();

        if (wantBalance > _debtOutstanding) {
            tokemakEthPool.deposit(wantBalance.sub(_debtOutstanding));
        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        // TODO: Do stuff here to free up to `_amountNeeded` from all positions back into `want`
        // NOTE: Maintain invariant `want.balanceOf(this) >= _liquidatedAmount`
        // NOTE: Maintain invariant `_liquidatedAmount + _loss <= _amountNeeded`

        uint256 liquidAssets = wantBalance();

        if (liquidAssets >= _amountNeeded) {
            return (_amountNeeded, 0);
        }

        uint256 amountToWithdraw = _amountNeeded.sub(liquidAssets);

        // Cannot withdraw more than what we have in deposit
        amountToWithdraw = Math.min(
            amountToWithdraw,
            twethBalance()
        );

        // TODO: implement some asynchronous logic to withdraw `amountToWithdraw` from Tokemak
    }

    function liquidateAllPositions() internal override returns (uint256) {
        (_amountFreed, ) = liquidatePosition(estimatedTotalAssets());
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        // TODO: Transfer any non-`want` tokens to the new strategy
        // NOTE: `migrate` will automatically forward all `want` in this strategy to the new one
    }

    // Override this to add all tokens/tokenized positions this contract manages
    // on a *persistent* basis (e.g. not just for swapping back to want ephemerally)
    // NOTE: Do *not* include `want`, already included in `sweep` below
    //
    // Example:
    //
    //    function protectedTokens() internal override view returns (address[] memory) {
    //      address[] memory protected = new address[](3);
    //      protected[0] = tokenA;
    //      protected[1] = tokenB;
    //      protected[2] = tokenC;
    //      return protected;
    //    }
    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}

    /**
     * @notice
     *  Provide an accurate conversion from `_amtInWei` (denominated in wei)
     *  to `want` (using the native decimal characteristics of `want`).
     * @dev
     *  Care must be taken when working with decimals to assure that the conversion
     *  is compatible. As an example:
     *
     *      given 1e17 wei (0.1 ETH) as input, and want is USDC (6 decimals),
     *      with USDC/ETH = 1800, this should give back 1800000000 (180 USDC)
     *
     * @param _amtInWei The amount (in wei/1e-18 ETH) to convert to `want`
     * @return The amount in `want` of `_amtInEth` converted to `want`
     **/
    function ethToWant(uint256 _amtInWei)
        public
        view
        virtual
        override
        returns (uint256)
    {
        // TODO create an accurate price oracle
        return _amtInWei;
    }

    // ----------------- SUPPORT FUNCTIONS ----------

    function wantBalance()
        internal
        view
        returns (uint256)
    {
        return want.balanceOf(address(this));
    }

    function twethBalance()
        internal
        view
        returns (uint256)
    {
        return tWETH.balanceOf(address(this));
    }

    function tokeBalance()
        internal
        view
        returns (uint256)
    {
        return TOKE.balanceOf(address(this));
    }

    function _checkAllowance(
        address _contract,
        address _token,
        uint256 _amount
    ) internal {
        if (IERC20(_token).allowance(address(this), _contract) < _amount) {
            IERC20(_token).safeApprove(_contract, 0);
            IERC20(_token).safeApprove(_contract, type(uint256).max);
        }
    }

    // ----------------- TOKEN CONVERSIONS -----------------

    function _sellRewards()
        internal
    {
        _sellAForB(tokeBalance(), address(TOKE), address(want));
    }

    function getTokenOutPath(address _token_in, address _token_out)
        internal
        pure
        returns (address[] memory _path)
    {
        bool is_weth =
            _token_in == address(WETH) || _token_out == address(WETH);
        _path = new address[](is_weth ? 2 : 3);
        _path[0] = _token_in;

        if (is_weth) {
            _path[1] = _token_out;
        } else {
            _path[1] = address(WETH);
            _path[2] = _token_out;
        }
    }

    function _sellAForB(
        uint256 _amount,
        address tokenA,
        address tokenB
    ) internal {
        if (_amount == 0 || tokenA == tokenB) {
            return;
        }

        _checkAllowance(address(router), tokenA, _amount);
        router.swapExactTokensForTokens(
            _amount,
            0,
            getTokenOutPath(tokenA, tokenB),
            address(this),
            now
        );
    }
}
