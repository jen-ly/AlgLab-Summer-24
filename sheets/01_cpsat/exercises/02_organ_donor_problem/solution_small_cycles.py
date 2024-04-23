import math
from collections import defaultdict

import networkx as nx
from data_schema import Donation, Solution
from database import TransplantDatabase
from ortools.sat.python.cp_model import FEASIBLE, OPTIMAL, CpModel, CpSolver


class CycleLimitingCrossoverTransplantSolver:
    def __init__(self, database: TransplantDatabase) -> None:
        """
        Constructs a new solver instance, using the instance data from the given database instance.
        :param Database database: The organ donor/recipients database.
        """

        self.database = database
        # TODO: Implement me!
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
            self.model.Add(sum(self.t[d,rec] for d in self.database.get_compatible_donors(rec)) <= sum(self.t[d,r] for d in dons for r in self.database.get_compatible_recipients(d)))

        #Constraint only allow 3-cycles. Need constraint for each combination of incoming/outgoing donation
        for rec in self.recipients:
            partner_donors = self.database.get_partner_donors(rec)
            incoming = []
            outgoing = []
            for partner in partner_donors:
                for recip in self.database.get_compatible_recipients(partner):
                    outgoing.append(Donation(donor=partner, recipient=recip))
            
            for compat_donor in self.database.get_compatible_donors(rec):
                incoming.append(Donation(donor=compat_donor, recipient=rec))

            for out_dono in outgoing:
                for inc_dono in incoming:
                    third_donos = []
                    
                    #case if it is 2-cycle
                    if out_dono.recipient == self.database.get_partner_recipient(inc_dono.donor):
                        continue

                    for partner in self.database.get_partner_donors(out_dono.recipient):
                        if partner in self.database.get_compatible_donors(self.database.get_partner_recipient(inc_dono.donor)):
                            third_donos.append(self.t[partner, self.database.get_partner_recipient(inc_dono.donor)])
                    
                    inc_dono_t = self.t[inc_dono.donor, inc_dono.recipient]
                    out_dono_t = self.t[out_dono.donor, out_dono.recipient]
                    self.model.Add(inc_dono_t + out_dono_t <= sum(third_donos) + 1)
                        
        #Objective
        self.model.Maximize(sum(self.t[d,r] for d in self.donors for r in self.database.get_compatible_recipients(d)))
        
        self.solver = CpSolver()
        self.solver.parameters.log_search_progress = True


    def optimize(self, timelimit: float = math.inf) -> Solution:
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
