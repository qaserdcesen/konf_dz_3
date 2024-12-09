import unittest
import subprocess
import os

class TestTranspileTool(unittest.TestCase):
    def setUp(self):
        # Путь к исполняемому скрипту
        self.script = 'transpile.py'
        # Создаём временную директорию для тестовых файлов
        os.makedirs('test_temp', exist_ok=True)
        self.test_dir = 'test_temp'

    def tearDown(self):
        # Удаляем временные файлы после тестов
        for filename in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, filename)
            os.remove(file_path)
        os.rmdir(self.test_dir)

    def run_transpile(self, input_content):
        input_path = os.path.join(self.test_dir, 'input.toml')
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write(input_content)

        result = subprocess.run(
            ['python', self.script, input_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result

    def test_simple_key_value(self):
        input_toml = """
[const]
name = "example"
value = 42
"""
        expected_output = """(define name example);
(define value 42);
"""
        result = self.run_transpile(input_toml)
        self.assertEqual(result.stdout.strip(), expected_output.strip())
        self.assertEqual(result.returncode, 0)

    def test_arrays_and_dictionaries(self):
        input_toml = """
[const]
numbers = [1, 2, 3, 4]
config = { host = "localhost", port = 8080 }
"""
        # Приводим отступы к 4 пробелам, как генерирует код
        expected_output = """(define numbers (list 1 2 3 4));
(define config $[
    host : localhost,
    port : 8080
]);
"""
        result = self.run_transpile(input_toml)
        self.assertEqual(result.stdout.strip(), expected_output.strip())
        self.assertEqual(result.returncode, 0)

    def test_nested_structures(self):
        # Удалим лишние пробелы в начале и приведём отступы под код (4 пробела)
        input_toml = """
[const]
database = { host = "127.0.0.1", ports = [8001, 8001, 8002], connection_max = 5000, enabled = true }
"""
        expected_output = """(define database $[
    host : "127.0.0.1",
    ports : (list 8001 8001 8002),
    connection_max : 5000,
    enabled : true
]);
"""
        result = self.run_transpile(input_toml)
        if result.returncode != 0:
            print("STDERR:", result.stderr)
        self.assertEqual(result.stdout.strip(), expected_output.strip())
        self.assertEqual(result.returncode, 0)

    def test_expressions(self):
        input_toml = """
[const]
base = 10
increment = "= base + 5"
sorted_numbers = "= sort([3,1,2])"
"""
        expected_output = """(define base 10);
(define increment |base + 5|;
(define sorted_numbers |sort((list 3 1 2))|;
"""
        result = self.run_transpile(input_toml)
        self.assertIn("(define base 10);", result.stdout)
        self.assertIn("(define increment |base + 5|);", result.stdout)
        self.assertIn("(define sorted_numbers |sort((list 3 1 2))|);", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_invalid_name(self):
        input_toml = """
[const]
1invalid = 100
"""
        result = self.run_transpile(input_toml)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Transformation error in [const] section: Invalid name: 1invalid", result.stderr)

    def test_invalid_syntax(self):
        input_toml = """
[const
name = "example
"""
        # Здесь ожидается ошибка парсинга TOML
        result = self.run_transpile(input_toml)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error parsing TOML", result.stderr)

if __name__ == '__main__':
    unittest.main()
