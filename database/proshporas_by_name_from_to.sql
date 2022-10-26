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
 WHERE PR.[Record Date] >= '2021-08-28' AND 
       PR.Payor = PD.Payor AND 
       PR.Date = PD.Date AND 
       PR.Method = PD.Method AND 
       IFNULL(PR.Identifier, '2.7182818284') = IFNULL(PD.Identifier,'2.7182818284')
 ORDER BY PR.Payor,
          PD.[Surname],
          PD.[Name],
          PD.[Paid From];
