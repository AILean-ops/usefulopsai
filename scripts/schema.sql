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
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach_actions(status);
CREATE INDEX IF NOT EXISTS idx_suppressions_email ON suppressions(email);
CREATE INDEX IF NOT EXISTS idx_payment_links_status ON payment_links(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_revenue_external_id ON revenue(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_stripe_sync_runs_synced_at ON stripe_sync_runs(synced_at);
CREATE INDEX IF NOT EXISTS idx_dashboard_snapshots_snapshot_at ON dashboard_snapshots(snapshot_at);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_action_log_action_at ON action_log(action_at);
CREATE INDEX IF NOT EXISTS idx_operator_runs_status ON operator_runs(status);
CREATE INDEX IF NOT EXISTS idx_operator_runs_updated_at ON operator_runs(updated_at);
CREATE INDEX IF NOT EXISTS idx_operator_checkpoints_run_id ON operator_checkpoints(run_id);
