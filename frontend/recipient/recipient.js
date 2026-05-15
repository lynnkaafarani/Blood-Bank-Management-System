//const API_URL = "http://127.0.0.1:5000/api";
const API_URL = "https://blood-bank-management-system-production-0359.up.railway.app/api";
const user = JSON.parse(localStorage.getItem("bbms_user"));

let recipientProfile = null;

if (!user || user.role !== "Recipient") {
    window.location.href = "../index.html";
}

function logout() {
    localStorage.removeItem("bbms_user");
    window.location.href = "../index.html";
}

async function loadRecipientProfile() {
    const res = await fetch(`${API_URL}/recipients`);
    const result = await res.json();

    recipientProfile = result.data.find(r => r.user_id === user.user_id);

    if (!recipientProfile) {
        document.getElementById("profileBox").innerHTML = "Recipient profile not found.";
        return;
    }

    document.getElementById("userInfo").textContent =
        `${user.full_name} (${user.email})`;

    document.getElementById("profileBox").innerHTML = `
        <table class="summary-table">
            <tr><th>Recipient ID</th><td>${recipientProfile.recipient_id}</td></tr>
            <tr><th>Name</th><td>${recipientProfile.full_name}</td></tr>
            <tr><th>Blood type</th><td><span class="status-pill">${recipientProfile.blood_type}</span></td></tr>
            <tr><th>Medical condition</th><td>${recipientProfile.medical_condition || "—"}</td></tr>
        </table>
    `;

    document.getElementById("updateFirstName").value = recipientProfile.full_name.split(" ")[0] || "";
    document.getElementById("updateLastName").value = recipientProfile.full_name.split(" ").slice(1).join(" ") || "";
    document.getElementById("updatePhone").value = recipientProfile.phone || "";
    document.getElementById("updateCondition").value = recipientProfile.medical_condition || "";
}

document.getElementById("profileForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const response = await fetch(`${API_URL}/recipients/${recipientProfile.recipient_id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            first_name: document.getElementById("updateFirstName").value,
            last_name: document.getElementById("updateLastName").value,
            phone: document.getElementById("updatePhone").value,
            medical_condition: document.getElementById("updateCondition").value
        })
    });

    const result = await response.json();

    if (!result.success) {
        alert(result.message || "Could not update profile.");
        return;
    }

    alert("Profile updated successfully.");
    await loadRecipientProfile();
});

async function loadBloodInventory() {
    const bloodType = document.getElementById("filterBloodType").value.toLowerCase();
    const location = document.getElementById("filterLocation").value.toLowerCase();
    const hospitalSearch = document.getElementById("filterHospital").value.toLowerCase();
    const date = document.getElementById("filterDate").value;
    const status = document.getElementById("filterStatus").value;

    const res = await fetch(`${API_URL}/blood-inventory`);
    const result = await res.json();

    // Filter the data based on criteria
    const filteredData = result.data.filter(b => {
        if (bloodType && !b.blood_type.toLowerCase().includes(bloodType)) return false;
        if (location && !b.location.toLowerCase().includes(location)) return false;
        if (hospitalSearch && !b.hospital_name.toLowerCase().includes(hospitalSearch) && !b.hospital_id.toString().includes(hospitalSearch)) return false;
        if (status && b.status !== status) return false;
        if (date && b.expiry_date < date) return false;
        return true;
    });

    // Check if no results found
    if (filteredData.length === 0) {
        document.getElementById("inventoryTable").innerHTML = `
            <div class="no-results-message">
                <p>⚠️ No blood units available matching your search criteria.</p>
                <p class="inline-note">Try adjusting your filters or check back later.</p>
            </div>
        `;
        return;
    }

    // Build the table with results
    let html = `
        <div class="table-scroll">
        <table class="data-table">
            <thead><tr>
                <th>Unit ID</th>
                <th>Blood type</th>
                <th>Quantity</th>
                <th>Status</th>
                <th>Hospital ID</th>
                <th>Hospital</th>
                <th>Location</th>
                <th>Expiry</th>
            </tr></thead><tbody>
    `;

    filteredData.forEach(b => {
        html += `
            <tr>
                <td>${b.blood_unit_id}</td>
                <td>${b.blood_type}</td>
                <td>${b.quantity_ml}</td>
                <td><span class="status-pill">${b.status}</span></td>
                <td>${b.hospital_id}</td>
                <td>${b.hospital_name}</td>
                <td>${b.location}</td>
                <td>${b.expiry_date}</td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("inventoryTable").innerHTML = html;
}

async function markNotificationRead(notificationId) {
    await fetch(`${API_URL}/notifications/${notificationId}/read`, {
        method: "PUT"
    });

    await loadNotifications();
}

async function init() {
    await loadRecipientProfile();
    await loadBloodInventory();
    await loadMyRequests();
    await loadNotifications();
    const today = new Date().toISOString().split('T')[0];
    document.getElementById("filterDate").min = today;
}

init();