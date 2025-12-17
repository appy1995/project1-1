import pytest

from zephyr.math_utils import add, multiply, multiply_only_positive, Calculator

@pytest.fixture
def numbers():
    return 2, 3

def test_add_with_fixture(numbers):
    a, b = numbers
    assert add(a, b) == 5

def test_calculator_save_called_once(mocker):
    calc = Calculator()

    mocked_save = mocker.patch.object(calc, "save")

    calc.save(10)

    mocked_save.assert_called_once_with(10)

@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1, 2, 3),
        (0, 0, 0),
        (-1, 1, 0),
    ],
)
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected

def test_multiply_only_positive_valid():
    result = multiply_only_positive(2, 3)
    assert result == 6

def test_multiply_only_positive_raises_assertion_error():
    with pytest.raises(AssertionError):
        multiply_only_positive(-1, 2)
