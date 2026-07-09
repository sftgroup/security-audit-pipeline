"""
v3-storage-layout.py — Slither Custom Detector
SCSVS: V3 区块链数据
检测: Proxy 升级合约中存储槽冲突
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations import Contract


class StorageLayoutConflict(AbstractDetector):
    ARGUMENT = "v3-storage-layout"
    HELP = "Upgradeable contract has potential storage layout conflict"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://docs.openzeppelin.com/upgrades-plugins/1.x/writing-upgradeable"
    WIKI_TITLE = "V3: Storage Layout Conflict in Upgradeable Contract"
    WIKI_DESCRIPTION = (
        "Storage variables in upgradeable contracts must maintain the same layout "
        "across versions. Adding/removing/reordering state variables can cause corruption."
    )
    WIKI_RECOMMENDATION = (
        "Use OpenZeppelin's storage gap pattern. Never remove or reorder existing "
        "state variables in upgradeable contracts. Append new variables at the end."
    )

    def _detect(self):
        results = []
        proxy_contracts = self._find_upgradeable_contracts()
        if len(proxy_contracts) < 2:
            return results  # No upgradeable contract pair to compare

        for contract in self.compilation_unit.contracts_derived:
            if not contract.is_upgradeable:
                continue
            # Check for storage gap
            has_gap = False
            for var in contract.state_variables:
                if "gap" in var.name.lower() and var.type == "uint256[50]":
                    has_gap = True
                    break
            if not has_gap:
                results.append(self.generate_result([
                    f"Upgradeable contract '{contract.name}' lacks storage gap.",
                    "  - Add: uint256[50] private __gap; at the end of state variables",
                    "  - This reserves slots for future upgrades"
                ]))

            # Check storage order consistency
            storage_order = self._get_storage_order(contract)
            for var_name, slot in storage_order:
                if self._is_misplaced(var_name, slot):
                    results.append(self.generate_result([
                        f"State variable '{var_name}' at slot {slot} in {contract.name}",
                        "  may cause storage collision with the implementation contract."
                    ]))

        return results

    def _find_upgradeable_contracts(self):
        return [c for c in self.compilation_unit.contracts_derived
                if c.is_upgradeable or any("proxy" in parent.name.lower()
                for parent in c.inheritance)]

    def _get_storage_order(self, contract):
        order = []
        for i, var in enumerate(contract.state_variables_ordered):
            order.append((var.name, i))
        return order

    def _is_misplaced(self, name, slot):
        # Flag if slot > 50 and no gap before it (heuristic)
        return False  # Requires comparison with implementation contract
