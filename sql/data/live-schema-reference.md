# Live Supabase Schema Reference
*Dumped: 2026-03-20 from project `llfkxnsfczludgigknbs`*

---

## portfolio (80 columns)

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` | integer | NO | nextval('portfolio_id_seq') |
| 2 | `notion_page_id` | text | YES | - |
| 3 | `portfolio_co` | text | NO | - |
| 4 | `company_name_id` | text | YES | - |
| 5 | `led_by_ids` | text[] | YES | '{}' |
| 6 | `sourcing_attribution_ids` | text[] | YES | '{}' |
| 7 | `participation_attribution_ids` | text[] | YES | '{}' |
| 8 | `venture_partner_old_ids` | text[] | YES | '{}' |
| 9 | `meeting_notes_ids` | text[] | YES | '{}' |
| 10 | `introduced_to_ids` | text[] | YES | '{}' |
| 11 | `ip_assigned` | text[] | YES | '{}' |
| 12 | `md_assigned` | text[] | YES | '{}' |
| 13 | `five_hundred_k_candidate` | text | YES | '' |
| 14 | `aif_usa` | text | YES | '' |
| 15 | `bu_follow_on_tag` | text | YES | '' |
| 16 | `check_in_cadence` | text | YES | '' |
| 17 | `current_stage` | text | YES | '' |
| 18 | `deep_dive` | text | YES | '' |
| 19 | `ef_eo` | text | YES | '' |
| 20 | `follow_on_decision` | text | YES | '' |
| 21 | `follow_on_decision_alt` | text | YES | '' |
| 22 | `hc_priority` | text | YES | '' |
| 23 | `health` | text | YES | '' |
| 24 | `ip_pull` | text | YES | '' |
| 25 | `investment_timeline` | text | YES | '' |
| 26 | `likely_follow_on_decision` | text | YES | '' |
| 27 | `next_3m_ic_candidate` | text | YES | '' |
| 28 | `ops_prio` | text | YES | '' |
| 29 | `outcome_category` | text | YES | '' |
| 30 | `raised_follow_on_funding` | text | YES | '' |
| 31 | `referenceability` | text | YES | '' |
| 32 | `revenue_generating` | text | YES | '' |
| 33 | `round_1_type` | text | YES | '' |
| 34 | `round_2_type` | text | YES | '' |
| 35 | `round_3_type` | text | YES | '' |
| 36 | `spikey` | text | YES | '' |
| 37 | `stage_at_entry` | text | YES | '' |
| 38 | `tier_1_marquee_cap_table` | text | YES | '' |
| 39 | `today` | text | YES | '' |
| 40 | `uw_decision` | text | YES | '' |
| 41 | `fy23_24_compliance` | text[] | YES | '{}' |
| 42 | `follow_on_outcome` | text[] | YES | '{}' |
| 43 | `follow_on_work_priority` | text[] | YES | '{}' |
| 44 | `next_round_status` | text[] | YES | '{}' |
| 45 | `pstatus` | text[] | YES | '{}' |
| 46 | `timing_of_involvement` | text[] | YES | '{}' |
| 47 | `entry_cheque` | numeric | YES | - |
| 48 | `entry_round_raise` | numeric | YES | - |
| 49 | `entry_round_valuation` | numeric | YES | - |
| 50 | `last_round_valuation` | numeric | YES | - |
| 51 | `fmv_carried` | numeric | YES | - |
| 52 | `bu_reserve_defend` | numeric | YES | - |
| 53 | `bu_reserve_no_defend` | numeric | YES | - |
| 54 | `earmarked_reserves` | numeric | YES | - |
| 55 | `reserve_committed` | numeric | YES | - |
| 56 | `reserve_deployed` | numeric | YES | - |
| 57 | `fresh_committed` | numeric | YES | - |
| 58 | `cash_in_bank` | numeric | YES | - |
| 59 | `room_to_deploy` | numeric | YES | - |
| 60 | `round_2_raise` | numeric | YES | - |
| 61 | `round_2_val` | numeric | YES | - |
| 62 | `round_3_raise` | numeric | YES | - |
| 63 | `round_3_val` | numeric | YES | - |
| 64 | `best_case_outcome` | numeric | YES | - |
| 65 | `good_case_outcome` | numeric | YES | - |
| 66 | `likely_outcome` | numeric | YES | - |
| 67 | `ownership_pct` | real | YES | - |
| 68 | `dilution_if_defend` | real | YES | - |
| 69 | `dilution_if_no_defend` | real | YES | - |
| 70 | `external_signal` | text | YES | '' |
| 71 | `high_impact` | text | YES | '' |
| 72 | `key_questions` | text | YES | '' |
| 73 | `note_on_deployment` | text | YES | '' |
| 74 | `scale_of_business` | text | YES | '' |
| 75 | `action_due_date` | date | YES | - |
| 76 | `fumes_date` | date | YES | - |
| 77 | `notion_last_edited` | timestamptz | YES | - |
| 78 | `research_file_path` | text | YES | - |
| 79 | `enrichment_metadata` | jsonb | YES | '{}' |
| 80 | `signal_history` | jsonb | YES | '[]' |
| 81 | `created_at` | timestamptz | YES | now() |
| 82 | `updated_at` | timestamptz | YES | now() |
| 83 | `last_synced_at` | timestamptz | YES | - |

### Relation columns (text[] storing Notion page IDs)
- `led_by_ids` -- Network DB page IDs
- `sourcing_attribution_ids` -- Network DB page IDs
- `participation_attribution_ids` -- Network DB page IDs
- `venture_partner_old_ids` -- Network DB page IDs
- `meeting_notes_ids` -- Meeting Notes page IDs
- `introduced_to_ids` -- Network DB page IDs
- `ip_assigned` -- Network DB page IDs
- `md_assigned` -- Network DB page IDs

### Multi-select columns (text[] storing tag values, NOT page IDs)
- `fy23_24_compliance`
- `follow_on_outcome`
- `follow_on_work_priority`
- `next_round_status`
- `pstatus`
- `timing_of_involvement`

---

## network (50 columns)

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` | integer | NO | nextval('network_id_seq') |
| 2 | `notion_page_id` | text | YES | - |
| 3 | `person_name` | text | NO | - |
| 4 | `current_role` | text | YES | - |
| 5 | `home_base` | text[] | YES | '{}' |
| 6 | `linkedin` | text | YES | - |
| 7 | `ryg` | text | YES | - |
| 8 | `e_e_priority` | text | YES | - |
| 9 | `sourcing_flow_hots` | text | YES | - |
| 10 | `investing_activity` | text | YES | - |
| 11 | `devc_relationship` | text[] | YES | '{}' |
| 12 | `collective_flag` | text[] | YES | '{}' |
| 13 | `engagement_playbook` | text[] | YES | '{}' |
| 14 | `leverage` | text[] | YES | '{}' |
| 15 | `customer_for` | text[] | YES | '{}' |
| 16 | `investorship` | text[] | YES | '{}' |
| 17 | `prev_foundership` | text[] | YES | '{}' |
| 18 | `folio_franchise` | text[] | YES | '{}' |
| 19 | `operating_franchise` | text[] | YES | '{}' |
| 20 | `big_events_invite` | text[] | YES | '{}' |
| 21 | `in_folio_of` | text[] | YES | '{}' |
| 22 | `local_network_tags` | text[] | YES | '{}' |
| 23 | `saas_buyer_type` | text[] | YES | '{}' |
| 24 | `current_company_ids` | text[] | YES | '{}' |
| 25 | `past_company_ids` | text[] | YES | '{}' |
| 26 | `agent_interaction_summaries` | jsonb | YES | '[]' |
| 27 | `meeting_context` | jsonb | YES | '[]' |
| 28 | `content_connections` | jsonb | YES | '[]' |
| 29 | `signal_history` | jsonb | YES | '[]' |
| 30 | `enrichment_metadata` | jsonb | YES | '{}' |
| 31 | `created_at` | timestamptz | YES | now() |
| 32 | `updated_at` | timestamptz | YES | now() |
| 33 | `last_synced_at` | timestamptz | YES | - |
| 34 | `notion_last_edited` | timestamptz | YES | - |
| 35 | `school_ids` | text[] | YES | '{}' |
| 36 | `angel_folio_ids` | text[] | YES | '{}' |
| 37 | `sourcing_attribution_ids` | text[] | YES | '{}' |
| 38 | `participation_attribution_ids` | text[] | YES | '{}' |
| 39 | `led_by_ids` | text[] | YES | '{}' |
| 40 | `piped_to_devc_ids` | text[] | YES | '{}' |
| 41 | `yc_partner_portfolio_ids` | text[] | YES | '{}' |
| 42 | `ce_speaker_ids` | text[] | YES | '{}' |
| 43 | `ce_attendance_ids` | text[] | YES | '{}' |
| 44 | `meeting_note_ids` | text[] | YES | '{}' |
| 45 | `task_pending_ids` | text[] | YES | '{}' |
| 46 | `devc_poc` | text | YES | '' |
| 47 | `ids_notes` | text | YES | '' |
| 48 | `last_interaction` | date | YES | - |
| 49 | `email` | text | YES | '' |
| 50 | `phone` | text | YES | '' |
| 51 | `relationship_status` | text | YES | '' |
| 52 | `source` | text | YES | '' |

