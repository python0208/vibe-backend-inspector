import { Database, GitCompare, Link2, RefreshCw, Search, Table2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getDatabaseSchema, inspectDatabase, testProjectDatabaseConnection } from "../api/database";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge } from "../components/ui/StatusBadge";
import type { Messages } from "../i18n";
import type { DatabaseSchema, DatabaseTable } from "../types/database";
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
              {t.databaseMap.refreshSchema}
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
              {selectedProject.database_type === "none"
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

          <div className="database-grid">
            <Card>
              <div className="card-heading">
                <h2>{t.databaseMap.tables}</h2>
                <StatusBadge tone="info">{filteredTables.length}</StatusBadge>
              </div>
              <label className="table-search database-search">
                <Search size={17} />
                <input
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder={t.databaseMap.searchTables}
                  value={search}
                />
              </label>
              <div className="table-list">
                {filteredTables.map((table) => (
                  <button
                    className={table.name === selectedTable?.name ? "table-row active" : "table-row"}
                    key={table.name}
                    onClick={() => setSelectedTableName(table.name)}
                    type="button"
                  >
                    <Table2 size={16} />
                    {table.name}
                    <span>{table.row_count} rows</span>
                  </button>
                ))}
              </div>
            </Card>

            <SchemaOverview schema={schema} t={t} />
            <TableDetail table={selectedTable} t={t} />
          </div>
        </>
      )}
    </section>
  );
}

function SchemaOverview({ schema, t }: { schema: DatabaseSchema; t: Messages }) {
  const relations = schema.tables.flatMap((table) =>
    table.foreign_keys.map((foreignKey) => ({
      from: `${table.name}.${foreignKey.column}`,
      to: `${foreignKey.referenced_table}.${foreignKey.referenced_column}`
    }))
  );

  return (
    <Card className="schema-canvas real-schema">
      <div className="card-heading floating-heading">
        <h2>{t.databaseMap.schemaOverview}</h2>
        <StatusBadge tone="info">{schema.tables.length}</StatusBadge>
      </div>
      <div className="schema-card-grid">
        {schema.tables.slice(0, 8).map((table) => (
          <div className="schema-table-card" key={table.name}>
            <strong>{table.name}</strong>
            <span>{table.row_count} rows</span>
            <ul>
              {table.columns.slice(0, 4).map((column) => (
                <li key={column.name}>
                  {column.name}
                  {column.primary_key ? <StatusBadge tone="info">PK</StatusBadge> : null}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="relation-list">
        {relations.length === 0 ? (
          <p>{t.databaseMap.foreignKeys}: 0</p>
        ) : (
          relations.map((relation) => (
            <p key={`${relation.from}-${relation.to}`}>
              {relation.from} → {relation.to}
            </p>
          ))
        )}
      </div>
    </Card>
  );
}

function TableDetail({ table, t }: { table: DatabaseTable | null; t: Messages }) {
  if (!table) {
    return (
      <Card>
        <div className="empty-panel">{t.databaseMap.selectTable}</div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="card-heading">
        <div>
          <h2>{table.name}</h2>
          <p>
            {t.databaseMap.rowCount}: {table.row_count}
          </p>
        </div>
        <StatusBadge tone="success">Table</StatusBadge>
      </div>

      <DetailSection title={t.databaseMap.columns}>
        <table className="data-table">
          <thead>
            <tr>
              <th>{t.projectSetup.projectName}</th>
              <th>Type</th>
              <th>{t.databaseMap.nullable}</th>
              <th>{t.databaseMap.primaryKey}</th>
              <th>{t.databaseMap.defaultValue}</th>
            </tr>
          </thead>
          <tbody>
            {table.columns.map((column) => (
              <tr key={column.name}>
                <td>{column.name}</td>
                <td>{column.type || "-"}</td>
                <td>{column.nullable ? "YES" : "NO"}</td>
                <td>{column.primary_key ? <StatusBadge tone="info">PK</StatusBadge> : "-"}</td>
                <td>{column.default == null ? "-" : String(column.default)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </DetailSection>

      <DetailSection title={t.databaseMap.indexes}>
        <table className="data-table">
          <tbody>
            {table.indexes.length === 0 ? (
              <tr><td>-</td></tr>
            ) : (
              table.indexes.map((index) => (
                <tr key={index.name}>
                  <td>{index.name}</td>
                  <td>{index.columns.join(", ") || "-"}</td>
                  <td>{index.unique ? <StatusBadge tone="success">{t.databaseMap.unique}</StatusBadge> : "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </DetailSection>

      <DetailSection title={t.databaseMap.foreignKeys}>
        <table className="data-table">
          <tbody>
            {table.foreign_keys.length === 0 ? (
              <tr><td>-</td></tr>
            ) : (
              table.foreign_keys.map((foreignKey) => (
                <tr key={`${foreignKey.column}-${foreignKey.referenced_table}-${foreignKey.referenced_column}`}>
                  <td>{foreignKey.column}</td>
                  <td>{foreignKey.referenced_table}</td>
                  <td>{foreignKey.referenced_column}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </DetailSection>

      <DetailSection title={t.databaseMap.sampleRows}>
        <div className="code-block">{JSON.stringify(table.sample_rows, null, 2)}</div>
      </DetailSection>
    </Card>
  );
}

function DetailSection({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <section className="detail-section">
      <h3 className="schema-title">{title}</h3>
      {children}
    </section>
  );
}
