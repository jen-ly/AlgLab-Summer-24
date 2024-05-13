import gurobipy as gb
import networkx as nx
from data_schema import Instance, Solution
from gurobipy import GRB



class MiningRoutingSolver:
    def __init__(self, instance: Instance) -> None:
        self.map = instance.map
        self.budget = instance.budget
        self.model = gp.Model()
        # TODO: Implement me!
        #for each tunnel have binary varible indicating if it is used, and integer variable indicating its flow
        self.tunnels = {(t.location_a,t.location_b):(self.model.addVar(vtype=GRB.BINARY, name=f"tunnel_{t.location_a}_{t.location_b}"), 
                        self.model.addVar(vtype=GRB.INTEGER, lb=0, ub=t.throughput_per_hour, name=f"flow_{t.location_a}_{t.location_b}"))
                        for t in self.map.tunnels}
        #have same varibles for each tunnels reverse direction
        self.rev_tunnels = {(t.location_b,t.location_a):(self.model.addVar(vtype=GRB.BINARY, name=f"tunnel_{t.location_b}_{t.location_a}"), 
                        self.model.addVar(vtype=GRB.INTEGER, lb=0, ub=t.throughput_per_hour, name=f"flow_{t.location_b}_{t.location_a}"))
                        for t in self.map.tunnels}
        #constraint: for each tunnel only select at most one direction
        for t in self.map.tunnels:
            x = self.tunnels[t.location_a, t.location_b][0]
            x_rev = self.rev_tunnels[t.location_b, t.location_a][0]
            self.model.addConstr(x + x_rev <= 1)

        #constraint: flow out of mines has to be <= that mines production + flow into mine
        for mine in self.map.mines:
            in_flow = [v[1]*v[0] for t,v in self.tunnels.items() if t[1] == mine.id] + [v[1]*v[0] for t,v in self.rev_tunnels.items() if t[1] == mine.id]
            out_flow = [v[1]*v[0] for t,v in self.tunnels.items() if t[0] == mine.id] + [v[1]*v[0] for t,v in self.rev_tunnels.items() if t[0] == mine.id]
            self.model.addConstr(sum(out_flow) <= mine.ore_per_hour + sum(in_flow))

        #constraint: sum of the costs of selected tunnels <= budget
        costs = [v[0] * self.getCost(t[0], t[1]) for t,v in self.tunnels.items()] + [v[0] * self.getCost(t[0], t[1]) for t,v in self.rev_tunnels.items()]
        self.model.addConstr(sum(costs) <= self.budget)

        #constraint: no flow out of elevator
        flow_out_elevator = [v[1] for t,v in self.tunnels.items() if t[0] == self.map.elevator.id] + [v[1] for t,v in self.rev_tunnels.items() if t[0] == self.map.elevator.id]
        self.model.addConstr(sum(flow_out_elevator) == 0)

        #objective: maximize the flow into the elevator
        flows_into_elevator = [v[1]*v[0] for t,v in self.tunnels.items() if t[1] == self.map.elevator.id] + [v[1]*v[0] for t,v in self.rev_tunnels.items() if t[1] == self.map.elevator.id]
        self.model.setObjective(sum(flows_into_elevator), gp.GRB.MAXIMIZE)

    def getCost(self, loc_a: int, loc_b: int):
        for tunnel in self.map.tunnels:
            if tunnel.location_a == loc_a and tunnel.location_b == loc_b:
                return tunnel.reinforcement_costs
            elif tunnel.location_b == loc_a and tunnel.location_a == loc_b:
                return tunnel.reinforcement_costs

    def solve(self) -> Solution:
        """
        Calculate the optimal solution to the problem.
        Returns the "flow" as a list of tuples, each tuple with two entries:
            - The *directed* edge tuple. Both entries in the edge should be ints, representing the ids of locations.
            - The throughput/utilization of the edge, in goods per hour
        """
        # TODO: implement me!
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            #now get the solution
            flow = []
            for t,v in self.tunnels.items():
                if v[0].X > 0.5:
                    flow.append(((t[0], t[1]),round(v[1].X)))
            for t,v in self.rev_tunnels.items():
                if v[0].X > 0.5:
                    flow.append(((t[0], t[1]),round(v[1].X)))
            return Solution(flow=flow)
