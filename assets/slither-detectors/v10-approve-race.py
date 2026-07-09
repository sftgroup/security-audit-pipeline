"""
v10-approve-race.py — Slither Custom Detector
SCSVS: V10 Token
检测: ERC20 approve/transferFrom race condition
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall, HighLevelCall


class ApproveRaceCondition(AbstractDetector):
    ARGUMENT = "v10-approve-race"
    HELP = "ERC20 approve used instead of increaseAllowance/decreaseAllowance"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729"
    WIKI_TITLE = "V10: ERC20 Approve Race Condition"
    WIKI_DESCRIPTION = (
        "ERC20 approve() is vulnerable to a race condition where a spender can "
        "front-run a re-approval and spend both the old and new allowance."
    )
    WIKI_RECOMMENDATION = "Use increaseAllowance() and decreaseAllowance() instead of approve()."

    def _detect(self):
        results = []
        approve_funcs = self._find_approve_functions()

        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions_entry_points:
                for ir in function.slithir_operations:
                    if not isinstance(ir, (HighLevelCall, LowLevelCall)):
                        continue
                    # Check if calling approve()
                    for called_func in ir.function_calls if hasattr(ir, "function_calls") else []:
                        if called_func in approve_funcs:
                            # Check if the approve is preceded by a check
                            if not self._has_allowance_check(function):
                                results.append(self.generate_result([
                                    f"'{function.name}' in {contract.name} calls ERC20.approve()",
                                    "  Consider using increaseAllowance() / decreaseAllowance()",
                                    "  to prevent the ERC20 approve race condition.",
                                    "  See: https://swcregistry.io/docs/SWC-114"
                                ]))
        return results

    def _find_approve_functions(self):
        approve_funcs = []
        for contract in self.compilation_unit.contracts:
            for func in contract.functions:
                if func.name == "approve" and func.visibility == "public":
                    approve_funcs.append(func)
        return approve_funcs

    def _has_allowance_check(self, function):
        # Check if the function resets to 0 first (common fix pattern)
        func_body = str(function).lower()
        return "approve(msg.sender, 0)" in func_body or \
               "approve(spender, 0)" in func_body or \
               "safeapprove" in func_body or \
               "increaseallowance" in func_body or \
               "decreaseallowance" in func_body
