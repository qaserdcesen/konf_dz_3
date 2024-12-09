import sys
import re
import toml

# Правило для проверки имени
NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')

def transform_name(name: str) -> str:
    # Все отладочные сообщения идут в stderr
    print(f"Transforming name: {name}", file=sys.stderr)
    if not NAME_PATTERN.match(name):
        raise ValueError(f"Invalid name: {name}")
    return name

def transform_expr(expr: str) -> str:
    print(f"Original expression: {expr}", file=sys.stderr)
    expr = expr.strip()
    # Преобразуем массивы внутри выражения
    expr = re.sub(
        r'\[(.*?)\]',
        lambda m: "(list " + " ".join(part.strip() for part in m.group(1).split(',')) + ")",
        expr
    )
    print(f"Transformed expression: {expr}", file=sys.stderr)
    return expr

def transform_value(value):
    print(f"Transforming value: {value}", file=sys.stderr)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) or isinstance(value, float):
        return str(value)
    if isinstance(value, list):
        transformed_items = [transform_value(v) for v in value]
        return "(list " + " ".join(transformed_items) + ")"
    if isinstance(value, dict):
        items = []
        for k, v in value.items():
            print(f"Processing key: {k}, value: {v}", file=sys.stderr)
            k_trans = transform_name(k)
            items.append(f"{k_trans} : {transform_value(v)}")
        # Используем 4 пробела как отступ для словарей
        return "$[\n    " + ",\n    ".join(items) + "\n]"
    if isinstance(value, str):
        # Если это IP-адрес, оставляем его в кавычках
        if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', value):
            return f"\"{value}\""
        # Проверяем, является ли это выражением
        if value.startswith("="):
            expr = value[1:].strip()
            print(f"Transforming expression: {expr}", file=sys.stderr)
            expr = transform_expr(expr)
            return f"|{expr}|"
        else:
            return transform_name(value)
    raise ValueError(f"Unsupported value type: {type(value)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python transpile.py <input.toml>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    print(f"Loading TOML file from: {input_path}", file=sys.stderr)
    try:
        data = toml.load(input_path)
        print(f"Loaded data: {data}", file=sys.stderr)
    except Exception as e:
        print(f"Error parsing TOML: {e}", file=sys.stderr)
        sys.exit(1)

    defines = []
    if "const" in data:
        const_table = data.pop("const")
        print(f"Processing [const] section: {const_table}", file=sys.stderr)
        for k, v in const_table.items():
            try:
                k_trans = transform_name(k)
                val = transform_value(v)
                defines.append(f"(define {k_trans} {val});")
            except ValueError as ve:
                print(f"Transformation error in [const] section: {ve}", file=sys.stderr)
                sys.exit(1)

    if data:
        print(f"Processing main data: {data}", file=sys.stderr)
        try:
            transformed = transform_value(data)
        except ValueError as e:
            print(f"Transformation error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        transformed = ""

    # Выводим результат только в stdout
    for d in defines:
        print(d)
    if transformed:
        print(transformed)

if __name__ == "__main__":
    main()
