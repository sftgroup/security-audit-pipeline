"""
v4-unchecked-delegatecall.py — Slither Custom Detector
SCSVS: V4 通信
检测: delegatecall 目标地址未验证
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall
from slither.core.variables.state_variable import StateVariable


class UncheckedDelegatecall(AbstractDetector):
    ARGUMENT = "v4-unchecked-delegatecall"
    HELP = "delegatecall target address is not verified against a whitelist"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/ComposableSecurity/SCSVS/blob/master/2-Architecture/README.md#v4-communication"
    WIKI_TITLE = "V4: Unchecked delegatecall"
    WIKI_DESCRIPTION = (
        "delegatecall to an unverified address allows arbitrary code execution "
        "in the caller's context, potentially compromising storage and funds."
    )
    WIKI_RECOMMENDATION = "Verify delegatecall targets against a whitelist of known-safe addresses."

    def _detect(self):
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions_entry_points:
                for ir in function.slithir_operations:
                    if not isinstance(ir, LowLevelCall):
                        continue
                    if ir.call_type != "delegatecall":
                        continue
                    destination = ir.destination

                    # Check if destination is a constant or whitelisted
                    is_safe = self._is_safe_delegatecall_target(destination, contract)
                    if not is_safe:
                        results.append(self.generate_result([
                            f"delegatecall in '{function.name}' of {contract.name}",
                            f"  targets: {destination}",
                            "  The target address is not verified against a whitelist.",
                            "  Use a mapping of approved implementation addresses."
                        ]))
        return results

    def _is_safe_delegatecall_target(self, destination, contract):
        # Check if destination is a hardcoded address == implementation
        if isinstance(destination, str) and destination.startswith("0x"):
            return True
        # Check if it's read from a verified source (e.g., proxy admin storage)
        if isinstance(destination, StateVariable):
            name = destination.name.lower()
            if any(kw in name for kw in ["implementation", "impl", "target", "logic"]):
                return True
        # Check if passed through require/if validation before
        # (simplified check — real implementation would trace dataflow)
        return False
