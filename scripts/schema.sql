PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS experiments (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  target_market TEXT,
  offer TEXT,
  authority_envelope TEXT,
  budget_limit_cents INTEGER DEFAULT 0,
  started_at TEXT,
  ended_at TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prospects (
  id TEXT PRIMARY KEY,
  experiment_id TEXT REFERENCES experiments(id),
  company TEXT NOT NULL,
  website TEXT,
  niche TEXT,
  city TEXT,
  state TEXT,
  country TEXT DEFAULT 'US',
  source TEXT,
  status TEXT NOT NULL DEFAULT 'not_researched',
  approval_state TEXT NOT NULL DEFAULT 'not_requested',
  pain_hypothesis TEXT,
  offer_fit TEXT,
  next_action TEXT,
  next_action_at TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contacts (
  id TEXT PRIMARY KEY,
  prospect_id TEXT NOT NULL REFERENCES prospects(id),
  name TEXT,
  role TEXT,
  email TEXT,
  phone TEXT,
  source TEXT,
  verification_status TEXT NOT NULL DEFAULT 'unverified',
  is_primary INTEGER NOT NULL DEFAULT 0,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS outreach_actions (
  id TEXT PRIMARY KEY,
  prospect_id TEXT NOT NULL REFERENCES prospects(id),
  contact_id TEXT REFERENCES contacts(id),
  channel TEXT NOT NULL,
  action_type TEXT NOT NULL,
  subject TEXT,
  body TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  approved_by TEXT,
  approved_at TEXT,
  sent_at TEXT,
  response_at TEXT,
  outcome TEXT,
  result_category TEXT,
  result_recorded_at TEXT,
  quality_score INTEGER,
  quality_notes TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS growth_batches (
  id TEXT PRIMARY KEY,
  experiment_id TEXT REFERENCES experiments(id),
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  hypothesis TEXT NOT NULL,
  target_niche TEXT,
  target_location TEXT,
  offer_angle TEXT,
  subject_pattern TEXT,
  cta TEXT,
  planned_count INTEGER NOT NULL DEFAULT 0,
  sent_count INTEGER NOT NULL DEFAULT 0,
  reply_count INTEGER NOT NULL DEFAULT 0,
  positive_reply_count INTEGER NOT NULL DEFAULT 0,
  opt_out_count INTEGER NOT NULL DEFAULT 0,
  undeliverable_count INTEGER NOT NULL DEFAULT 0,
  delivery_delay_count INTEGER NOT NULL DEFAULT 0,
  booked_count INTEGER NOT NULL DEFAULT 0,
  paid_count INTEGER NOT NULL DEFAULT 0,
  revenue_cents INTEGER NOT NULL DEFAULT 0,
  started_at TEXT,
  ended_at TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS growth_batch_items (
  id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL REFERENCES growth_batches(id),
  prospect_id TEXT NOT NULL REFERENCES prospects(id),
  outreach_action_id TEXT REFERENCES outreach_actions(id),
  status TEXT NOT NULL DEFAULT 'planned',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_reviews (
  id TEXT PRIMARY KEY,
  reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  scope TEXT NOT NULL DEFAULT 'daily',
  sends INTEGER NOT NULL DEFAULT 0,
  drafts INTEGER NOT NULL DEFAULT 0,
  replies INTEGER NOT NULL DEFAULT 0,
  positive_replies INTEGER NOT NULL DEFAULT 0,
  opt_outs INTEGER NOT NULL DEFAULT 0,
  undeliverable INTEGER NOT NULL DEFAULT 0,
  delivery_delayed INTEGER NOT NULL DEFAULT 0,
  booked INTEGER NOT NULL DEFAULT 0,
  paid INTEGER NOT NULL DEFAULT 0,
  revenue_cents INTEGER NOT NULL DEFAULT 0,
  diagnosis TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  next_action TEXT NOT NULL,
  metrics_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS learning_log (
  id TEXT PRIMARY KEY,
  learned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  source_type TEXT NOT NULL,
  source_id TEXT,
  lesson_type TEXT NOT NULL,
  finding TEXT NOT NULL,
  decision TEXT NOT NULL,
  confidence TEXT NOT NULL DEFAULT 'low',
  applies_to TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suppressions (
  id TEXT PRIMARY KEY,
  email TEXT,
  domain TEXT,
  prospect_id TEXT REFERENCES prospects(id),
  reason TEXT NOT NULL,
  source TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  request_type TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT,
  request_summary TEXT NOT NULL,
  exact_text_or_change TEXT,
  status TEXT NOT NULL DEFAULT 'requested',
  approved_by TEXT,
  approved_at TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clients (
  id TEXT PRIMARY KEY,
  prospect_id TEXT REFERENCES prospects(id),
  company TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  package TEXT,
  approved_scope TEXT,
  payment_status TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deliverables (
  id TEXT PRIMARY KEY,
  client_id TEXT NOT NULL REFERENCES clients(id),
  deliverable_type TEXT NOT NULL,
  title TEXT NOT NULL,
  file_path TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  approved_by TEXT,
  approved_at TEXT,
  delivered_at TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS revenue (
  id TEXT PRIMARY KEY,
  client_id TEXT REFERENCES clients(id),
  source TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  status TEXT NOT NULL DEFAULT 'pending',
  received_at TEXT,
  external_id TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stripe_sync_runs (
  id TEXT PRIMARY KEY,
  synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status TEXT NOT NULL,
  payment_links_seen INTEGER NOT NULL DEFAULT 0,
  checkout_sessions_seen INTEGER NOT NULL DEFAULT 0,
  subscriptions_seen INTEGER NOT NULL DEFAULT 0,
  gross_revenue_cents INTEGER NOT NULL DEFAULT 0,
  active_mrr_cents INTEGER NOT NULL DEFAULT 0,
  summary_json TEXT NOT NULL DEFAULT '{}',
  error TEXT
);

CREATE TABLE IF NOT EXISTS payment_links (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  stripe_url TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  billing_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intake_form_responses (
  response_id TEXT PRIMARY KEY,
  form_id TEXT NOT NULL,
  submitted_at TEXT,
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  alerted_at TEXT,
  alert_status TEXT NOT NULL DEFAULT 'pending',
  name TEXT,
  email TEXT,
  phone TEXT,
  business_name TEXT,
  website TEXT,
  business_type TEXT,
  team_size TEXT,
  urgency TEXT,
  pain_point TEXT,
  workflow_needing_help TEXT,
  tools_used TEXT,
  worth_fixing TEXT,
  raw_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS crm_leads (
  id TEXT PRIMARY KEY,
  dedupe_key TEXT NOT NULL UNIQUE,
  person_name TEXT,
  company TEXT,
  primary_email TEXT,
  primary_phone TEXT,
  website TEXT,
  business_type TEXT,
  stage TEXT NOT NULL DEFAULT 'new_inquiry',
  priority TEXT NOT NULL DEFAULT 'normal',
  owner TEXT NOT NULL DEFAULT 'rowan',
  source_first TEXT NOT NULL,
  source_latest TEXT NOT NULL,
  first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_source_record_id TEXT,
  intake_response_id TEXT REFERENCES intake_form_responses(response_id),
  prospect_id TEXT REFERENCES prospects(id),
  client_id TEXT REFERENCES clients(id),
  urgency TEXT,
  pain_point TEXT,
  workflow_needing_help TEXT,
  next_action TEXT,
  next_action_at TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crm_source_submissions (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  lead_id TEXT NOT NULL REFERENCES crm_leads(id),
  intake_response_id TEXT REFERENCES intake_form_responses(response_id),
  submitted_at TEXT,
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  alert_status TEXT,
  created_task_id TEXT REFERENCES tasks(id),
  payload_json TEXT NOT NULL DEFAULT '{}',
  notes TEXT,
  UNIQUE(source, source_record_id)
);

CREATE TABLE IF NOT EXISTS crm_stage_history (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES crm_leads(id),
  changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  from_stage TEXT,
  to_stage TEXT NOT NULL,
  actor TEXT NOT NULL DEFAULT 'rowan',
  reason TEXT NOT NULL,
  source_record_id TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS crm_touchpoints (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES crm_leads(id),
  occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  channel TEXT NOT NULL,
  direction TEXT NOT NULL,
  summary TEXT NOT NULL,
  source TEXT,
  source_record_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crm_opportunities (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES crm_leads(id),
  prospect_id TEXT REFERENCES prospects(id),
  client_id TEXT REFERENCES clients(id),
  name TEXT NOT NULL,
  stage TEXT NOT NULL DEFAULT 'new',
  value_cents INTEGER NOT NULL DEFAULT 0,
  probability INTEGER NOT NULL DEFAULT 0,
  next_action TEXT,
  next_action_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crm_integrity_checks (
  id TEXT PRIMARY KEY,
  checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status TEXT NOT NULL,
  source_submission_count INTEGER NOT NULL DEFAULT 0,
  lead_count INTEGER NOT NULL DEFAULT 0,
  open_followup_count INTEGER NOT NULL DEFAULT 0,
  missing_task_count INTEGER NOT NULL DEFAULT 0,
  duplicate_email_count INTEGER NOT NULL DEFAULT 0,
  details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS expenses (
  id TEXT PRIMARY KEY,
  vendor TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  status TEXT NOT NULL DEFAULT 'planned',
  category TEXT,
  approved_by TEXT,
  approved_at TEXT,
  incurred_at TEXT,
  recurring_interval TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dashboard_snapshots (
  id TEXT PRIMARY KEY,
  snapshot_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  gross_revenue_cents INTEGER NOT NULL DEFAULT 0,
  active_mrr_cents INTEGER NOT NULL DEFAULT 0,
  tax_reserve_cents INTEGER NOT NULL DEFAULT 0,
  brian_share_cents INTEGER NOT NULL DEFAULT 0,
  usefulops_growth_cents INTEGER NOT NULL DEFAULT 0,
  operator_discretion_cents INTEGER NOT NULL DEFAULT 0,
  budget_used_cents INTEGER NOT NULL DEFAULT 0,
  active_prospects INTEGER NOT NULL DEFAULT 0,
  cold_contacts_sent INTEGER NOT NULL DEFAULT 0,
  replies INTEGER NOT NULL DEFAULT 0,
  active_clients INTEGER NOT NULL DEFAULT 0,
  open_deliverables INTEGER NOT NULL DEFAULT 0,
  open_tasks INTEGER NOT NULL DEFAULT 0,
  metrics_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  priority TEXT NOT NULL DEFAULT 'normal',
  due_at TEXT,
  owner TEXT NOT NULL DEFAULT 'rowan',
  related_type TEXT,
  related_id TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS action_log (
  id TEXT PRIMARY KEY,
  action_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actor TEXT NOT NULL DEFAULT 'rowan',
  action_type TEXT NOT NULL,
  authority_basis TEXT,
  target_type TEXT,
  target_id TEXT,
  summary TEXT NOT NULL,
  external_effect INTEGER NOT NULL DEFAULT 0,
  cost_cents INTEGER DEFAULT 0,
  revenue_cents INTEGER DEFAULT 0,
  risk_notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operator_runs (
  id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  status TEXT NOT NULL DEFAULT 'running',
  trigger_source TEXT NOT NULL,
  objective TEXT NOT NULL,
  selected_task_id TEXT REFERENCES tasks(id),
  current_step TEXT NOT NULL DEFAULT 'started',
  next_action TEXT,
  summary TEXT,
  last_error TEXT,
  previous_run_id TEXT REFERENCES operator_runs(id),
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS operator_checkpoints (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES operator_runs(id),
  checkpoint_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  step TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'noted',
  summary TEXT NOT NULL,
  next_action TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status);
CREATE INDEX IF NOT EXISTS idx_prospects_approval_state ON prospects(approval_state);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_prospect_email ON contacts(prospect_id, email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach_actions(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_outreach_initial_email_prospect ON outreach_actions(prospect_id, action_type, channel) WHERE action_type = 'cold_initial' AND channel = 'email';
CREATE INDEX IF NOT EXISTS idx_growth_batches_status ON growth_batches(status);
CREATE INDEX IF NOT EXISTS idx_growth_batch_items_batch_id ON growth_batch_items(batch_id);
CREATE INDEX IF NOT EXISTS idx_strategy_reviews_reviewed_at ON strategy_reviews(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_learning_log_learned_at ON learning_log(learned_at);
CREATE INDEX IF NOT EXISTS idx_suppressions_email ON suppressions(email);
CREATE INDEX IF NOT EXISTS idx_payment_links_status ON payment_links(status);
CREATE INDEX IF NOT EXISTS idx_intake_form_submitted_at ON intake_form_responses(submitted_at);
CREATE INDEX IF NOT EXISTS idx_intake_form_alert_status ON intake_form_responses(alert_status);
CREATE INDEX IF NOT EXISTS idx_crm_leads_stage ON crm_leads(stage);
CREATE INDEX IF NOT EXISTS idx_crm_leads_email ON crm_leads(primary_email);
CREATE INDEX IF NOT EXISTS idx_crm_leads_company ON crm_leads(company);
CREATE INDEX IF NOT EXISTS idx_crm_leads_updated_at ON crm_leads(updated_at);
CREATE INDEX IF NOT EXISTS idx_crm_source_submissions_lead_id ON crm_source_submissions(lead_id);
CREATE INDEX IF NOT EXISTS idx_crm_source_submissions_intake_response_id ON crm_source_submissions(intake_response_id);
CREATE INDEX IF NOT EXISTS idx_crm_stage_history_lead_id ON crm_stage_history(lead_id);
CREATE INDEX IF NOT EXISTS idx_crm_touchpoints_lead_id ON crm_touchpoints(lead_id);
CREATE INDEX IF NOT EXISTS idx_crm_opportunities_lead_id ON crm_opportunities(lead_id);
CREATE INDEX IF NOT EXISTS idx_crm_integrity_checked_at ON crm_integrity_checks(checked_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_revenue_external_id ON revenue(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_stripe_sync_runs_synced_at ON stripe_sync_runs(synced_at);
CREATE INDEX IF NOT EXISTS idx_dashboard_snapshots_snapshot_at ON dashboard_snapshots(snapshot_at);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_action_log_action_at ON action_log(action_at);
CREATE INDEX IF NOT EXISTS idx_operator_runs_status ON operator_runs(status);
CREATE INDEX IF NOT EXISTS idx_operator_runs_updated_at ON operator_runs(updated_at);
CREATE INDEX IF NOT EXISTS idx_operator_checkpoints_run_id ON operator_checkpoints(run_id);
