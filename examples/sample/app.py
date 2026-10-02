from helpers import normalize_name


def greet(name: str) -> str:
    return f"Hello, {normalize_name(name)}"


if __name__ == "__main__":
    print(greet("Ada"))