### Relation columns (text[] storing Notion page IDs)
- `current_company_ids` -- Companies DB page IDs
- `past_company_ids` -- Companies DB page IDs
- `school_ids` -- page IDs
- `angel_folio_ids` -- Companies/Portfolio page IDs
- `sourcing_attribution_ids` -- Portfolio DB page IDs
- `participation_attribution_ids` -- Portfolio DB page IDs
- `led_by_ids` -- Portfolio DB page IDs
- `piped_to_devc_ids` -- Companies DB page IDs
- `yc_partner_portfolio_ids` -- Portfolio DB page IDs
- `ce_speaker_ids` -- page IDs (Collective Events)
- `ce_attendance_ids` -- page IDs (Collective Events)
- `meeting_note_ids` -- Meeting Notes page IDs
- `task_pending_ids` -- Tasks page IDs

### Multi-select columns (text[] storing tag values, NOT page IDs)
- `home_base`
- `devc_relationship`
- `collective_flag`
- `engagement_playbook`
- `leverage`
- `customer_for`
- `investorship`
- `prev_foundership`
- `folio_franchise`
- `operating_franchise`
- `big_events_invite`
- `in_folio_of`
- `local_network_tags`
- `saas_buyer_type`

---

## companies (54 columns)

| # | Column | Type | Nullable | Default |
|---|--------|------|----------|---------|
| 1 | `id` | integer | NO | nextval('companies_id_seq') |
| 2 | `notion_page_id` | text | YES | - |
| 3 | `name` | text | NO | - |
| 4 | `deal_status` | text | YES | '' |
| 5 | `deal_status_at_discovery` | text | YES | '' |
| 6 | `pipeline_status` | text | YES | '' |
| 7 | `type` | text | YES | '' |
| 8 | `sector` | text | YES | '' |
| 9 | `sector_tags` | text[] | YES | '{}' |
| 10 | `priority` | text | YES | '' |
| 11 | `founding_timeline` | text | YES | '' |
| 12 | `venture_funding` | text | YES | '' |
| 13 | `last_round_amount` | real | YES | - |
| 14 | `last_round_timing` | text | YES | '' |
| 15 | `smart_money` | text | YES | '' |
| 16 | `hil_review` | text | YES | '' |
| 17 | `jtbd` | text[] | YES | '{}' |
| 18 | `sells_to` | text[] | YES | '{}' |
| 19 | `batch` | text[] | YES | '{}' |
| 20 | `website` | text | YES | '' |
| 21 | `deck_link` | text | YES | '' |
| 22 | `vault_link` | text | YES | '' |
| 23 | `agent_ids_notes` | text | YES | '' |
| 24 | `content_connections` | jsonb | YES | '[]' |
| 25 | `thesis_thread_links` | jsonb | YES | '[]' |
| 26 | `signal_history` | jsonb | YES | '[]' |
| 27 | `computed_conviction_score` | real | YES | - |
| 28 | `enrichment_metadata` | jsonb | YES | '{}' |
| 29 | `created_at` | timestamptz | YES | now() |
| 30 | `updated_at` | timestamptz | YES | now() |
| 31 | `last_synced_at` | timestamptz | YES | - |
| 32 | `notion_last_edited` | timestamptz | YES | - |
| 33 | `money_committed` | real | YES | - |
| 34 | `action_due` | date | YES | - |
| 35 | `surface_to_collective` | date | YES | - |
| 36 | `devc_ip_poc` | text | YES | '' |
| 37 | `current_people_ids` | text[] | YES | '{}' |
| 38 | `angel_ids` | text[] | YES | '{}' |
| 39 | `alum_ids` | text[] | YES | '{}' |
| 40 | `mpi_connect_ids` | text[] | YES | '{}' |
| 41 | `domain_eval_ids` | text[] | YES | '{}' |
| 42 | `piped_from_ids` | text[] | YES | '{}' |
| 43 | `met_by_ids` | text[] | YES | '{}' |
| 44 | `shared_with_ids` | text[] | YES | '{}' |
| 45 | `yc_partner_ids` | text[] | YES | '{}' |
| 46 | `network_ids` | text[] | YES | '{}' |
| 47 | `investor_company_ids` | text[] | YES | '{}' |
| 48 | `known_portfolio_ids` | text[] | YES | '{}' |
| 49 | `finance_notion_ids` | text[] | YES | '{}' |
| 50 | `corp_dev_notion_ids` | text[] | YES | '{}' |
| 51 | `portfolio_notion_ids` | text[] | YES | '{}' |
| 52 | `meeting_note_ids` | text[] | YES | '{}' |
| 53 | `pending_task_ids` | text[] | YES | '{}' |
| 54 | `embedding` | vector | YES | - |
| 55 | `fts` | tsvector | YES | - |

