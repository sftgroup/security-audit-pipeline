"""
v14-flashloan-callback.py — Slither Custom Detector
SCSVS: V14 DeFi
检测: 闪电贷回调函数缺少访问控制
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall


class FlashloanCallbackAccess(AbstractDetector):
    ARGUMENT = "v14-flashloan-callback"
    HELP = "Flashloan callback function lacks access control"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/ComposableSecurity/SCSVS/blob/master/2-Architecture/README.md#v14-defi"
    WIKI_TITLE = "V14: Unprotected Flashloan Callback"
    WIKI_DESCRIPTION = (
        "Flashloan callback functions (e.g., onFlashLoan, executeOperation) "
        "must verify that the caller is the expected lending pool, or anyone "
        "could invoke them to drain funds."
    )
    WIKI_RECOMMENDATION = "Add require(msg.sender == address(lendingPool)) in flashloan callback."

    # Known flashloan callback function names
    FLASHLOAN_CALLBACKS = [
        "onFlashLoan",
        "executeOperation",
        "onFlashSwap",
        "uniswapV3FlashCallback",
        "uniswapV2Call",
        "pancakeCall",
        "balancerFlashLoanCallback",
        "onERC3156FlashLoan",
    ]

    def _detect(self):
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                if not self._is_flashloan_callback(function):
                    continue
                if not self._has_caller_verification(function):
                    results.append(self.generate_result([
                        f"Flashloan callback '{function.name}' in {contract.name}",
                        "  lacks msg.sender verification.",
                        "  Add: require(msg.sender == address(LENDING_POOL), 'unauthorized');",
                        "  Anyone can call this function and potentially drain funds."
                    ]))
        return results

    def _is_flashloan_callback(self, function):
        return function.name in self.FLASHLOAN_CALLBACKS or \
               any(kw in function.name.lower() for kw in ["flashloan", "flashswap", "flash_loan"])

    def _has_caller_verification(self, function):
        func_body = str(function).lower() if hasattr(function, "body") else str(function.slithir_operations).lower()
        checks = [
            "msg.sender ==",
            "require(msg.sender",
            "require(_msgSender()",
        ]
        for check in checks:
            if check in func_body:
                # Found a sender check — verify it's restricting to known pool
                if any(pool in func_body for pool in ["lendingpool", "pool", "aave", "compound", "balancer", "uniswap"]):
                    return True
        return False
