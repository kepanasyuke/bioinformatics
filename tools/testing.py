"""Фабрики тест-кейсов: одна строка таблицы данных — один тест unittest.

Так сотни проверок остаются читаемыми таблицами, а не копипастой из одинаковых
методов. Каждая фабрика возвращает функцию без аргументов: unittest вызовет её
как метод, подставив self.
"""

from pathlib import Path


def equal(function, *args, expected):
    return lambda self: self.assertEqual(function(*args), expected)


def close(function, *args, expected, places=6):
    return lambda self: self.assertAlmostEqual(function(*args), expected, places=places)


def truthy(function, *args):
    return lambda self: self.assertTrue(function(*args))


def falsy(function, *args):
    return lambda self: self.assertFalse(function(*args))


def raises(error, function, *args):
    return lambda self: self.assertRaises(error, function, *args)


def contains(function, *args, needle):
    return lambda self: self.assertIn(needle, function(*args))


def attach(cls, prefix, rows):
    names = [setattr(cls, f"test_{prefix}_{index:03d}", row) for index, row in enumerate(rows)]
    return len(names)


def keep_file(target, action):
    original = Path(target).read_bytes() if Path(target).exists() else b""
    result = action()
    Path(target).write_bytes(original)
    return result
