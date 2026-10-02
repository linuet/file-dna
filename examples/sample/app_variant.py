from helpers import normalize_name


def greet(name: str, excited: bool = False) -> str:
    result = f"Hello, {normalize_name(name)}"
    return result + "!" if excited else result
