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
 WHERE PR.[Record Date] IN ('2021-06-06', '2021-06-13', '2021-06-21') AND 
       PR.Payor = PD.Payor AND 
       PR.Date = PD.Date AND 
       PR.Method = PD.Method AND 
       PR.Identifier = PD.Identifier
 ORDER BY PR.Payor,
          PD.[Member Last],
          PD.[Member First],
          PD.[Paid From];
