import { Database, GitCompare, Link2, RefreshCw, Search, Table2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getDatabaseSchema, inspectDatabase, testProjectDatabaseConnection } from "../api/database";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";
import type { DatabaseForeignKey, DatabaseSchema, DatabaseTable } from "../types/database";
import type { PageKey } from "../types/navigation";
import type { ProjectListItem } from "../types/project";

interface DatabaseMapProps {
  t: Messages;
  projects: ProjectListItem[];
  selectedProjectId: number | null;
  onNavigate: (page: PageKey) => void;
}

export function DatabaseMap({ t, projects, selectedProjectId, onNavigate }: DatabaseMapProps) {
  const [schema, setSchema] = useState<DatabaseSchema | null>(null);
  const [selectedTableName, setSelectedTableName] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? null;

  async function loadSchema(projectId = selectedProjectId) {
    if (!projectId) {
      setSchema(null);
      setSelectedTableName(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await getDatabaseSchema(projectId);
      if (!response.ok || !response.schema) {
        setSchema(null);
        setError(response.message);
        return;
      }
      setSchema(response.schema);
      setSelectedTableName((current) => current ?? response.schema?.tables[0]?.name ?? null);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.databaseMap.inspectFailed);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSchema();
  }, [selectedProjectId]);

  async function refreshSchema() {
    if (!selectedProjectId) {
      return;
    }
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      const response = await inspectDatabase(selectedProjectId);
      if (!response.ok || !response.schema) {
        setSchema(null);
        setError(response.message);
        return;
      }
      setSchema(response.schema);
      setSelectedTableName(response.schema.tables[0]?.name ?? null);
      setMessage(t.databaseMap.schemaLoaded);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.databaseMap.inspectFailed);
    } finally {
      setLoading(false);
    }
  }

  async function testConnection() {
    if (!selectedProjectId) {
      return;
    }
    setMessage(null);
    setError(null);
    const result = await testProjectDatabaseConnection(selectedProjectId);
    if (result.ok) {
      setMessage(result.message);
    } else {
      setError(result.message);
    }
  }

  const filteredTables = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return (schema?.tables ?? []).filter(
      (table) => !normalizedSearch || table.name.toLowerCase().includes(normalizedSearch)
    );
  }, [schema, search]);

  const selectedTable =
    filteredTables.find((table) => table.name === selectedTableName) ?? filteredTables[0] ?? null;
  const relationCount = schema?.tables.reduce((total, table) => total + table.foreign_keys.length, 0) ?? 0;
  const totalRows = schema?.tables.reduce((total, table) => total + table.row_count, 0) ?? 0;

  if (!selectedProjectId || !selectedProject) {
    return (
      <section className="page-stack">
        <PageHeader subtitle={t.placeholders.databaseMapSubtitle} title={t.placeholders.databaseMapTitle} />
        <Card>
          <div className="empty-panel">
            <h2>{t.databaseMap.noProjectTitle}</h2>
            <p>{t.databaseMap.noProjectDescription}</p>
            <button className="primary-button" onClick={() => onNavigate("setup")} type="button">
              {t.nav.projectSetup}
            </button>
          </div>
        </Card>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <PageHeader
        actions={
          <div className="button-row">
            <button className="ghost-button" disabled={loading} onClick={() => void testConnection()} type="button">
              <Database size={17} />
              {t.databaseMap.testConnection}
            </button>
            <button className="primary-button" disabled={loading} onClick={() => void refreshSchema()} type="button">
              <RefreshCw size={17} />
              {loading ? t.common.checking : t.databaseMap.refreshSchema}
            </button>
          </div>
        }
        subtitle={t.placeholders.databaseMapSubtitle}
        title={t.placeholders.databaseMapTitle}
      />

      {message ? <div className="notice success">{message}</div> : null}
      {error ? <div className="notice danger">{error}</div> : null}

      {!schema ? (
        <Card>
          <div className="empty-panel">
            <h2>
              {loading
                ? t.databaseMap.loadingSchema
                : selectedProject.database_type === "none"
                ? t.databaseMap.noDatabaseTitle
                : t.databaseMap.inspectFailed}
            </h2>
            <p>
              {selectedProject.database_type === "none"
                ? t.databaseMap.noDatabaseDescription
                : error ?? t.databaseMap.noDatabaseDescription}
            </p>
            <button className="primary-button" onClick={() => onNavigate("setup")} type="button">
              {t.nav.projectSetup}
            </button>
          </div>
        </Card>
      ) : (
        <>
          <div className="stat-grid four">
            <StatCard
              icon={Database}
              title={t.databaseMap.databaseType}
              value={schema.database_type}
              hint={schema.database_name}
              tone="purple"
            />
            <StatCard
              icon={Table2}
              title={t.databaseMap.totalTables}
              value={schema.tables.length}
              hint={selectedProject.name}
              tone="blue"
            />
            <StatCard
              icon={Link2}
              title={t.databaseMap.relations}
              value={relationCount}
              hint={t.common.phaseNotice}
              tone="cyan"
            />
            <StatCard
              icon={GitCompare}
              title={t.databaseMap.totalRows}
              value={totalRows}
              hint={`${t.databaseMap.inspectedAt}: ${new Date(schema.inspected_at).toLocaleString()}`}
              tone="green"
            />
          </div>

          <div className="database-inspector-layout">
            <TableNavigator
              filteredTables={filteredTables}
              schema={schema}
              search={search}
              selectedTableName={selectedTable?.name ?? null}
              setSearch={setSearch}
              setSelectedTableName={setSelectedTableName}
              t={t}
            />
            <TableDetail schema={schema} table={selectedTable} t={t} />
          </div>
        </>
      )}
    </section>
  );
}

