const API_URL = "https://blood-bank-management-system-production-0359.up.railway.app/api";

const user = JSON.parse(localStorage.getItem("bbms_user"));

if (!user || user.role !== "MinistryOfHealth") {
    window.location.href = "../index.html";
}

document.getElementById("userInfo").textContent =
    `${user.full_name} (${user.email}) — Ministry of Health`;

function logout() {
    localStorage.removeItem("bbms_user");
    window.location.href = "../index.html";
}

async function loadInventorySummary() {
    const res = await fetch(`${API_URL}/ministry/inventory-summary`);
    const result = await res.json();

    let html = `
        <div class="table-scroll">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Blood Type</th>
                    <th>Component</th>
                    <th>Status</th>
                    <th>Units</th>
                    <th>Total Quantity (ml)</th>
                </tr>
            </thead>
            <tbody>
    `;

    if (!result.data || result.data.length === 0) {
        html += `
            <tr>
                <td colspan="5" class="muted">No inventory data available.</td>
            </tr>
        `;
    } else {
        result.data.forEach(row => {
            html += `
                <tr>
                    <td>${row.blood_type}</td>
                    <td>${row.component_type}</td>
                    <td><span class="status-pill">${row.status}</span></td>
                    <td>${row.unit_count}</td>
                    <td>${row.total_quantity_ml || 0}</td>
                </tr>
            `;
        });
    }

    html += `</tbody></table></div>`;
    document.getElementById("inventorySummaryTable").innerHTML = html;
}

async function loadHospitalSummary() {
    const res = await fetch(`${API_URL}/ministry/hospital-summary`);
    const result = await res.json();

    let html = `
        <div class="table-scroll">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Hospital</th>
                    <th>Location</th>
                    <th>Blood Type</th>
                    <th>Units</th>
                    <th>Total Quantity (ml)</th>
                </tr>
            </thead>
            <tbody>
    `;

    if (!result.data || result.data.length === 0) {
        html += `
            <tr>
                <td colspan="5" class="muted">No hospital inventory data available.</td>
            </tr>
        `;
    } else {
        result.data.forEach(row => {
            html += `
                <tr>
                    <td>${row.hospital_name}</td>
                    <td>${row.location}</td>
                    <td>${row.blood_type}</td>
                    <td>${row.unit_count}</td>
                    <td>${row.total_quantity_ml || 0}</td>
                </tr>
            `;
        });
    }

    html += `</tbody></table></div>`;
    document.getElementById("hospitalSummaryTable").innerHTML = html;
}

async function init() {
    await loadInventorySummary();
    await loadHospitalSummary();
}

init();