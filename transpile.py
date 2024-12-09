import sys
import re
import toml

# Правило для проверки имени
NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')

def transform_name(name: str) -> str:
    # Заменяем недопустимые символы на подчеркивания
    valid_name = re.sub(r'[^a-z0-9_]', '_', name.lower())
    # Если имя начинается с цифры, добавляем префикс
    if valid_name[0].isdigit():
        valid_name = f"ip_{valid_name}"
    # Проверяем, соответствует ли имя правилам
    if not NAME_PATTERN.match(valid_name):
        raise ValueError(f"Invalid name after normalization: {name}")
    return valid_name



def transform_value(value):
    if isinstance(value, int) or isinstance(value, float):
        return str(value)
    if isinstance(value, list):
        transformed_items = [transform_value(v) for v in value]
        return "(list " + " ".join(transformed_items) + ")"
    if isinstance(value, dict):
        items = []
        for k, v in value.items():
            k_trans = transform_name(k)
            items.append(f"{k_trans} : {transform_value(v)}")
        return "$[\n  " + ",\n  ".join(items) + "\n]"
    if isinstance(value, str):
        # Если строка является IP-адресом, оставляем её как есть
        if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', value):
            return f"\"{value}\""  # Оставляем IP-адрес в кавычках
        # Проверяем, не является ли строка выражением
        if value.startswith("="):
            expr = value[1:].strip()
            expr = transform_expr(expr)
            return f"|{expr}|"
        else:
            return transform_name(value)
    raise ValueError(f"Unsupported value type: {type(value)}")

def transform_expr(expr: str) -> str:
    # Примерная трансформация выражений
    # Допустим, что sort(...) → sort((list ...))
    # Нам нужно определить, как преобразовать массивы внутри выражения.
    # Простая эвристика: искать [...], заменять на (list ...).
    expr = expr.strip()
    # Пример: sort([5,3,9,1]) → sort((list 5 3 9 1))
    # Можем заменить с помощью регулярного выражения
    expr = re.sub(r'\[(.*?)\]', lambda m: "(list " + " ".join(part.strip() for part in m.group(1).split(',')) + ")", expr)
    return expr

def main():
    if len(sys.argv) < 2:
        print("Usage: python transpile.py <input.toml>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    try:
        data = toml.load(input_path)
    except Exception as e:
        print(f"Error parsing TOML: {e}", file=sys.stderr)
        sys.exit(1)

    # Ищем раздел [const] для констант
    defines = []
    if "const" in data:
        const_table = data["const"]
        for k, v in const_table.items():
            k_trans = transform_name(k)
            val = transform_value(v)
            defines.append(f"(define {k_trans} {val});")
        del data["const"]

    # Преобразуем основную структуру
    try:
        transformed = transform_value(data)
    except ValueError as e:
        print(f"Transformation error: {e}", file=sys.stderr)
        sys.exit(1)

    # Выводим константы и затем основную структуру
    for d in defines:
        print(d)
    print(transformed)

if __name__ == "__main__":
    main()
