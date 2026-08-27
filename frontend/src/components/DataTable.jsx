function DataTable({
  columns = [],
  data = [],
  loading = false,
  emptyMessage = "No records found.",
  onEdit,
  onDelete,
}) {
  if (loading) {
    return (
      <div
        style={{
          padding: "40px",
          textAlign: "center",
          color: "#64748b",
        }}
      >
        Loading...
      </div>
    );
  }

  return (
    <div
      style={{
        width: "100%",
        overflowX: "auto",
      }}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          minWidth: "750px",
        }}
      >
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                style={{
                  padding: "14px 16px",
                  textAlign: "left",
                  fontSize: "12px",
                  fontWeight: "700",
                  color: "#64748b",
                  background: "#f8fafc",
                  borderBottom: "1px solid #e2e8f0",
                  whiteSpace: "nowrap",
                }}
              >
                {column.label}
              </th>
            ))}

            {(onEdit || onDelete) && (
              <th
                style={{
                  padding: "14px 16px",
                  textAlign: "right",
                  fontSize: "12px",
                  fontWeight: "700",
                  color: "#64748b",
                  background: "#f8fafc",
                  borderBottom: "1px solid #e2e8f0",
                }}
              >
                Actions
              </th>
            )}
          </tr>
        </thead>

        <tbody>
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={
                  columns.length + (onEdit || onDelete ? 1 : 0)
                }
                style={{
                  padding: "45px 20px",
                  textAlign: "center",
                  color: "#94a3b8",
                  fontSize: "13px",
                }}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr key={row.id ?? index}>
                {columns.map((column) => (
                  <td
                    key={column.key}
                    style={{
                      padding: "14px 16px",
                      color: "#334155",
                      fontSize: "13px",
                      borderBottom: "1px solid #f1f5f9",
                    }}
                  >
                    {column.render
                      ? column.render(row)
                      : row[column.key] ?? "-"}
                  </td>
                ))}

                {(onEdit || onDelete) && (
                  <td
                    style={{
                      padding: "14px 16px",
                      textAlign: "right",
                      borderBottom: "1px solid #f1f5f9",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {onEdit && (
                      <button
                        onClick={() => onEdit(row)}
                        style={{
                          marginRight: "8px",
                          padding: "7px 11px",
                          border: "1px solid #c7d2fe",
                          borderRadius: "7px",
                          background: "#eef2ff",
                          color: "#4f46e5",
                          cursor: "pointer",
                          fontSize: "12px",
                          fontWeight: "600",
                        }}
                      >
                        Edit
                      </button>
                    )}

                    {onDelete && (
                      <button
                        onClick={() => onDelete(row)}
                        style={{
                          padding: "7px 11px",
                          border: "1px solid #fecaca",
                          borderRadius: "7px",
                          background: "#fef2f2",
                          color: "#dc2626",
                          cursor: "pointer",
                          fontSize: "12px",
                          fontWeight: "600",
                        }}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;