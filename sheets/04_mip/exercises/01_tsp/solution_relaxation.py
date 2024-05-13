"""
Implement the Dantzig-Fulkerson-Johnson formulation for the TSP.
"""

import typing

import gurobipy as gp
import networkx as nx

class _EdgeVariables:
    """
    A helper class that manages the variables for the edges.
    Such a helper class turns out to be useful in many cases.
    """

    def __init__(self, G: nx.Graph, model: gp.Model):
        self._graph = G
        self._model = model
        self._vars = {
            (u, v): model.addVar(vtype=gp.GRB.CONTINUOUS, lb=0, ub=1, name=f"edge_{u}_{v}")
            for u, v in G.edges
        }

    def x(self, v, w) -> gp.Var:
        """
        Return variable for edge (v, w).
        """
        if (v, w) in self._vars:
            return self._vars[v, w]
        # If (v,w) was not found, try (w,v)
        return self._vars[w, v]

    def outgoing_edges(self, vertices):
        """
        Return all edges&variables that are outgoing from the given vertices.
        """
        # Not super efficient, but efficient enough for our purposes.
        for (v, w), x in self._vars.items():
            if v in vertices and w not in vertices:
                yield (v, w), x
            elif w in vertices and v not in vertices:
                yield (w, v), x

    def incident_edges(self, v):
        """
        Return all edges&variables that are incident to the given vertex.
        """
        for n in self._graph.neighbors(v):
            yield (v, n), self.x(v, n)

    def __iter__(self):
        """
        Iterate over all edges&variables.
        """
        return iter(self._vars.items())

    def as_graph(self, in_callback: bool = False):
        """
        Return the current solution as a graph.
        """
        #TODO: modify this function to set the "x" attribute of each edge
        if in_callback:
            # If we are in a callback, we need to use the solution from the callback.
            used_edges = [(vw, self._model.cbGetSolution(x)) for vw, x in self if self._model.cbGetSolution(x) >= 0.01]
        else:
            # Otherwise, we can use the solution from the model.
            used_edges = [(vw, x.X) for vw, x in self if x.X >= 0.01]
        g = nx.Graph()
        for e,x in used_edges:
            g.add_edge(e[0], e[1], x=x)
        return g


class GurobiTspRelaxationSolver:
    """
    IMPLEMENT ME!
    """

    def __init__(self, G: nx.Graph):
        """
        G is a weighted networkx graph, where the weight of an edge is stored in the
        "weight" attribute. It is strictly positive.
        """
        self.graph = G
        assert (
            G.number_of_edges() == G.number_of_nodes() * (G.number_of_nodes() - 1) / 2
        ), "Invalid graph"
        assert all(
            weight > 0 for _, _, weight in G.edges.data("weight", default=None)
        ), "Invalid graph"
        self._model = gp.Model()
        # TODO: Implement me!
        # add the edge variables
        self._edge_vars = _EdgeVariables(self.graph, self._model)
        self._enforce_vertex_constraints()
        self._minimize()

    def _enforce_vertex_constraints(self):
        #add constraints that every node has degree of 2 
        for node in self.graph:
            self._model.addConstr(sum(x for _, x in self._edge_vars.incident_edges(node)) == 2)

    def _minimize(self):
        # add the minimize objective to model
        self._model.setObjective(sum(self.graph[e[0]][e[1]]["weight"] * x for e,x in self._edge_vars), gp.GRB.MINIMIZE)

    def get_lower_bound(self) -> float:
        """
        Return the current lower bound.
        """
        # TODO: Implement me!
        return self._model.ObjBound

    def get_solution(self) -> typing.Optional[nx.Graph]:
        """
        Return the current solution as a graph.

        The solution should be a networkx Graph were the
        fractional value of the edge is stored in the "x" attribute.
        You do not have to add edges with x=0.

        ```python
        graph = nx.Graph()
        graph.add_edge(0, 1, x=0.5)
        graph.add_edge(1, 2, x=1.0)
        ```
        """
        # TODO: Implement me!
        return self._edge_vars.as_graph()

    def get_objective(self) -> typing.Optional[float]:
        """
        Return the objective value of the last solution.
        """
        # TODO: Implement me!
        return self._model.getObjective().getValue()

    def solve(self) -> None:
        """
        Solve the model and return the objective value and the lower bound.
        """
        # Set parameters for the solver.
        self._model.Params.LogToConsole = 1

        # TODO: Implement me!
        while True:
            self._model.optimize()
            solution = self._edge_vars.as_graph(in_callback=False)
            comps = list(nx.connected_components(solution))
            if len(comps) == 1:
                break # tour is already whole graph
                
            # for each component add constraint, that minimum 2 edges leave this component
            for comp in comps:
                # only deal with components that are minimum 2 nodes
                if len(comp) < 2:
                    continue
                # now add constraint
                self._model.addConstr(sum(x for _, x in self._edge_vars.outgoing_edges(comp)) >= 2)
        
        if self._model.Status == gp.GRB.OPTIMAL:
            return None
