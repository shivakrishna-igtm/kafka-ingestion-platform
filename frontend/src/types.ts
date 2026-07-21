export type Role = "viewer" | "producer" | "admin";

export interface Session {
  token: string;
  username: string;
  role: Role;
}

export interface FieldDef {
  name: string;
  type: string;
  required: boolean;
}

export interface SchemaVersion {
  version: number;
  definition: { fields: FieldDef[] };
  created_by: string;
  created_at: string;
}

export interface Topic {
  id: number;
  name: string;
  description: string;
  owner_team: string;
  created_by: string;
  created_at: string;
  latest_version: number;
  schemas: SchemaVersion[];
}

export interface ColumnDef {
  name: string;
  snowflake_type: string;
  nullable: boolean;
}

export interface PreviewResult {
  columns: ColumnDef[];
  rows: Record<string, string>[];
  warnings: string[];
  create_table_ddl: string;
  copy_into_sql: string;
}

export interface CompatibilityResult {
  compatible: boolean;
  breaking_changes: string[];
  safe_changes: string[];
}
