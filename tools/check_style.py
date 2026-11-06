"""Проверяет стиль кода: один выход, без continue, вложенность не глубже трёх.

Правила из STYLE.md. Запуск: python tools/check_style.py .
"""

import ast
import re
import sys
from pathlib import Path

MAX_RETURNS = 1
MAX_DEPTH = 3
MAX_BODY = 12
SKIP_PARTS = {".git", "__pycache__", ".venv", "legacy", "node_modules"}
COMPOUND = (
    ast.For,
    ast.While,
    ast.If,
    ast.With,
    ast.Try,
    ast.AsyncFor,
    ast.AsyncWith,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
)


def clean_parts(path):
    return [part for part in path.parts if part not in SKIP_PARTS]


def files_with_suffix(root, suffix):
    found = [p for p in Path(root).rglob(f"*{suffix}") if len(clean_parts(p)) == len(p.parts)]
    return sorted(found)


def read_tree(path):
    return ast.parse(Path(path).read_text(encoding="utf-8"))


def functions_of(tree):
    nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return [(node.name, node) for node in nodes]


def count_returns(node):
    returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
    return len(returns)


def continue_lines(node):
    return [n.lineno for n in ast.walk(node) if isinstance(n, ast.Continue)]


def max_depth(node):
    depths = [1 + max_depth(child) for child in ast.iter_child_nodes(node) if isinstance(child, COMPOUND)]
    return max(depths) if depths else 0


def body_length(node):
    starts = [item.lineno for item in node.body]
    ends = [item.end_lineno or item.lineno for item in node.body]
    return max(ends) - min(starts) + 1


def return_issue(name, node):
    total = count_returns(node)
    return [f"выходов {total}, нужен один"] if total > MAX_RETURNS else []


def depth_issue(name, node):
    depth = max_depth(node)
    return [f"вложенность {depth}, максимум {MAX_DEPTH}"] if depth > MAX_DEPTH else []


def size_issue(name, node):
    size = body_length(node)
    return [f"тело {size} строк, максимум {MAX_BODY}"] if size > MAX_BODY else []


def contact_issues(name, node):
    return [f"найден continue в строке {line}" for line in continue_lines(node)]


def check_function(name, node):
    problems = return_issue(name, node) + depth_issue(name, node) + size_issue(name, node) + contact_issues(name, node)
    return [f"строка {node.lineno}: функция {name}: {problem}" for problem in problems]


def check_file(path):
    return [f"{path}:{issue}" for name, node in functions_of(read_tree(path)) for issue in check_function(name, node)]


def bash_returns(block):
    return len(re.findall(r"^\s*return\b", block, re.M))


def check_bash(path):
    text = Path(path).read_text(encoding="utf-8")
    blocks = re.findall(r"^([a-zA-Z_][a-zA-Z0-9_]*)\(\)\s*\{\n(.*?)^\}", text, re.S | re.M)
    counts = [f"{path}: функция {name}: выходов {bash_returns(body)}, нужен один" for name, body in blocks if bash_returns(body) > 1]
    continues = [f"{path}: найден continue"] if re.search(r"^\s*continue\b", text, re.M) else []
    return counts + continues


def report_text(issues, python_count, bash_count):
    head = f"Проверено файлов: Python {python_count}, bash {bash_count}"
    body = "\n".join(issues) if issues else "Нарушений стиля нет."
    return f"{head}\n{body}"


def main(argv):
    root = argv[1] if len(argv) > 1 else "."
    python_files = files_with_suffix(root, ".py")
    bash_files = files_with_suffix(root, ".sh")
    issues = [item for path in python_files for item in check_file(path)]
    issues = issues + [item for path in bash_files for item in check_bash(path)]
    print(report_text(issues, len(python_files), len(bash_files)))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
