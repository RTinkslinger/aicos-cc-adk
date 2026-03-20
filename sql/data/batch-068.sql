UPDATE network SET engagement_playbook = CASE notion_page_id
  WHEN '6c22055b-2f52-4ac7-adff-7741d29ea1d6' THEN ARRAY['Programmatic Dealflow']
  WHEN 'dbdffe0b-bd73-443a-aa12-02974339d639' THEN ARRAY['Solo Capitalist']
END, updated_at = now()
WHERE notion_page_id IN ('6c22055b-2f52-4ac7-adff-7741d29ea1d6','dbdffe0b-bd73-443a-aa12-02974339d639')
AND engagement_playbook IS NULL;