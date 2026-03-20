UPDATE network SET e_e_priority = CASE notion_page_id
  WHEN '20f0040a-64da-4ac0-a45e-9d31ef9ee8d1' THEN 'P0🔥'
  WHEN '29a29bcc-b6fc-8020-992d-d71537a7a70f' THEN 'P1'
  WHEN '2ec29bcc-b6fc-81d1-9d1c-ce3aa46935b9' THEN 'P0🔥'
  WHEN '2ed29bcc-b6fc-81fa-a328-e32721b99b95' THEN 'P2'
  WHEN '2fd29bcc-b6fc-8100-a3b4-ea8cf01e61e9' THEN 'P1'
  WHEN '2fd29bcc-b6fc-8164-86ef-fd3b155bd10d' THEN 'P1'
  WHEN '2fd29bcc-b6fc-8178-9a9e-dc18d8c9a9a7' THEN 'P1'
  WHEN '2fd29bcc-b6fc-81b3-b081-dab7d13a3d31' THEN 'P1'
  WHEN '2fd29bcc-b6fc-81f2-a146-f01b94624ad8' THEN 'P1'
  WHEN 'a154cbcb-d124-4d4f-bda5-0b6995871439' THEN 'P0🔥'
END, updated_at = now()
WHERE notion_page_id IN ('20f0040a-64da-4ac0-a45e-9d31ef9ee8d1','29a29bcc-b6fc-8020-992d-d71537a7a70f','2ec29bcc-b6fc-81d1-9d1c-ce3aa46935b9','2ed29bcc-b6fc-81fa-a328-e32721b99b95','2fd29bcc-b6fc-8100-a3b4-ea8cf01e61e9','2fd29bcc-b6fc-8164-86ef-fd3b155bd10d','2fd29bcc-b6fc-8178-9a9e-dc18d8c9a9a7','2fd29bcc-b6fc-81b3-b081-dab7d13a3d31','2fd29bcc-b6fc-81f2-a146-f01b94624ad8','a154cbcb-d124-4d4f-bda5-0b6995871439')
AND e_e_priority IS NULL;