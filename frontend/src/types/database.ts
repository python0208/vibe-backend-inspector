export interface DatabaseColumn {
  name: string;
  type?: string | null;
  nullable: boolean;
  default?: unknown;
  primary_key: boolean;
}

export interface DatabaseIndex {
  name: string;
  columns: string[];
  unique: boolean;
}

export interface DatabaseForeignKey {
  column: string;
  referenced_table: string;
  referenced_column: string;
}

export interface DatabaseTable {
  name: string;
  row_count: number;
  columns: DatabaseColumn[];
  indexes: DatabaseIndex[];
  foreign_keys: DatabaseForeignKey[];
  sample_rows: Record<string, unknown>[];
}

export interface DatabaseSchema {
  project_id: number;
  database_type: string;
  database_name: string;
  inspected_at: string;
  tables: DatabaseTable[];
}

export interface DatabaseInspectResponse {
  ok: boolean;
  message: string;
  schema?: DatabaseSchema | null;
}

export interface DatabaseProjectConnectionTestResponse {
  ok: boolean;
  message: string;
  database_type: string;
}
