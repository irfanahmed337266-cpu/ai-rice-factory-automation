import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

const EMPTY_FORM = {
  input_material_id: "",
  output_product_id: "",
  input_quantity: "",
  output_quantity: "",
  waste_quantity: "0",
  status: "Pending",
  notes: "",
};

function Production() {
  const [productions, setProductions] = useState([]);

  const [form, setForm] = useState({ ...EMPTY_FORM });

  const [editingId, setEditingId] = useState(null);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [predicting, setPredicting] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [prediction, setPrediction] = useState(null);

  // =========================================================
  // AUTH
  // =========================================================

  const getToken = () => {
    return localStorage.getItem("access_token");
  };

  const getHeaders = () => {
    const token = getToken();

    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  // =========================================================
  // LOAD PRODUCTION
  // =========================================================

  const loadProductions = async () => {
    setLoading(true);
    setError("");

    try {
      const token = getToken();

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      const response = await fetch(
        `${API_URL}/production/`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data =
        await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `Failed to load production (${response.status})`
        );
      }

      setProductions(
        Array.isArray(data) ? data : []
      );
    } catch (err) {
      console.error(
        "Load production error:",
        err
      );

      setError(
        err?.message ||
          "Failed to load production."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProductions();
  }, []);

  // =========================================================
  // FORM CHANGE
  // =========================================================

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));

    setError("");
    setSuccess("");
  };

  // =========================================================
  // RESET
  // =========================================================

  const resetForm = () => {
    setForm({ ...EMPTY_FORM });
    setEditingId(null);
    setPrediction(null);
    setError("");
  };

  // =========================================================
  // VALIDATION
  // =========================================================

  const validateForm = () => {
    const materialId = Number(
      form.input_material_id
    );

    const productId = Number(
      form.output_product_id
    );

    const inputQuantity = Number(
      form.input_quantity
    );

    const outputQuantity = Number(
      form.output_quantity
    );

    const wasteQuantity = Number(
      form.waste_quantity
    );

    if (
      !Number.isInteger(materialId) ||
      materialId <= 0
    ) {
      throw new Error(
        "Input Material ID must be a valid positive number."
      );
    }

    if (
      !Number.isInteger(productId) ||
      productId <= 0
    ) {
      throw new Error(
        "Output Product ID must be a valid positive number."
      );
    }

    if (
      !Number.isInteger(inputQuantity) ||
      inputQuantity <= 0
    ) {
      throw new Error(
        "Input quantity must be a positive whole number."
      );
    }

    if (
      !Number.isInteger(outputQuantity) ||
      outputQuantity <= 0
    ) {
      throw new Error(
        "Output quantity must be a positive whole number."
      );
    }

    if (
      !Number.isInteger(wasteQuantity) ||
      wasteQuantity < 0
    ) {
      throw new Error(
        "Waste quantity cannot be negative."
      );
    }
  };

  // =========================================================
  // CREATE / UPDATE
  // =========================================================

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setSaving(true);

    try {
      const token = getToken();

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      validateForm();

      // =====================================================
      // CREATE
      // =====================================================

      if (editingId === null) {
        const payload = {
          input_material_id: Number(
            form.input_material_id
          ),

          output_product_id: Number(
            form.output_product_id
          ),

          input_quantity: Number(
            form.input_quantity
          ),

          output_quantity: Number(
            form.output_quantity
          ),

          waste_quantity: Number(
            form.waste_quantity || 0
          ),

          status: form.status,

          notes:
            form.notes.trim() || null,
        };

        const response = await fetch(
          `${API_URL}/production/`,
          {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(payload),
          }
        );

        const data =
          await response.json().catch(() => null);

        if (!response.ok) {
          throw new Error(
            data?.detail ||
              data?.message ||
              `Failed to create production (${response.status})`
          );
        }

        setSuccess(
          `Production #${
            data?.production?.id ?? ""
          } created successfully.`
        );

        resetForm();

        await loadProductions();

        return;
      }

      // =====================================================
      // UPDATE
      // =====================================================

      const payload = {
        input_quantity: Number(
          form.input_quantity
        ),

        output_quantity: Number(
          form.output_quantity
        ),

        waste_quantity: Number(
          form.waste_quantity || 0
        ),

        status: form.status,

        notes:
          form.notes.trim() || null,
      };

      const response = await fetch(
        `${API_URL}/production/${editingId}`,
        {
          method: "PUT",
          headers: getHeaders(),
          body: JSON.stringify(payload),
        }
      );

      const data =
        await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `Failed to update production (${response.status})`
        );
      }

      setSuccess(
        `Production #${editingId} updated successfully.`
      );

      resetForm();

      await loadProductions();
    } catch (err) {
      console.error(
        "Production save error:",
        err
      );

      setError(
        err?.message ||
          "Failed to save production."
      );
    } finally {
      setSaving(false);
    }
  };

  // =========================================================
  // EDIT
  // =========================================================

  const startEdit = (production) => {
    setError("");
    setSuccess("");
    setPrediction(null);

    setEditingId(production.id);

    setForm({
      input_material_id:
        production.input_material_id ?? "",

      output_product_id:
        production.output_product_id ?? "",

      input_quantity:
        production.input_quantity ?? "",

      output_quantity:
        production.output_quantity ?? "",

      waste_quantity:
        production.waste_quantity ?? 0,

      status:
        production.status ?? "Pending",

      notes:
        production.notes ?? "",
    });

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // =========================================================
  // DELETE
  // =========================================================

  const deleteProduction = async (
    production
  ) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete Production #${production.id}?\n\n` +
        `Input: ${production.input_quantity}\n` +
        `Output: ${production.output_quantity}\n` +
        `Status: ${production.status}\n\n` +
        `If completed, the backend will reverse the stock.`
    );

    if (!confirmed) {
      return;
    }

    setDeletingId(production.id);
    setError("");
    setSuccess("");

    try {
      const token = getToken();

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      const response = await fetch(
        `${API_URL}/production/${production.id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data =
        await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `Failed to delete production (${response.status})`
        );
      }

      setSuccess(
        `Production #${production.id} deleted successfully.`
      );

      if (editingId === production.id) {
        resetForm();
      }

      await loadProductions();
    } catch (err) {
      console.error(
        "Delete production error:",
        err
      );

      setError(
        err?.message ||
          "Failed to delete production."
      );
    } finally {
      setDeletingId(null);
    }
  };

  // =========================================================
  // ML PREDICTION
  // =========================================================

  const runPrediction = async () => {
    setError("");
    setSuccess("");
    setPrediction(null);

    try {
      const token = getToken();

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      const materialId = Number(
        form.input_material_id
      );

      const inputQuantity = Number(
        form.input_quantity
      );

      if (
        !Number.isInteger(materialId) ||
        materialId <= 0
      ) {
        throw new Error(
          "Enter a valid Input Material ID first."
        );
      }

      if (
        !Number.isInteger(inputQuantity) ||
        inputQuantity <= 0
      ) {
        throw new Error(
          "Enter a valid Input Quantity first."
        );
      }

      setPredicting(true);

      const response = await fetch(
        `${API_URL}/production/prediction`,
        {
          method: "POST",
          headers: getHeaders(),
          body: JSON.stringify({
            input_material_id: materialId,
            input_quantity: inputQuantity,
          }),
        }
      );

      const data =
        await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `Prediction failed (${response.status})`
        );
      }

      setPrediction(data);
    } catch (err) {
      console.error(
        "Production prediction error:",
        err
      );

      setError(
        err?.message ||
          "Production prediction failed."
      );
    } finally {
      setPredicting(false);
    }
  };

  // =========================================================
  // FORMAT
  // =========================================================

  const formatNumber = (value) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "-";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
      return "-";
    }

    return number.toLocaleString("en-PK");
  };

  const formatCurrency = (value) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "-";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
      return "-";
    }

    return `Rs. ${number.toLocaleString(
      "en-PK",
      {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }
    )}`;
  };

  // =========================================================
  // STATUS BADGE
  // =========================================================

  const statusBadge = (status) => {
    let background = "#fef3c7";
    let color = "#92400e";

    if (status === "Completed") {
      background = "#dcfce7";
      color = "#166534";
    }

    if (status === "Cancelled") {
      background = "#fee2e2";
      color = "#991b1b";
    }

    return (
      <span
        style={{
          display: "inline-block",
          padding: "5px 10px",
          borderRadius: "999px",
          background,
          color,
          fontSize: "11px",
          fontWeight: "700",
        }}
      >
        {status || "-"}
      </span>
    );
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <div
      style={{
        padding: "30px",
        maxWidth: "1500px",
        margin: "0 auto",
        background: "#f6f8fc",
        minHeight: "100vh",
        color: "#172033",
      }}
    >
      {/* =====================================================
          HEADER
      ====================================================== */}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "20px",
          marginBottom: "25px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <p
            style={{
              margin: "0 0 6px",
              color: "#6366f1",
              fontSize: "11px",
              fontWeight: "800",
              letterSpacing: "0.15em",
            }}
          >
            FACTORY MANAGEMENT
          </p>

          <h1
            style={{
              margin: 0,
              color: "#111827",
              fontSize: "30px",
            }}
          >
            Production
          </h1>

          <p
            style={{
              marginTop: "8px",
              color: "#64748b",
            }}
          >
            Manage production, stock conversion,
            waste and AI production predictions.
          </p>
        </div>

        <button
          type="button"
          onClick={loadProductions}
          disabled={loading || saving}
          style={refreshButtonStyle}
        >
          {loading
            ? "Refreshing..."
            : "Refresh"}
        </button>
      </div>

      {/* =====================================================
          MESSAGES
      ====================================================== */}

      {error && (
        <div style={errorStyle}>
          {error}
        </div>
      )}

      {success && (
        <div style={successStyle}>
          {success}
        </div>
      )}

      {/* =====================================================
          FORM
      ====================================================== */}

      <div style={cardStyle}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "20px",
            gap: "15px",
          }}
        >
          <h2
            style={{
              margin: 0,
              color: "#172033",
              fontSize: "18px",
            }}
          >
            {editingId !== null
              ? `Edit Production #${editingId}`
              : "Create New Production"}
          </h2>

          {editingId !== null && (
            <button
              type="button"
              onClick={resetForm}
              style={cancelButtonStyle}
            >
              Cancel Edit
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(210px, 1fr))",
              gap: "16px",
            }}
          >
            {/* MATERIAL */}

            <div>
              <label>
                Input Material ID
              </label>

              <input
                type="number"
                name="input_material_id"
                value={
                  form.input_material_id
                }
                onChange={handleChange}
                required
                min="1"
                step="1"
                disabled={
                  editingId !== null
                }
                placeholder="e.g. 1"
              />
            </div>

            {/* PRODUCT */}

            <div>
              <label>
                Output Product ID
              </label>

              <input
                type="number"
                name="output_product_id"
                value={
                  form.output_product_id
                }
                onChange={handleChange}
                required
                min="1"
                step="1"
                disabled={
                  editingId !== null
                }
                placeholder="e.g. 1"
              />
            </div>

            {/* INPUT */}

            <div>
              <label>
                Input Quantity
              </label>

              <input
                type="number"
                name="input_quantity"
                value={
                  form.input_quantity
                }
                onChange={handleChange}
                required
                min="1"
                step="1"
                placeholder="e.g. 1000"
              />
            </div>

            {/* OUTPUT */}

            <div>
              <label>
                Output Quantity
              </label>

              <input
                type="number"
                name="output_quantity"
                value={
                  form.output_quantity
                }
                onChange={handleChange}
                required
                min="1"
                step="1"
                placeholder="e.g. 900"
              />
            </div>

            {/* WASTE */}

            <div>
              <label>
                Waste Quantity
              </label>

              <input
                type="number"
                name="waste_quantity"
                value={
                  form.waste_quantity
                }
                onChange={handleChange}
                min="0"
                step="1"
                placeholder="e.g. 100"
              />
            </div>

            {/* STATUS */}

            <div>
              <label>Status</label>

              <select
                name="status"
                value={form.status}
                onChange={handleChange}
              >
                <option value="Pending">
                  Pending
                </option>

                <option value="Completed">
                  Completed
                </option>

                <option value="Cancelled">
                  Cancelled
                </option>
              </select>
            </div>
          </div>

          {/* NOTES */}

          <div
            style={{
              marginTop: "16px",
            }}
          >
            <label>Notes</label>

            <textarea
              name="notes"
              value={form.notes}
              onChange={handleChange}
              rows="3"
              placeholder="Production notes..."
            />
          </div>

          {/* BUTTONS */}

          <div
            style={{
              display: "flex",
              gap: "10px",
              marginTop: "18px",
              flexWrap: "wrap",
            }}
          >
            <button
              type="submit"
              disabled={
                saving ||
                predicting ||
                deletingId !== null
              }
              style={primaryButtonStyle}
            >
              {saving
                ? editingId !== null
                  ? "Updating..."
                  : "Creating..."
                : editingId !== null
                ? "Update Production"
                : "Create Production"}
            </button>

            <button
              type="button"
              onClick={runPrediction}
              disabled={
                predicting ||
                saving ||
                deletingId !== null
              }
              style={predictionButtonStyle}
            >
              {predicting
                ? "Running AI Prediction..."
                : "🤖 AI Production Prediction"}
            </button>

            {editingId !== null && (
              <button
                type="button"
                onClick={resetForm}
                disabled={saving}
                style={cancelButtonStyle}
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      {/* =====================================================
          ML PREDICTION
      ====================================================== */}

      {prediction && (
        <div style={predictionCardStyle}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "18px",
              gap: "15px",
              flexWrap: "wrap",
            }}
          >
            <div>
              <p
                style={{
                  margin: "0 0 5px",
                  color: "#6366f1",
                  fontSize: "11px",
                  fontWeight: "800",
                  letterSpacing: "0.12em",
                }}
              >
                AI PRODUCTION ANALYSIS
              </p>

              <h2
                style={{
                  margin: 0,
                  fontSize: "20px",
                  color: "#111827",
                }}
              >
                Production Prediction
              </h2>
            </div>

            <span
              style={{
                padding: "8px 14px",
                borderRadius: "999px",
                background:
                  prediction.recommendation?.status ===
                  "GOOD"
                    ? "#dcfce7"
                    : prediction.recommendation?.status ===
                      "ACCEPTABLE"
                    ? "#fef3c7"
                    : "#fee2e2",
                color:
                  prediction.recommendation?.status ===
                  "GOOD"
                    ? "#166534"
                    : prediction.recommendation?.status ===
                      "ACCEPTABLE"
                    ? "#92400e"
                    : "#991b1b",
                fontWeight: "800",
                fontSize: "12px",
              }}
            >
              {prediction.recommendation?.status ||
                "-"}
            </span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "14px",
            }}
          >
            <Metric
              title="Material"
              value={
                prediction.material?.name ||
                "-"
              }
            />

            <Metric
              title="Input Quantity"
              value={`${formatNumber(
                prediction.input_quantity
              )} kg`}
            />

            <Metric
              title="Predicted Yield"
              value={
                prediction.ml_prediction
                  ?.predicted_yield_rate !==
                undefined
                  ? `${(
                      Number(
                        prediction
                          .ml_prediction
                          .predicted_yield_rate
                      ) * 100
                    ).toFixed(2)}%`
                  : "-"
              }
            />

            <Metric
              title="Predicted Output"
              value={`${formatNumber(
                prediction.ml_prediction
                  ?.predicted_output_quantity
              )} kg`}
            />

            <Metric
              title="Predicted Waste"
              value={`${formatNumber(
                prediction.ml_prediction
                  ?.predicted_waste_quantity
              )} kg`}
            />

            <Metric
              title="Input Material Cost"
              value={formatCurrency(
                prediction.estimated_cost
                  ?.input_material_cost
              )}
            />

            <Metric
              title="Estimated Output Rate"
              value={formatCurrency(
                prediction.estimated_cost
                  ?.estimated_output_rate
              )}
            />

            <Metric
              title="Available Stock"
              value={`${formatNumber(
                prediction.stock
                  ?.available_quantity
              )} kg`}
            />
          </div>

          <div
            style={{
              marginTop: "18px",
              padding: "15px",
              borderRadius: "10px",
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
            }}
          >
            <strong
              style={{
                color: "#334155",
              }}
            >
              Recommendation
            </strong>

            <p
              style={{
                margin: "7px 0 0",
                color: "#64748b",
                lineHeight: 1.6,
              }}
            >
              {prediction.recommendation
                ?.message || "-"}
            </p>
          </div>

          <div
            style={{
              marginTop: "12px",
              fontSize: "12px",
              color: "#64748b",
            }}
          >
            ⚠️ Prediction only. No inventory or
            production record was modified.
          </div>
        </div>
      )}

      {/* =====================================================
          PRODUCTION TABLE
      ====================================================== */}

      <div style={cardStyle}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingBottom: "20px",
            borderBottom:
              "1px solid #eef1f6",
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: "18px",
              color: "#172033",
            }}
          >
            Production Transactions
          </h2>

          <span
            style={{
              color: "#64748b",
              fontSize: "13px",
              fontWeight: "600",
            }}
          >
            {productions.length}{" "}
            {productions.length === 1
              ? "production"
              : "productions"}
          </span>
        </div>

        {loading &&
        productions.length === 0 ? (
          <div style={emptyStyle}>
            Loading production...
          </div>
        ) : productions.length === 0 ? (
          <div style={emptyStyle}>
            No production records found.
          </div>
        ) : (
          <div
            style={{
              overflowX: "auto",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                minWidth: "1250px",
              }}
            >
              <thead>
                <tr
                  style={{
                    background: "#f8fafc",
                  }}
                >
                  <th>ID</th>
                  <th>Material</th>
                  <th>Product</th>
                  <th>Input</th>
                  <th>Output</th>
                  <th>Waste</th>
                  <th>ML Yield</th>
                  <th>ML Output</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {productions.map(
                  (production) => (
                    <tr
                      key={production.id}
                    >
                      <td>
                        <strong>
                          #{production.id}
                        </strong>
                      </td>

                      <td>
                        {production.input_material_id ??
                          "-"}
                      </td>

                      <td>
                        {production.output_product_id ??
                          "-"}
                      </td>

                      <td>
                        <strong>
                          {formatNumber(
                            production.input_quantity
                          )}
                        </strong>
                      </td>

                      <td>
                        <strong>
                          {formatNumber(
                            production.output_quantity
                          )}
                        </strong>
                      </td>

                      <td>
                        {formatNumber(
                          production.waste_quantity
                        )}
                      </td>

                      <td>
                        {production.ml_predicted_yield_rate !==
                        null &&
                        production.ml_predicted_yield_rate !==
                        undefined
                          ? `${(
                              Number(
                                production.ml_predicted_yield_rate
                              ) * 100
                            ).toFixed(2)}%`
                          : "-"}
                      </td>

                      <td>
                        {formatNumber(
                          production.ml_predicted_output_quantity
                        )}
                      </td>

                      <td>
                        {statusBadge(
                          production.status
                        )}
                      </td>

                      <td>
                        <div
                          style={{
                            display: "flex",
                            gap: "8px",
                            alignItems:
                              "center",
                          }}
                        >
                          <button
                            type="button"
                            onClick={() =>
                              startEdit(
                                production
                              )
                            }
                            disabled={
                              saving ||
                              deletingId !==
                                null
                            }
                            style={
                              editButtonStyle
                            }
                          >
                            ✏️ Edit
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              deleteProduction(
                                production
                              )
                            }
                            disabled={
                              saving ||
                              deletingId !==
                                null
                            }
                            style={
                              deleteButtonStyle
                            }
                          >
                            {deletingId ===
                            production.id
                              ? "Deleting..."
                              : "🗑️ Delete"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* =====================================================
          LOCAL STYLES
      ====================================================== */}

      <style>{`
        label {
          display: block;
          margin-bottom: 7px;
          color: #334155;
          font-size: 13px;
          font-weight: 600;
        }

        input,
        select,
        textarea {
          width: 100%;
          box-sizing: border-box;
          padding: 11px 12px;
          border: 1px solid #cbd5e1;
          border-radius: 8px;
          background: #ffffff;
          color: #172033;
          font-size: 14px;
          outline: none;
        }

        input:focus,
        select:focus,
        textarea:focus {
          border-color: #6366f1;
          box-shadow:
            0 0 0 3px
            rgba(99, 102, 241, 0.10);
        }

        input:disabled {
          background: #f1f5f9;
          color: #64748b;
          cursor: not-allowed;
        }

        th {
          padding: 13px 14px;
          text-align: left;
          color: #64748b;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
        }

        td {
          padding: 14px;
          border-top:
            1px solid #eef1f6;
          color: #334155;
          font-size: 13px;
          white-space: nowrap;
        }

        tbody tr:hover {
          background: #fafbff;
        }

        button {
          transition:
            opacity 0.15s ease,
            transform 0.15s ease;
        }

        button:hover:not(:disabled) {
          transform: translateY(-1px);
        }

        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}

// =========================================================
// METRIC COMPONENT
// =========================================================

function Metric({ title, value }) {
  return (
    <div
      style={{
        padding: "16px",
        borderRadius: "12px",
        background: "#ffffff",
        border: "1px solid #e2e8f0",
      }}
    >
      <div
        style={{
          color: "#64748b",
          fontSize: "11px",
          fontWeight: "700",
          marginBottom: "7px",
          textTransform: "uppercase",
        }}
      >
        {title}
      </div>

      <div
        style={{
          color: "#111827",
          fontSize: "17px",
          fontWeight: "800",
        }}
      >
        {value}
      </div>
    </div>
  );
}

// =========================================================
// STYLES
// =========================================================

const cardStyle = {
  background: "#ffffff",
  border: "1px solid #e5e7eb",
  borderRadius: "16px",
  padding: "24px",
  marginBottom: "25px",
  boxShadow:
    "0 8px 25px rgba(15,23,42,0.05)",
};

const predictionCardStyle = {
  background: "#ffffff",
  border: "1px solid #c7d2fe",
  borderRadius: "16px",
  padding: "24px",
  marginBottom: "25px",
  boxShadow:
    "0 8px 25px rgba(79,70,229,0.08)",
};

const primaryButtonStyle = {
  padding: "12px 22px",
  border: "none",
  borderRadius: "9px",
  background: "#4f46e5",
  color: "#ffffff",
  fontWeight: "700",
  cursor: "pointer",
};

const predictionButtonStyle = {
  padding: "12px 22px",
  border: "none",
  borderRadius: "9px",
  background: "#0f766e",
  color: "#ffffff",
  fontWeight: "700",
  cursor: "pointer",
};

const refreshButtonStyle = {
  padding: "10px 16px",
  border: "1px solid #e2e8f0",
  borderRadius: "9px",
  background: "#ffffff",
  color: "#334155",
  cursor: "pointer",
  fontWeight: "600",
};

const cancelButtonStyle = {
  padding: "10px 16px",
  border: "1px solid #cbd5e1",
  borderRadius: "9px",
  background: "#ffffff",
  color: "#475569",
  cursor: "pointer",
  fontWeight: "600",
};

const editButtonStyle = {
  padding: "8px 12px",
  border: "1px solid #c7d2fe",
  borderRadius: "7px",
  background: "#eef2ff",
  color: "#4338ca",
  cursor: "pointer",
  fontWeight: "700",
  fontSize: "12px",
};

const deleteButtonStyle = {
  padding: "8px 12px",
  border: "1px solid #fecaca",
  borderRadius: "7px",
  background: "#fef2f2",
  color: "#b91c1c",
  cursor: "pointer",
  fontWeight: "700",
  fontSize: "12px",
};

const errorStyle = {
  marginBottom: "20px",
  padding: "13px 15px",
  borderRadius: "9px",
  background: "#fef2f2",
  border: "1px solid #fecaca",
  color: "#b91c1c",
};

const successStyle = {
  marginBottom: "20px",
  padding: "13px 15px",
  borderRadius: "9px",
  background: "#f0fdf4",
  border: "1px solid #bbf7d0",
  color: "#15803d",
};

const emptyStyle = {
  padding: "40px",
  textAlign: "center",
  color: "#64748b",
};

export default Production;