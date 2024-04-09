from data_schema import Instance, Solution


def solve(instance: Instance) -> Solution:
    instance.numbers.sort()
    numbers = instance.numbers
    return Solution(
        number_a=numbers[0],
        number_b=numbers[-1],
        distance=abs(numbers[0] - numbers[-1]),
    )
