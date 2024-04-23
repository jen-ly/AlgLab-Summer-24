import math

import networkx as nx
from data_schema import Donation, Solution
from database import TransplantDatabase
from ortools.sat.python.cp_model import FEASIBLE, OPTIMAL, CpModel, CpSolver


class CrossoverTransplantSolver:
    def __init__(self, database: TransplantDatabase) -> None:
        """
        Constructs a new solver instance, using the instance data from the given database instance.
        :param Database database: The organ donor/recipients database.
        """
        self.database = database
        self.model = CpModel()
        # TODO: Implement me!
        self.donors = self.database.get_all_donors()
        self.recipients = self.database.get_all_recipients()

        #Variables: Try only var if compatible
        self.t = {}
        for don in self.donors:
            for rec in self.database.get_compatible_recipients(don):
                self.t[don,rec] = self.model.NewBoolVar(f"t_{don}{rec}")
        #Constraint: donor can only donate once
        for don in self.donors:
            recips = self.database.get_compatible_recipients(don)
            self.model.Add(sum(self.t[don,rec] for rec in recips) <= 1)

        #Constraint: recipient can only receive one organ
        for rec in self.recipients:
            dons = self.database.get_compatible_donors(rec)
            self.model.Add(sum(self.t[don, rec] for don in dons) <= 1)
        #Constraint: donor only donates if their recipient receives an organ
        for rec in self.recipients:
            dons = self.database.get_partner_donors(rec)
            #make list with all incoming donations to rec
            incoming_donos = []
            for donor in self.database.get_compatible_donors(rec):
                incoming_donos.append(self.t[donor,rec])
            #make list with all donations goint out of any partner donor of rec
            outgoing = []
            for don in dons:
                for recip in self.database.get_compatible_recipients(don):
                    outgoing.append(self.t[don, recip])
            self.model.Add(sum(incoming_donos) <= sum(outgoing))

        #Objective
        t2 = []
        for don in self.donors:
            for rec in self.database.get_compatible_recipients(don):
                t2.append(self.t[don,rec])
        self.model.Maximize(sum(t2))

        self.solver = CpSolver()
        self.solver.parameters.log_search_progress = True


    def optimize(self, timelimit: float = math.inf) -> Solution:
        """
        Solves the constraint programming model and returns the optimal solution (if found within time limit).
        :param timelimit: The maximum time limit for the solver.
        :return: A list of Donation objects representing the best solution, or None if no solution was found.
        """
        if timelimit <= 0.0:
            return Solution(donations=[])
        if timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit
        # TODO: Implement me!
        status = self.solver.Solve(self.model)
        assert status == OPTIMAL

        donos = []
        for don in self.donors:
            for rec in self.database.get_compatible_recipients(don):
                if self.solver.Value(self.t[don,rec]) == 1:
                    donos.append(Donation(donor=don, recipient=rec))
        return Solution(donations=donos)
