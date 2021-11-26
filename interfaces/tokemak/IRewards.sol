pragma solidity 0.6.11;

interface IRewards {

    event SignerSet(address newSigner);
    event Claimed(uint256 cycle, address recipient, uint256 amount);

    struct EIP712Domain {
        string name;
        string version;
        uint256 chainId;
        address verifyingContract;
    }

    struct Recipient {
        uint256 chainId;
        uint256 cycle;
        address wallet;
        uint256 amount;
    }

    function getClaimableAmount(Recipient calldata recipient) external view returns (uint256);

    function claim(
        Recipient calldata recipient,
        uint8 v,
        bytes32 r,
        bytes32 s // bytes calldata signature
    ) external;
}