function TableNavigator({
  filteredTables,
  schema,
  search,
  selectedTableName,
  setSearch,
  setSelectedTableName,
  t
}: {
  filteredTables: DatabaseTable[];
  schema: DatabaseSchema;
  search: string;
  selectedTableName: string | null;
  setSearch: (value: string) => void;
  setSelectedTableName: (value: string) => void;
  t: Messages;
}) {
  return (
    <Card className="database-table-navigator">
      <div className="card-heading">
        <div>
          <h2>{t.databaseMap.tables}</h2>
          <p>{schema.database_type} / {schema.database_name}</p>
        </div>
        <StatusBadge tone="info">{schema.tables.length}</StatusBadge>
      </div>
      <label className="table-search database-search">
        <Search size={17} />
        <input
          onChange={(event) => setSearch(event.target.value)}
          placeholder={t.databaseMap.searchTables}
          value={search}
        />
      </label>
      <div className="database-table-list">
        {filteredTables.length === 0 ? (
          <div className="empty-panel compact">{t.databaseMap.noTables}</div>
        ) : (
          filteredTables.map((table) => (
            <button
              className={table.name === selectedTableName ? "database-table-item active" : "database-table-item"}
              key={table.name}
              onClick={() => setSelectedTableName(table.name)}
              type="button"
            >
              <div>
                <Table2 size={16} />
                <strong>{table.name}</strong>
              </div>
              <span>{table.row_count} rows</span>
              <em>{table.columns.length} fields</em>
              {table.foreign_keys.length > 0 ? <small>{table.foreign_keys.length} FK</small> : null}
            </button>
          ))
        )}
      </div>
    </Card>
  );
}