### Relation columns (text[] storing Notion page IDs)
- `current_people_ids` -- Network DB page IDs
- `angel_ids` -- Network DB page IDs
- `alum_ids` -- Network DB page IDs
- `mpi_connect_ids` -- Network DB page IDs
- `domain_eval_ids` -- Network DB page IDs
- `piped_from_ids` -- Network DB page IDs
- `met_by_ids` -- Network DB page IDs
- `shared_with_ids` -- Network DB page IDs
- `yc_partner_ids` -- Network DB page IDs
- `network_ids` -- Network DB page IDs
- `investor_company_ids` -- Companies DB page IDs (self-referencing)
- `known_portfolio_ids` -- Portfolio DB page IDs
- `finance_notion_ids` -- page IDs
- `corp_dev_notion_ids` -- page IDs
- `portfolio_notion_ids` -- Portfolio DB page IDs
- `meeting_note_ids` -- Meeting Notes page IDs
- `pending_task_ids` -- Tasks page IDs

### Multi-select columns (text[] storing tag values, NOT page IDs)
- `sector_tags`
- `jtbd`
- `sells_to`
- `batch`

### Special columns
- `embedding` -- pgvector column (vector type) for semantic search
- `fts` -- tsvector column for full-text search

---

## Cross-table column summary

### Columns present on ALL 3 tables
| Column | Type | Purpose |
|--------|------|---------|
| `id` | integer | Auto-increment PK |
| `notion_page_id` | text | Notion page UUID (join key) |
| `enrichment_metadata` | jsonb | Agent enrichment tracking |
| `signal_history` | jsonb | Timestamped signal log |
| `created_at` | timestamptz | Row creation time |
| `updated_at` | timestamptz | Row update time |
| `last_synced_at` | timestamptz | Last Notion sync time |
| `notion_last_edited` | timestamptz | Last Notion edit time |

### Enrichment agent write targets
Enrichment agents should write to these columns:
- **Any `*_ids` column** -- relation arrays (text[] of Notion page UUIDs)
- **`enrichment_metadata`** -- track what was enriched, when, by which agent
- **`signal_history`** -- append timestamped signals
- **`content_connections`** (network, companies) -- link to content digest items
- **`thesis_thread_links`** (companies) -- link to thesis threads
- **`agent_interaction_summaries`** (network) -- meeting/interaction summaries
- **`meeting_context`** (network) -- structured meeting context
- **`agent_ids_notes`** (companies) -- agent-generated IDS notes
- **`research_file_path`** (portfolio) -- path to local research file
- **`computed_conviction_score`** (companies) -- agent-computed score
