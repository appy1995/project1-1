def add(a: int, b: int) -> int:
    return a + b


def multiply(a: int, b: int) -> int:
    return a * b

def multiply_only_positive(a: int, b: int) -> int:
    assert a >= 0 and b >= 0, "Only positive numbers allowed"
    return a * b

class Calculator:
    def save(self, value: int) -> None:
        # Imagine this saves to a database
        pass