function TableDetail({ schema, table, t }: { schema: DatabaseSchema; table: DatabaseTable | null; t: Messages }) {
  if (!table) {
    return (
      <Card>
        <div className="empty-panel">{t.databaseMap.selectTable}</div>
      </Card>
    );
  }

  return (
    <div className="database-detail-stack">
      <StructurePreview schema={schema} selectedTable={table} t={t} />

      <Card>
        <div className="table-overview-hero">
          <div>
            <span>{t.databaseMap.tableOverview}</span>
            <h2>{table.name}</h2>
            <p>{t.databaseMap.rowCount}: {table.row_count}</p>
          </div>
          <StatusBadge tone="success">Table</StatusBadge>
        </div>
        <div className="table-overview-grid">
          <MetricPill label={t.databaseMap.columns} value={table.columns.length} />
          <MetricPill label={t.databaseMap.indexes} value={table.indexes.length} />
          <MetricPill label={t.databaseMap.foreignKeys} value={table.foreign_keys.length} />
          <MetricPill label={t.databaseMap.primaryKey} value={table.columns.filter((column) => column.primary_key).length} />
        </div>
      </Card>

      <Card>
        <SectionHeading title={t.databaseMap.columns} count={table.columns.length} />
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>{t.databaseMap.nullable}</th>
              <th>{t.databaseMap.defaultValue}</th>
              <th>{t.databaseMap.primaryKey}</th>
            </tr>
          </thead>
          <tbody>
            {table.columns.map((column) => (
              <tr key={column.name}>
                <td><strong>{column.name}</strong></td>
                <td>{column.type || "-"}</td>
                <td><StatusBadge tone={column.nullable ? "neutral" : "info"}>{column.nullable ? "YES" : "NO"}</StatusBadge></td>
                <td>{column.default == null ? "-" : String(column.default)}</td>
                <td>{column.primary_key ? <StatusBadge tone="info">PK</StatusBadge> : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card>
        <SectionHeading title={t.databaseMap.indexes} count={table.indexes.length} />
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>{t.databaseMap.columns}</th>
              <th>{t.databaseMap.unique}</th>
            </tr>
          </thead>
          <tbody>
            {table.indexes.length === 0 ? (
              <tr><td colSpan={3}>-</td></tr>
            ) : (
              table.indexes.map((index) => (
                <tr key={index.name}>
                  <td><strong>{index.name}</strong></td>
                  <td>{index.columns.join(", ") || "-"}</td>
                  <td>{index.unique ? <StatusBadge tone="success">{t.databaseMap.unique}</StatusBadge> : "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>

      <Card>
        <SectionHeading title={t.databaseMap.foreignKeys} count={table.foreign_keys.length} />
        <table className="data-table">
          <thead>
            <tr>
              <th>{t.databaseMap.columns}</th>
              <th>{t.databaseMap.referencedTable}</th>
              <th>{t.databaseMap.referencedColumn}</th>
            </tr>
          </thead>
          <tbody>
            {table.foreign_keys.length === 0 ? (
              <tr><td colSpan={3}>-</td></tr>
            ) : (
              table.foreign_keys.map((foreignKey) => (
                <tr key={`${foreignKey.column}-${foreignKey.referenced_table}-${foreignKey.referenced_column}`}>
                  <td><strong>{foreignKey.column}</strong></td>
                  <td>{foreignKey.referenced_table}</td>
                  <td>{foreignKey.referenced_column}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>

      <Card>
        <SectionHeading title={t.databaseMap.sampleRows} count={table.sample_rows.length} />
        <SampleRowsTable rows={table.sample_rows} t={t} />
      </Card>
    </div>
  );
}

interface TableRelationship {
  fromColumn: string;
  fromTable: string;
  relatedToSelected: boolean;
  toColumn: string;
  toTable: string;
}

function StructurePreview({
  schema,
  selectedTable,
  t
}: {
  schema: DatabaseSchema;
  selectedTable: DatabaseTable;
  t: Messages;
}) {
  const relationships = getRelationships(schema, selectedTable.name);
  const visibleRelationships = relationships.slice(0, 8);

  return (
    <Card className="structure-preview-card">
      <div className="structure-preview-heading">
        <div>
          <span>{t.databaseMap.schemaOverview}</span>
          <h2>{t.databaseMap.structurePreview}</h2>
          <p>{t.databaseMap.structurePreviewHint}</p>
        </div>
        <StatusBadge tone={relationships.length > 0 ? "info" : "neutral"}>
          {relationships.length}
        </StatusBadge>
      </div>

      {relationships.length === 0 ? (
        <div className="empty-panel compact">{t.databaseMap.noRelationships}</div>
      ) : (
        <div className="relationship-list">
          {visibleRelationships.map((relationship) => (
            <div
              className={relationship.relatedToSelected ? "relationship-card active" : "relationship-card"}
              key={`${relationship.fromTable}.${relationship.fromColumn}-${relationship.toTable}.${relationship.toColumn}`}
            >
              <div className="relationship-node" title={`${relationship.fromTable}.${relationship.fromColumn}`}>
                <strong>{relationship.fromTable}</strong>
                <span>{relationship.fromColumn}</span>
              </div>
              <div className="relationship-arrow">-&gt;</div>
              <div className="relationship-node" title={`${relationship.toTable}.${relationship.toColumn}`}>
                <strong>{relationship.toTable}</strong>
                <span>{relationship.toColumn}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function getRelationships(schema: DatabaseSchema, selectedTableName: string): TableRelationship[] {
  const allRelationships = schema.tables.flatMap((table) =>
    table.foreign_keys.map((foreignKey: DatabaseForeignKey) => ({
      fromColumn: foreignKey.column,
      fromTable: table.name,
      relatedToSelected: table.name === selectedTableName || foreignKey.referenced_table === selectedTableName,
      toColumn: foreignKey.referenced_column,
      toTable: foreignKey.referenced_table
    }))
  );
  const selectedRelationships = allRelationships.filter((relationship) => relationship.relatedToSelected);
  return selectedRelationships.length > 0 ? selectedRelationships : allRelationships;
}

function MetricPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-pill">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SectionHeading({ count, title }: { count: number; title: string }) {
  return (
    <div className="section-heading compact-section-heading">
      <h2>{title}</h2>
      <StatusBadge tone="neutral">{count}</StatusBadge>
    </div>
  );
}

function SampleRowsTable({ rows, t }: { rows: Record<string, unknown>[]; t: Messages }) {
  const [showAllColumns, setShowAllColumns] = useState(false);
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  const compactColumnLimit = 8;
  const visibleColumns = showAllColumns ? columns : columns.slice(0, compactColumnLimit);
  if (rows.length === 0 || columns.length === 0) {
    return <div className="empty-panel compact">{t.databaseMap.sampleRowsEmpty}</div>;
  }

  return (
    <>
      <div className="sample-column-toolbar">
        <span>
          {t.databaseMap.showingColumns}: {visibleColumns.length}/{columns.length}
        </span>
        {columns.length > compactColumnLimit ? (
          <button className="ghost-button small" onClick={() => setShowAllColumns((value) => !value)} type="button">
            {showAllColumns ? t.databaseMap.showFewerColumns : t.databaseMap.showMoreColumns}
          </button>
        ) : null}
      </div>
      <div className="sample-table-scroll">
        <table className="data-table sample-data-table">
          <thead>
            <tr>
              {visibleColumns.map((column) => (
                <th key={column} title={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {visibleColumns.map((column) => (
                  <td key={column} title={formatCell(row[column])}>
                    {formatCell(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
