from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS = ROOT / "experimentos"
FORBIDDEN_ROOT_DIRS = {"experiments", "harness", "tests", "artifacts"}
SYSTEM_DIRS = {"_sistema", "Evidencias", "conocimiento_agregado", "registro_flujo"}


class RepositorySandboxTests(unittest.TestCase):
    def test_no_legacy_experiment_roots(self) -> None:
        existing = {
            name for name in FORBIDDEN_ROOT_DIRS
            if (ROOT / name).exists()
        }
        self.assertFalse(
            existing,
            f"Experimental work must stay under experimentos/: {sorted(existing)}",
        )

    def test_central_knowledge_and_evidence_exist(self) -> None:
        self.assertTrue((EXPERIMENTS / "conocimiento_agregado" / "DESCUBRIMIENTOS.md").is_file())
        self.assertTrue((EXPERIMENTS / "Evidencias" / "README.md").is_file())

    def test_top_level_experiment_folders_link_to_evidence(self) -> None:
        missing = []
        for child in EXPERIMENTS.iterdir():
            if not child.is_dir() or child.name in SYSTEM_DIRS:
                continue
            if not (child / "EVIDENCIA.md").is_file():
                missing.append(child.name)
        self.assertFalse(
            missing,
            f"Experiment folders missing EVIDENCIA.md: {sorted(missing)}",
        )

    def test_executable_experiment_directories_link_to_evidence(self) -> None:
        missing = []
        for script in EXPERIMENTS.rglob("*.py"):
            if "_sistema" in script.parts:
                continue
            if not script.name.startswith(("run_", "run")):
                continue
            if not (script.parent / "EVIDENCIA.md").is_file():
                missing.append(str(script.parent.relative_to(ROOT)))
        self.assertFalse(
            sorted(set(missing)),
            f"Executable experiment directories missing EVIDENCIA.md: {sorted(set(missing))}",
        )

    def test_evidence_links_point_to_central_registry(self) -> None:
        bad = []
        for link_file in EXPERIMENTS.rglob("EVIDENCIA.md"):
            content = link_file.read_text(encoding="utf-8")
            if "Evidencias/EV-" not in content:
                bad.append(str(link_file.relative_to(ROOT)))
        self.assertFalse(
            bad,
            f"EVIDENCIA.md without central EV link: {sorted(bad)}",
        )

    def test_central_evidence_links_to_accumulated_knowledge(self) -> None:
        bad = []
        for evidence in (EXPERIMENTS / "Evidencias").glob("EV-*.md"):
            content = evidence.read_text(encoding="utf-8")
            if "conocimiento_agregado/DESCUBRIMIENTOS.md" not in content:
                bad.append(evidence.name)
        self.assertFalse(
            bad,
            f"Central evidence missing accumulated-knowledge link: {sorted(bad)}",
        )


if __name__ == "__main__":
    unittest.main()
