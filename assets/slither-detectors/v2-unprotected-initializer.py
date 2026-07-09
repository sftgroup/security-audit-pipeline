"""
v2-unprotected-initializer.py — Slither Custom Detector
SCSVS: V2 访问控制
检测: 初始化函数是否可被重复调用 / 未授权调用
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import InternalCall


class UnprotectedInitializer(AbstractDetector):
    ARGUMENT = "v2-unprotected-initializer"
    HELP = "Initialize function lacks protection against repeated or unauthorized calls"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/ComposableSecurity/SCSVS/blob/master/2-Architecture/README.md#v2-access-control"
    WIKI_TITLE = "V2: Unprotected Initializer"
    WIKI_DESCRIPTION = "Initializer functions must be protected to prevent re-initialization or unauthorized calls."
    WIKI_RECOMMENDATION = "Use OpenZeppelin initializer modifier or custom re-initialization guard."

    def _detect(self):
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                if not self._is_initializer(function):
                    continue
                if not self._has_initializer_protection(function):
                    results.append(self.generate_result([
                        f"Initializer '{function.name}' in {contract.name} lacks protection.",
                        "  - No initializer modifier found",
                        "  - Could be called multiple times or by unauthorized callers",
                        "  - Add 'initializer' modifier (OpenZeppelin) or custom guard"
                    ]))
        return results

    def _is_initializer(self, function):
        name_lower = function.name.lower()
        return (
            function.name == "initialize" or
            "init" in name_lower or
            function.name.startswith("__")
        ) and not function.is_constructor

    def _has_initializer_protection(self, function):
        modifiers = [m.name.lower() for m in function.modifiers]
        for mod_name in modifiers:
            if any(kw in mod_name for kw in ["initializer", "onlyonce", "initguard", "notinitialized"]):
                return True
        # Check for manual bool flag pattern
        for ir in function.slithir_operations:
            if hasattr(ir, "value") and "_initialized" in str(ir).lower():
                return True
        return False
