const API = "";

const COMPLAINT_CATEGORIES = [
  "Damaged Product",
  "Leakage / Spillage",
  "Missing Items / Parts",
  "Wrong Product Delivered",
  "Poor Product Quality",
  "Defective / Not Working",
  "Damaged Packaging",
  "Expired Product",
  "Incorrect Product Description",
  "Wrong Size / Quantity",
  "Delivery Delay",
  "Incorrect Delivery",
  "Return / Refund Issue",
  "Other / New Complaint",
  "Unknown / Uncategorized",
];

const PRODUCT_CATEGORIES = [
  "Cosmetics & Beauty",
  "Electronics",
  "Clothing & Fashion",
  "Home Appliances",
  "Kitchenware & Utensils",
  "Furniture & Home Decor",
  "Food & Beverages",
  "Health & Personal Care",
  "Toys & Games",
  "Books & Stationery",
  "Sports & Fitness",
  "Other Product Category",
  "Unknown / Uncategorized",
];

let categoryChart = null;
let productChart = null;
let patternChart = null;
let productCategoryChart = null;
let productPatternChart = null;

const $ = (id) => document.getElementById(id);

function escapeHTML(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
      })[char],
  );
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString();
}

async function apiRequest(url, options = {}) {
  const response = await fetch(`${API}${url}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || "Something went wrong.");
  }

  return data;
}

function createBarChart(canvasId, chartInstance, labels, values, label) {
  const canvas = $(canvasId);

  if (!canvas || typeof Chart === "undefined") {
    return chartInstance;
  }

  if (chartInstance) {
    chartInstance.destroy();
  }

  return new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          borderWidth: 1,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          ticks: {
            precision: 0,
          },
        },
      },
    },
  });
}

function renderCategoryChart(summary) {
  const canvas = $("categoryChart");

  if (!canvas || typeof Chart === "undefined") return;

  const ranking = summary.category_ranking || [];

  if (categoryChart) categoryChart.destroy();

  categoryChart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: ranking.map((item) => item.category),
      datasets: [
        {
          data: ranking.map((item) => Number(item.complaints || 0)),
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
        },
      },
    },
  });
}

function renderProductChart(summary) {
  const products = summary.product_ranking || [];

  productChart = createBarChart(
    "productChart",
    productChart,
    products.map((item) => item.product),
    products.map((item) => Number(item.complaints || 0)),
    "Complaints by Product",
  );
}

function renderPatternChart(summary) {
  const categories = summary.category_ranking || [];

  patternChart = createBarChart(
    "patternChart",
    patternChart,
    categories.map((item) => item.category),
    categories.map((item) => Number(item.complaints || 0)),
    "Complaints by Complaint Category",
  );
}

function renderProductCategoryChart(summary) {
  const categories = summary.product_category_ranking || [];

  productCategoryChart = createBarChart(
    "productCategoryChart",
    productCategoryChart,
    categories.map((item) => item.category || item.product_category),
    categories.map((item) => Number(item.complaints || 0)),
    "Complaints by Product Category",
  );
}

function renderProductPatternChart(summary) {
  const categories = summary.product_category_ranking || [];

  productPatternChart = createBarChart(
    "productPatternChart",
    productPatternChart,
    categories.map((item) => item.category || item.product_category),
    categories.map((item) => Number(item.complaints || 0)),
    "Product Category Patterns",
  );
}

function renderTopProducts(summary) {
  const container = $("topProducts");

  if (!container) return;

  const products = summary.product_ranking || [];

  if (!products.length) {
    container.innerHTML = "<p>No product data available yet.</p>";
    return;
  }

  container.innerHTML = products
    .slice(0, 8)
    .map(
      (item, index) => `
        <div class="ranking-item">
          <div>
            <strong>${index + 1}. ${escapeHTML(item.product)}</strong>
          </div>
          <span>${formatNumber(item.complaints)} complaints</span>
        </div>
      `,
    )
    .join("");
}

function renderProductBreakdown(summary) {
  const container = $("productBreakdown");

  if (!container) return;

  const products = summary.product_breakdown || [];

  if (!products.length) {
    container.innerHTML = "<p>No product intelligence available yet.</p>";
    return;
  }

  container.innerHTML = products
    .map((product) => {
      const categories = product.categories || [];

      return `
        <div class="product-card">
          <h3>${escapeHTML(product.product)}</h3>
          <p>
            <strong>${formatNumber(product.complaints)}</strong>
            total complaints
          </p>
          <div class="product-categories">
            ${
              categories.length
                ? categories
                    .map(
                      (category) => `
                        <span class="tag">
                          ${escapeHTML(category.category)}
                          (${formatNumber(category.complaints)})
                        </span>
                      `,
                    )
                    .join("")
                : "<span>No complaint category details available.</span>"
            }
          </div>
        </div>
      `;
    })
    .join("");
}

function renderProductCategoryBreakdown(summary) {
  const container = $("productCategoryBreakdown");

  if (!container) return;

  const categories = summary.product_category_breakdown || [];

  if (!categories.length) {
    container.innerHTML =
      "<p>No product category intelligence available yet.</p>";
    return;
  }

  container.innerHTML = categories
    .map((category) => {
      const products = category.products || [];

      return `
        <div class="product-card">
          <h3>${escapeHTML(
            category.product_category || category.category || "Uncategorized",
          )}</h3>

          <p>
            <strong>${formatNumber(category.complaints)}</strong>
            total complaints
          </p>

          <div class="product-categories">
            ${
              products.length
                ? products
                    .map(
                      (product) => `
                        <span class="tag">
                          ${escapeHTML(product.product)}
                          (${formatNumber(product.complaints)})
                        </span>
                      `,
                    )
                    .join("")
                : "<span>No individual products recorded.</span>"
            }
          </div>
        </div>
      `;
    })
    .join("");
}

function renderAnomalies(summary) {
  const container = $("anomalyList");

  if (!container) return;

  const anomalies = summary.anomalies || [];

  if (!anomalies.length) {
    container.innerHTML = "<p>No unusual complaint patterns detected.</p>";
    return;
  }

  container.innerHTML = anomalies
    .map(
      (item) => `
        <div class="insight-item">
          <strong>${escapeHTML(
            item.title || item.product || "Anomaly detected",
          )}</strong>
          <p>${escapeHTML(
            item.description ||
              item.message ||
              "An unusual complaint pattern was identified.",
          )}</p>
        </div>
      `,
    )
    .join("");
}

function renderUnknownComplaints(records) {
  const container = $("unknownList");

  if (!container) return;

  const unknownRecords = records.filter((record) => {
    const category = String(record.category || "").trim();

    return [
      "Unknown / Uncategorized",
      "Other / New Complaint",
      "Uncategorized",
      "Unknown / Unclear Reasons",
      "Other / New Category",
    ].includes(category);
  });

  if (!unknownRecords.length) {
    container.innerHTML =
      "<p>No unknown or new complaint categories currently recorded.</p>";
    return;
  }

  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Product</th>
          <th>Product Category</th>
          <th>Customer Complaint</th>
          <th>Complaint Category</th>
          <th>Severity</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        ${unknownRecords
          .map(
            (record) => `
              <tr>
                <td>${escapeHTML(record.product)}</td>
                <td>${escapeHTML(record.product_category || "Unknown / Uncategorized")}</td>
                <td>${escapeHTML(record.complaint_text)}</td>
                <td>${escapeHTML(record.category)}</td>
                <td>${escapeHTML(record.severity)}</td>
                <td>${escapeHTML(record.status)}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderUnknownProducts(records) {
  const container = $("unknownProductList");

  if (!container) return;

  const unknownRecords = records.filter((record) => {
    const category = String(
      record.product_category || "Unknown / Uncategorized",
    ).trim();

    return ["", "Unknown / Uncategorized", "Uncategorized"].includes(category);
  });

  if (!unknownRecords.length) {
    container.innerHTML =
      "<p>No complaints with unknown product categories.</p>";
    return;
  }

  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Product</th>
          <th>Customer Complaint</th>
          <th>Product Category</th>
          <th>AI Complaint Category</th>
          <th>Severity</th>
        </tr>
      </thead>
      <tbody>
        ${unknownRecords
          .map(
            (record) => `
              <tr>
                <td>${escapeHTML(record.product)}</td>
                <td>${escapeHTML(record.complaint_text)}</td>
                <td>${escapeHTML(record.product_category || "Unknown / Uncategorized")}</td>
                <td>${escapeHTML(record.category)}</td>
                <td>${escapeHTML(record.severity)}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderReview(records) {
  const container = $("complaintTable");

  if (!container) return;

  if (!records.length) {
    container.innerHTML = "<p>No complaints have been submitted yet.</p>";
    return;
  }

  const groupedRecords = {};

  records.forEach((record) => {
    const category = record.category || "Unknown / Uncategorized";

    if (!groupedRecords[category]) {
      groupedRecords[category] = [];
    }

    groupedRecords[category].push(record);
  });

  const orderedCategories = [
    ...COMPLAINT_CATEGORIES.filter((category) => groupedRecords[category]),
    ...Object.keys(groupedRecords).filter(
      (category) => !COMPLAINT_CATEGORIES.includes(category),
    ),
  ];

  container.innerHTML = orderedCategories
    .map((category) => {
      const categoryRecords = groupedRecords[category];

      return `
        <div class="review-category-group">
          <h3>
            ${escapeHTML(category)}
            <span class="tag">${formatNumber(categoryRecords.length)} complaints</span>
          </h3>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Product Category</th>
                  <th>Customer Complaint</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Correct AI Category</th>
                </tr>
              </thead>

              <tbody>
                ${categoryRecords
                  .map(
                    (record) => `
                      <tr>
                        <td>${escapeHTML(record.product)}</td>

                        <td>${escapeHTML(
                          record.product_category || "Unknown / Uncategorized",
                        )}</td>

                        <td>${escapeHTML(record.complaint_text)}</td>

                        <td>${escapeHTML(record.severity)}</td>

                        <td>${escapeHTML(record.status)}</td>

                        <td>
                          <select id="correction-${Number(record.id)}">
                            ${COMPLAINT_CATEGORIES.map(
                              (option) => `
                                <option
                                  value="${escapeHTML(option)}"
                                  ${option === record.category ? "selected" : ""}
                                >
                                  ${escapeHTML(option)}
                                </option>
                              `,
                            ).join("")}
                          </select>

                          <button
                            class="primary-btn"
                            type="button"
                            onclick="correctComplaint(${Number(record.id)})"
                          >
                            Save
                          </button>
                        </td>
                      </tr>
                    `,
                  )
                  .join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    })
    .join("");
}

async function refreshDashboard() {
  try {
    const data = await apiRequest("/api/analysis");

    const summary = data.summary || {};
    const records = data.records || [];

    if ($("totalComplaints")) {
      $("totalComplaints").textContent = formatNumber(summary.total);
    }

    if ($("productsAffected")) {
      $("productsAffected").textContent = formatNumber(summary.products_count);
    }

    if ($("unknownCount")) {
      $("unknownCount").textContent = formatNumber(summary.unknown_count);
    }

    if ($("unknownRate")) {
      $("unknownRate").textContent =
        `${Number(summary.unknown_rate || 0).toFixed(1)}% of complaints`;
    }

    if ($("highSeverity")) {
      $("highSeverity").textContent = formatNumber(summary.high_severity);
    }

    renderCategoryChart(summary);
    renderProductChart(summary);
    renderPatternChart(summary);
    renderProductCategoryChart(summary);
    renderProductPatternChart(summary);

    renderTopProducts(summary);
    renderProductBreakdown(summary);
    renderProductCategoryBreakdown(summary);
    renderAnomalies(summary);

    renderUnknownComplaints(records);
    renderUnknownProducts(records);
    renderReview(records);
  } catch (error) {
    console.error("Dashboard loading error:", error);
    console.error("Make sure the Flask backend is running.");
  }
}

async function correctComplaint(recordId) {
  const select = $(`correction-${recordId}`);

  if (!select) return;

  try {
    await apiRequest(`/api/correct/${recordId}`, {
      method: "POST",
      body: JSON.stringify({
        category: select.value,
      }),
    });

    alert("Complaint category corrected successfully.");

    await refreshDashboard();
  } catch (error) {
    alert(error.message);
  }
}

window.correctComplaint = correctComplaint;
window.refreshDashboard = refreshDashboard;

// CUSTOMER COMPLAINT SUBMISSION
const complaintForm = $("complaintForm");

if (complaintForm) {
  complaintForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = complaintForm.querySelector('button[type="submit"]');

    const resultBox = $("classificationResult");

    const payload = {
      product: $("productInput").value.trim(),

      product_category: $("productCategoryInput").value,

      complaint_text: $("complaintInput").value.trim(),

      severity: $("severityInput").value,
    };

    if (
      !payload.product ||
      !payload.product_category ||
      !payload.complaint_text
    ) {
      alert(
        "Please enter the product name, select its product category, and describe the complaint.",
      );
      return;
    }

    if (button) {
      button.disabled = true;
      button.textContent = "Analyzing complaint...";
    }

    try {
      const result = await apiRequest("/api/complaints", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (resultBox) {
        resultBox.classList.remove("hidden");

        resultBox.innerHTML = `
          <h3>Complaint Analyzed Successfully</h3>

          <p>
            <strong>Product:</strong>
            ${escapeHTML(result.product)}
          </p>

          <p>
            <strong>Product Category:</strong>
            ${escapeHTML(result.product_category || payload.product_category)}
          </p>

          <p>
            <strong>AI Complaint Category:</strong>
            ${escapeHTML(result.category)}
          </p>

          <p>
            <strong>Severity:</strong>
            ${escapeHTML(result.severity)}
          </p>

          <p>
            <strong>AI Explanation:</strong>
            ${escapeHTML(result.explanation)}
          </p>
        `;
      }

      complaintForm.reset();

      await refreshDashboard();
    } catch (error) {
      if (resultBox) {
        resultBox.classList.remove("hidden");
        resultBox.textContent = error.message;
      } else {
        alert(error.message);
      }
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "✧ Analyze and save complaint";
      }
    }
  });
}

// SIDEBAR NAVIGATION
document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => {
    document.querySelectorAll(".nav-link").forEach((item) => {
      item.classList.remove("active");
    });

    link.classList.add("active");
  });
});

// LOAD DASHBOARD
document.addEventListener("DOMContentLoaded", () => {
  refreshDashboard();
});
