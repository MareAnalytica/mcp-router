export interface HealthCheck {
  server_id: string;
  server_name: string;
  status: 'healthy' | 'unhealthy' | 'timeout' | 'error' | 'unknown';
  response_time_ms: number | null;
  error_message: string | null;
  checked_at: string;
}
