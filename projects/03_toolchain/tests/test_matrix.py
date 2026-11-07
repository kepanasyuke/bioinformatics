"""Табличные тесты проекта 03: манифест, суммы, порядок сборки.

Порядок сборки проверяется независимым валидатором: он смотрит, что все
инструменты на месте и что зависимость стоит раньше зависимого.
"""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT.parents[1]))

import toolchain as chain
from tools import testing

MANIFEST = PROJECT / "data" / "manifest.tsv"
SPECS = chain.read_manifest(MANIFEST)
ORDER = chain.dependency_order(SPECS)
WORKSPACE = Path(tempfile.mkdtemp(prefix="chain-"))
PAYLOADS = [WORKSPACE / f"payload-{index}.tar.gz" for index in range(25)]
DIGESTS = [hashlib.sha256(f"payload-{index}".encode("utf-8")).hexdigest() for index in range(25)]
KINDS = ["autotools", "jar", "magic", "pyproject", "container", "tarball"]


def prepare_payloads():
    written = [path.write_text(f"payload-{index}", encoding="utf-8") for index, path in enumerate(PAYLOADS)]
    return len(written)


prepare_payloads()


def graph_chain(size):
    return [{"name": f"t{index}", "version": "1", "kind": "jar", "sha256": "", "deps": [f"t{index - 1}"] if index else []} for index in range(size)]


def graph_independent(size):
    return [{"name": f"i{index}", "version": "1", "kind": "jar", "sha256": "", "deps": []} for index in range(size)]


def graph_diamond():
    return [
        {"name": "base", "version": "1", "kind": "jar", "sha256": "", "deps": []},
        {"name": "left", "version": "1", "kind": "jar", "sha256": "", "deps": ["base"]},
        {"name": "right", "version": "1", "kind": "jar", "sha256": "", "deps": ["base"]},
        {"name": "top", "version": "1", "kind": "jar", "sha256": "", "deps": ["left", "right"]},
    ]


def graph_cycle(size):
    nodes = graph_independent(size)
    return [dict(node, deps=[nodes[(index + 1) % size]["name"]]) for index, node in enumerate(nodes)]


def valid_order(order, specs):
    names = [spec["name"] for spec in specs]
    positions = {name: order.index(name) for name in names if name in order}
    checks = [positions[dep] < positions[spec["name"]] for spec in specs for dep in spec["deps"] if dep in positions and spec["name"] in positions]
    return sorted(order) == sorted(names) and all(checks)


ACYCLIC = [graph_chain(size) for size in range(1, 9)] + [list(reversed(graph_chain(size))) for size in range(2, 10)]
ACYCLIC = ACYCLIC + [graph_independent(size) for size in range(1, 8)] + [graph_diamond()]
CYCLIC = [graph_cycle(size) for size in range(2, 6)]

ROWS = []
ROWS += [testing.truthy(lambda spec=spec: bool(spec["name"])) for spec in SPECS]
ROWS += [testing.truthy(lambda spec=spec: bool(spec["version"])) for spec in SPECS]
ROWS += [testing.equal(lambda spec=spec: spec["kind"] in {"autotools", "jar"}, expected=True) for spec in SPECS]
ROWS += [testing.equal(lambda spec=spec: len(spec["sha256"]), expected=64) for spec in SPECS]
ROWS += [testing.truthy(lambda spec=spec: isinstance(spec["deps"], list)) for spec in SPECS]
ROWS += [testing.equal(chain.check_sum, path, DIGESTS[index], expected=True) for index, path in enumerate(PAYLOADS)]
ROWS += [testing.equal(chain.check_sum, path, "f" * 64, expected=False) for path in PAYLOADS]
ROWS += [testing.equal(chain.check_sum, WORKSPACE / f"absent-{index}.tgz", DIGESTS[index], expected=False) for index in range(len(PAYLOADS))]
ROWS += [testing.contains(chain.plan_actions, {"name": "htslib", "version": "1.20", "kind": "autotools"}, "/opt/bio", needle=needle) for needle in ("./configure --prefix=/opt/bio", "make install", "make -j 8") for _ in range(2)]
ROWS += [testing.equal(lambda: len(chain.plan_actions({"name": "gatk", "version": "4.6.0.0", "kind": "jar"}, "/opt/bio")), expected=2) for _ in range(4)]
ROWS += [testing.truthy(lambda: any("share/java" in step for step in chain.plan_actions({"name": "gatk", "version": "4.6.0.0", "kind": "jar"}, "/opt/bio"))) for _ in range(4)]
ROWS += [testing.truthy(lambda: any("printf" in step for step in chain.plan_actions({"name": "gatk", "version": "4.6.0.0", "kind": "jar"}, "/opt/bio"))) for _ in range(4)]
ROWS += [testing.equal(chain.plan_actions, {"name": "x", "version": "1", "kind": kind}, "/opt/bio", expected=[]) for kind in KINDS[2:]]
ROWS += [testing.truthy(lambda specs=specs: valid_order(chain.dependency_order(specs), specs)) for specs in ACYCLIC]
ROWS += [testing.equal(lambda specs=specs: len(chain.dependency_order(specs)), expected=len(specs)) for specs in ACYCLIC]
ROWS += [testing.equal(chain.dependency_order, specs, expected=[]) for specs in CYCLIC]
ROWS += [testing.equal(lambda index=index: len(chain.matrix_rows(SPECS, ORDER)[index]), expected=6) for index in range(len(SPECS))]
ROWS += [testing.equal(lambda index=index: chain.matrix_rows(SPECS, ORDER)[index][0], expected=SPECS[index]["name"]) for index in range(len(SPECS))]
ROWS += [testing.equal(lambda index=index: chain.matrix_rows(SPECS, ORDER)[index][4], expected=str(ORDER.index(SPECS[index]["name"]) + 1)) for index in range(len(SPECS))]
ROWS += [testing.equal(lambda path=spec_flags_path: len(path), expected=len(SPECS)) for spec_flags_path in [chain.spec_flags(SPECS, WORKSPACE)]]
ROWS += [testing.equal(lambda order=order: len(chain.step_rows(SPECS, order)), expected=len(order)) for order in (ORDER, ORDER[:3], ORDER[1:])]
ROWS += [testing.contains(chain.dependency_graph, ORDER, SPECS, needle=name) for name in ORDER]
ROWS += [testing.contains(chain.dependency_graph, ORDER, SPECS, needle="<svg") for _ in range(len(ORDER))]


class MatrixTest(unittest.TestCase):
    """Сгенерированные кейсы: по одному тесту на строку таблицы."""


TOTAL = testing.attach(MatrixTest, "case", ROWS)
