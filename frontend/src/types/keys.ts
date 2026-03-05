export interface ApiKey {
  key_name: string;
  created_at: string;
}

export interface ApiKeySet {
  keys: { key_name: string; value: string }[];
}
