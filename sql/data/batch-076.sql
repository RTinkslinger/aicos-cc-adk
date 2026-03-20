UPDATE network SET big_events_invite = CASE notion_page_id
  WHEN '11429bcc-b6fc-8084-8090-f8969833762e' THEN ARRAY['Yes']
  WHEN '11f29bcc-b6fc-805a-b4f3-e8f1441faafa' THEN ARRAY['Yes']
  WHEN '12629bcc-b6fc-8054-aed9-d21ddd48c1ec' THEN ARRAY['Yes']
  WHEN '12729bcc-b6fc-80a5-9406-feb6c6bf5c44' THEN ARRAY['Yes']
  WHEN '2aee9beb-5812-428a-8b1e-fb87293e5ee2' THEN ARRAY['Yes']
  WHEN '2eee0d36-5059-42c8-860c-2b09370f091e' THEN ARRAY['Yes']
  WHEN '4e1be440-cb28-45b2-a4b4-72e84f92cfb2' THEN ARRAY['Yes']
  WHEN '595f3992-75c9-4f09-a431-edd66a86eff8' THEN ARRAY['Yes']
  WHEN '6c22055b-2f52-4ac7-adff-7741d29ea1d6' THEN ARRAY['Yes']
  WHEN '7d11218d-d718-4817-8de1-af2e3c0a574e' THEN ARRAY['Yes']
  WHEN 'ba94197c-52c9-49f8-b187-f053e8a6d543' THEN ARRAY['Yes']
  WHEN 'bea803ad-2fc2-4b97-95a6-3ea1d4f61974' THEN ARRAY['Yes']
  WHEN 'e725a978-7ad0-4d84-a77c-9c4e1335d0ed' THEN ARRAY['Yes']
END, updated_at = now()
WHERE notion_page_id IN ('11429bcc-b6fc-8084-8090-f8969833762e','11f29bcc-b6fc-805a-b4f3-e8f1441faafa','12629bcc-b6fc-8054-aed9-d21ddd48c1ec','12729bcc-b6fc-80a5-9406-feb6c6bf5c44','2aee9beb-5812-428a-8b1e-fb87293e5ee2','2eee0d36-5059-42c8-860c-2b09370f091e','4e1be440-cb28-45b2-a4b4-72e84f92cfb2','595f3992-75c9-4f09-a431-edd66a86eff8','6c22055b-2f52-4ac7-adff-7741d29ea1d6','7d11218d-d718-4817-8de1-af2e3c0a574e','ba94197c-52c9-49f8-b187-f053e8a6d543','bea803ad-2fc2-4b97-95a6-3ea1d4f61974','e725a978-7ad0-4d84-a77c-9c4e1335d0ed')
AND big_events_invite IS NULL;