export interface IDPSystem {
  id: string;
  name: string;
  description: string;
  version: string;
  endpoint?: string;
}

export interface MigrationJob {
  id: string;
  source_system: string;
  destination_system: string;
  migration_type: 'one_time' | 'runtime';
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'paused';
  created_at: string;
  updated_at: string;
  progress_percentage: number;
  total_records: number;
  migrated_records: number;
  failed_records: number;
  error_message?: string;
  estimated_completion?: string;
}

export interface MigrationRequest {
  source_system: string;
  destination_system: string;
  migration_type: 'one_time' | 'runtime';
  batch_size?: number;
  include_historical?: boolean;
  transformation_rules?: Record<string, any>;
}

export interface DashboardStats {
  total_jobs: number;
  completed_jobs: number;
  in_progress_jobs: number;
  failed_jobs: number;
  total_migrated_records: number;
  total_failed_records: number;
  success_rate: number;
}

export interface SystemConfig {
  system_type: string;
  endpoint_url: string;
  api_key: string;
  connection_timeout: number;
  batch_size: number;
  rate_limit: number;
}

export interface UserRecord {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
  last_login?: string;
  is_active: boolean;
  roles: string[];
  attributes: Record<string, any>;
}