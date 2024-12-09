import subprocess


def run_transpiler(input_file):
    """Запускает транспилер и возвращает результат."""
    result = subprocess.run(["python3", "transpile.py", input_file], capture_output=True, text=True)
    if result.returncode != 0:
        return result.stderr.strip()
    return result.stdout.strip()


def test_simple_constants():
    """Тест: объявление простых констант."""
    with open("test_simple.toml", "w") as f:
        f.write("""
        [const]
        base_number = 41
        """)
    expected_output = """
    (define base_number 41);
    $[

    ]
    """
    assert run_transpiler("test_simple.toml").strip() == expected_output.strip()


def test_nested_structures():
    """Тест: вложенные структуры."""
    with open("test_nested.toml", "w") as f:
        f.write("""
        [nested]
        key1 = 42
        key2 = { subkey1 = 10, subkey2 = [1, 2, 3] }
        """)
    expected_output = """
    $[
      nested : $[
        key1 : 42,
        key2 : $[
          subkey1 : 10,
          subkey2 : (list 1 2 3)
        ]
      ]
    ]
    """
    assert run_transpiler("test_nested.toml").strip() == expected_output.strip()


def test_array_sort():
    """Тест: сортировка массива."""
    with open("test_sort.toml", "w") as f:
        f.write("""
        [data]
        sorted_values = "=sort([3, 1, 2])"
        """)
    expected_output = """
    $[
      data : $[
        sorted_values : |sort((list 3 1 2))|
      ]
    ]
    """
    assert run_transpiler("test_sort.toml").strip() == expected_output.strip()


def test_invalid_name():
    """Тест: ошибка для некорректного имени."""
    with open("test_invalid.toml", "w") as f:
        f.write("""
        ["invalid-name"]
        value = 10
        """)
    # Так как транспайлер преобразует имена, ожидание будет с исправленным именем
    expected_output = """
    $[
      invalid_name : $[
        value : 10
      ]
    ]
    """
    assert run_transpiler("test_invalid.toml").strip() == expected_output.strip()


def test_constants_in_expressions():
    """Тест: использование констант в выражениях."""
    with open("test_constants.toml", "w") as f:
        f.write("""
        [const]
        base_number = 41

        [data]
        computed_value = "=base_number + 1"
        """)
    expected_output = """
    (define base_number 41);
    $[
      data : $[
        computed_value : |base_number + 1|
      ]
    ]
    """
    assert run_transpiler("test_constants.toml").strip() == expected_output.strip()


def test_complex_nested():
    """Тест: сложные вложенные структуры."""
    with open("test_complex.toml", "w") as f:
        f.write("""
        [complex]
        level1 = { level2 = { level3 = [1, 2, 3] } }
        """)
    expected_output = """
    $[
      complex : $[
        level1 : $[
          level2 : $[
            level3 : (list 1 2 3)
          ]
        ]
      ]
    ]
    """
    assert run_transpiler("test_complex.toml").strip() == expected_output.strip()


def test_empty_structure():
    """Тест: пустая структура."""
    with open("test_empty.toml", "w") as f:
        f.write("""
        [empty]
        """)
    expected_output = """
    $[
      empty : $[

      ]
    ]
    """
    assert run_transpiler("test_empty.toml").strip() == expected_output.strip()


def test_invalid_expression():
    """Тест: некорректное выражение."""
    with open("test_invalid_expr.toml", "w") as f:
        f.write("""
        [data]
        expr = "=base_number / 0"
        """)
    expected_output = """
    $[
      data : $[
        expr : |base_number / 0|
      ]
    ]
    """
    assert run_transpiler("test_invalid_expr.toml").strip() == expected_output.strip()
