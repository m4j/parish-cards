SELECT PR.Payor,
       PR.[Record Date],
       PD.[Member Last],
       PD.[Member First],
       PD.Method,
       PD.Identifier,
       PD.[Paid From],
       PD.[Paid Through],
       PD.Amount
  FROM Payments_Register PR,
       Payments_Dues PD
 WHERE PR.[Record Date] > '2021-08-28' AND 
       PR.Payor = PD.Payor AND 
       PR.Date = PD.Date AND 
       PR.Method = PD.Method AND 
       IFNULL(PR.Identifier, '2.7182818284') = IFNULL(PD.Identifier,'2.7182818284')
 ORDER BY PR.Payor,
          PD.[Member Last],
          PD.[Member First],
          PD.[Paid From];
