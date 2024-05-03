import math
from enum import Enum
from typing import List, Optional, Tuple

import networkx as nx
from _timer import Timer
from solution_hamiltonian import HamiltonianCycleModel


class SearchStrategy(Enum):
    """
    Different search strategies for the solver.
    """

    SEQUENTIAL_UP = 1  # Try smallest possible k first.
    SEQUENTIAL_DOWN = 2  # Try any improvement.
    BINARY_SEARCH = 3  # Try a binary search for the optimal k.

    def __str__(self):
        return self.name.title()

    @staticmethod
    def from_str(s: str):
        return SearchStrategy[s.upper()]


class BottleneckTSPSolver:
    def __init__(self, graph: nx.Graph) -> None:
        """
        Creates a solver for the Bottleneck Traveling Salesman Problem on the given networkx graph.
        You can assume that the input graph is complete, so all nodes are neighbors.
        The distance between two neighboring nodes is a numeric value (int / float), saved as
        an edge data parameter called "weight".
        There are multiple ways to access this data, and networkx also implements
        several algorithms that automatically make use of this value.
        Check the networkx documentation for more information!
        """
        self.graph = graph
        # get list of sorted weights of the graph
        self.weights = set(self.graph.edges[e]["weight"] for e in self.graph.edges)
        self.weights = list(self.weights)
        self.weights.sort()
        self.best_solution = None

    def optimize_bottleneck(
        self,
        time_limit: float = math.inf,
        search_strategy: SearchStrategy = SearchStrategy.BINARY_SEARCH,
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Find the optimal bottleneck tsp tour.
        """

        self.timer = Timer(time_limit)
        left = 0
        right = len(self.weights) - 1
        while left < right:
            m = math.floor((left + right) / 2)
            t_weight = self.weights[m]
            # remove all edges with weight > t_weight
            new_graph = self.graph.copy()
            edges = [
                (u, v)
                for (u, v) in self.graph.edges
                if self.graph.edges[(u, v)]["weight"] > t_weight
            ]
            new_graph.remove_edges_from(edges)
            model = HamiltonianCycleModel(graph=new_graph)
            # if the graph after removing the edges is still Hamiltonian, then continue binary search in lower half of weights list
            solution = model.solve()
            if solution is not None:
                self.best_solution = solution
                right = m
            else:
                # after deleting edges the model is not solvable, so continue binary search in upper half of weights list
                left = m + 1

        return self.best_solution
