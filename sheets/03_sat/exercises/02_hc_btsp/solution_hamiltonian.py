from typing import List, Optional, Tuple

import networkx as nx
from pysat.solvers import Solver as SATSolver


class HamiltonianCycleModel:
    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph
        self.solver = SATSolver("Minicard")
        self.assumptions = []
        self.vars = {(u, v): i for i, (u, v) in enumerate(self.graph.edges, start=1)}
        self.reverse = {i: (u, v) for (u, v), i in self.vars.items()}
        self.num_edges = len(self.graph.edges)
        self.num_nodes = len(self.graph)

        # every node has exactly 2 incident edges selected
        for node in self.graph:
            incident_edges = []
            for edge in self.graph.edges(node):
                incident_edges.append(self.get_clause(edge))
            self.solver.add_atmost(incident_edges, k=2)
            self.solver.add_atmost(
                [-i for i in incident_edges], k=len(incident_edges) - 2
            )

    def get_clause(self, edge: Tuple[int, int]):
        if self.vars.get(edge) is not None:
            return self.vars[edge]
        else:
            u, v = edge
            return self.vars[v, u]

    def get_negative_clause(self, edge: Tuple[int, int]):
        if self.vars.get(edge) is not None:
            return -self.vars[edge]
        else:
            u, v = edge
            return -self.vars[v, u]

    def solve(self) -> Optional[List[Tuple[int, int]]]:
        """
        Solves the Hamiltonian Cycle Problem. If a HC is found,
        its edges are returned as a list.
        If the graph has no HC, 'None' is returned.
        """

        while self.solver.solve():
            solution = self.solver.get_model()
            cycle = []
            for i in solution:
                if i > 0:
                    cycle.append(self.reverse[i])

            # constraint: Dantzig-Fulkerson-Johnson formulation -> every vertex subset has at least two crossing edges
            tour_graph = self.graph.edge_subgraph(cycle)
            components = list(nx.connected_components(tour_graph))
            if len(components) > 1:
                for c in components:
                    subgraph = self.graph.subgraph(c)
                    negative_exiting_edges = []
                    for node in subgraph:
                        incident_edges_total = self.graph.edges(node)
                        for edge in incident_edges_total:
                            u, v = edge
                            if u in subgraph and v in subgraph:
                                continue
                            else:
                                negative_exiting_edges.append(
                                    self.get_negative_clause(edge)
                                )
                    self.solver.add_atmost(
                        negative_exiting_edges, len(negative_exiting_edges) - 2
                    )

            # solution consists of one component, HC found
            else:
                return cycle

        return None
