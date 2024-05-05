import math
from typing import Dict, Iterable, List

import networkx as nx
from pysat.solvers import Solver as SATSolver



class KCentersSolver:
    def __init__(self, graph: nx.Graph) -> None:
        """
        Creates a solver for the k-centers problem on the given networkx graph.
        The graph is not necessarily complete, so not all nodes are neighbors.
        The distance between two neighboring nodes is a numeric value (int / float), saved as
        an edge data parameter called "weight".
        There are multiple ways to access this data, and networkx also implements
        several algorithms that automatically make use of this value.
        Check the networkx documentation for more information!
        """
        self.graph = graph
        self.sat = SATSolver("MiniCard")
        # TODO: Implement me!

    def solve_heur(self, k: int) -> List[int]:
        """
        Calculate a heuristic solution to the k-centers problem.
        Returns the k selected centers as a list of ints.
        (nodes will be ints in the given graph).
        """
        # TODO: Implement me!
        centers = []
        # start with random node
        centers.append(1)
        for i in range(k - 1):
            path_lengths = nx.multi_source_dijkstra_path_length(self.graph, sources=centers)
            centers.append(list(path_lengths)[-1])
        return centers


    def solve(self, k: int) -> List[int]:
        """
        For the given parameter k, calculate the optimal solution
        to the k-centers solution and return the selected centers as a list.
        """
        # first add atmost clause (cardinality constraint)
        self.sat.add_atmost([node for node in self.graph], k=k)

        heuristic = self.solve_heur(k)
        # get upper bound for c
        lens = nx.multi_source_dijkstra_path_length(self.graph, sources=heuristic)
        upper_bound = 0
        for target in self.graph:
            if lens[target] > upper_bound:
                upper_bound = lens[target]
        #iterate through all objectives c, for c equals all possible path lengths in Graph
        path_lengths = dict(nx.all_pairs_dijkstra_path_length(self.graph))
        #get descending list of all lengths
        leng = set()
        leng = (path_lengths[i][j] for i in self.graph for j in self.graph)
        lengths = list(leng)
        lengths.sort(reverse=True)

        for c in lengths:
            if c > upper_bound:
                continue
            #for each node add clause that one node reachable in c-distance has to be center
            for node in self.graph:
                clause = []
                for target in self.graph:
                    if path_lengths[node][target] <= c:
                        clause.append(target)
                self.sat.add_clause(clause)

            #if objective c is not feasible then stop
            if self.sat.solve():
                solution = self.sat.get_model()
            else:
                break
        # TODO: Implement me!
        centers = []
        for cent in solution:
            if cent > 0:
                centers.append(cent)
        return centers
