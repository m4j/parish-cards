-- campaign_mail_merge source

CREATE VIEW campaign_mail_merge AS SELECT group_concat(M.first_name || ' ' || M.last_name, '\\') || '\\' || M.Primary_Address || '\\' || M.City || ', ' || M.State_Region || ' ' || M.Postal_Code || CASE WHEN coalesce(M.Plus_4, '') <> '' THEN '-' ELSE '' END || M.Plus_4 AS Latex_Mailing_TO,
       CASE WHEN COUNT( * ) > 1 THEN 'Дорогие ' || group_concat(M.RU_Member_Name, ' и ') WHEN M.Gender = 'M' THEN 'Дорогой ' || M.RU_Member_Name ELSE 'Дорогая ' || M.RU_Member_Name END AS RU_Salutation,
       'Dear ' || group_concat(M.first_name, ' and ') AS EN_Salutation,
       group_concat(M.last_name || ', ' || M.first_name, ' & ') AS EN_Names,
       M.Primary_Address,
       M.City,
       M.State_Region,
       M.Postal_Code,
       M.Plus_4,
       group_concat(M.Latex_RU_Payment_Status, ' ') AS Latex_RU_Payment_Status,
       group_concat(M.Latex_EN_Payment_Status, ' ') AS Latex_EN_Payment_Status
  FROM (
           SELECT MS.*
             FROM member_status_v MS,
                  mail_campaign CAMP,
                  card_campaign CC
            WHERE CAMP.Current = 'Y' AND 
                  CC.Campaign = CAMP.Campaign AND 
                  CC.last_name = MS.last_name AND 
                  CC.first_name = MS.first_name
            ORDER BY MS.Member_Order
       )
       M
 ORDER BY EN_Names;