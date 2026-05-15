const API_URL =
"https://blood-bank-management-system-production-0359.up.railway.app/api";

const user =
JSON.parse(localStorage.getItem("bbms_user"));

if (!user || user.role !== "MinistryOfHealth") {
    window.location.href = "../index.html";
}

function logout() {
    localStorage.removeItem("bbms_user");
    window.location.href = "../index.html";
}

async function loadInventorySummary() {

    const res = await fetch(
        `${API_URL}/ministry/inventory-summary`
    );

    const result = await res.json();

    let html = `
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

    result.data.forEach(r => {

        html += `
            <tr>
                <td>${r.blood_type}</td>
                <td>${r.component_type}</td>
                <td>${r.status}</td>
                <td>${r.unit_count}</td>
                <td>${r.total_quantity_ml}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    document.getElementById("inventoryTable").innerHTML = html;
}

loadInventorySummary();