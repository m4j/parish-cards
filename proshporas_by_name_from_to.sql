SELECT PR.Payor,
       PR.[Record Date],
       PD.[Surname],
       PD.[Name],
       PD.Method,
       PD.Identifier,
       PD.[Paid From],
       PD.[Paid Through],
       PD.Amount,
       PD.Quantity,
       PD.Comment
  FROM Payments_Register PR,
       Payments_Prosphoras PD
 WHERE PR.[Record Date] >= '2021-06-06' AND 
       PR.Payor = PD.Payor AND 
       PR.Date = PD.Date AND 
       PR.Method = PD.Method AND 
       PR.Identifier = PD.Identifier
 ORDER BY PR.Payor,
          PD.[Surname],
          PD.[Name],
          PD.[Paid From];
