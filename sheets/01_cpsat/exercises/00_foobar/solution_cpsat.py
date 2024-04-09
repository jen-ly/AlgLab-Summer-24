from data_schema import Instance, Solution
from ortools.sat.python import cp_model


def solve(instance: Instance) -> Solution:
    numbers = instance.numbers
    model = cp_model.CpModel()
    max_distance = model.NewIntVar(
        0, 200, "distance"
    )  # Maximum number selected based on the tests

    first_selected = [model.NewBoolVar(f"{i}") for i in range(len(numbers))]
    second_selected = [model.NewBoolVar(f"{j}") for j in range(len(numbers))]
    model.Add(sum(first_selected) == 1)
    model.Add(sum(second_selected) == 1)
    model.Add(
        max_distance
        == sum(first_selected[i] * numbers[i] for i in range(len(numbers)))
        - sum(second_selected[j] * numbers[j] for j in range(len(numbers)))
    )
    model.Maximize(max_distance)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    assert status == cp_model.OPTIMAL
    print(solver.SolutionInfo())
    print(solver.ResponseStats())

    # Find out the numbers that got selected
    index_first_selected = [
        i for i, var in enumerate(first_selected) if solver.Value(var) == 1
    ]
    index_second_selected = [
        j for j, var in enumerate(second_selected) if solver.Value(var) == 1
    ]

    return Solution(
        number_a=numbers[index_first_selected[0]],
        number_b=numbers[index_second_selected[0]],
        distance=solver.Value(max_distance),
    )
