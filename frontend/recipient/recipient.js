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
async function loadHospitalsDropdown() {

    const res = await fetch(`${API_URL}/hospitals`);
    const result = await res.json();

    const dropdown =
        document.getElementById("requestHospitalId");

    dropdown.innerHTML =
        `<option value="">Select hospital</option>`;

    result.data.forEach(h => {

        dropdown.innerHTML += `
            <option value="${h.hospital_id}">
                ${h.hospital_name} - ${h.location}
            </option>
        `;
    });
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

document.getElementById("requestForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    if (!recipientProfile) {
        alert("Recipient profile not loaded.");
        return;
    }

    const hospitalId = document.getElementById("requestHospitalId").value.trim();
    const bloodType  = document.getElementById("requestBloodType").value.trim();
    const quantity   = document.getElementById("requestQuantity").value.trim();
    const priority   = document.getElementById("requestPriority").value;

    if (!hospitalId || !bloodType || !quantity) {
        alert("All fields are required.");
        return;
    }

    const response = await fetch(`${API_URL}/blood-requests`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            recipient_id:     recipientProfile.recipient_id,
            hospital_id:      hospitalId,
            blood_type:       bloodType,
            quantity_needed_ml: quantity,
            priority_level:   priority
        })
    });

    const result = await response.json();

    if (!result.success) {
        alert(result.message || "Could not submit request.");
        return;
    }

    alert("Blood request submitted successfully.");
    document.getElementById("requestForm").reset();
    await loadMyRequests();
});

async function loadBloodInventory() {
    const bloodType      = document.getElementById("filterBloodType").value.toLowerCase();
    const location       = document.getElementById("filterLocation").value.toLowerCase();
    const hospitalSearch = document.getElementById("filterHospital").value.toLowerCase();
    const date           = document.getElementById("filterDate").value;
    const status         = document.getElementById("filterStatus").value;

    const res    = await fetch(`${API_URL}/blood-inventory`);
    const result = await res.json();

    const filteredData = result.data.filter(b => {
        if (bloodType      && !b.blood_type.toLowerCase().includes(bloodType))                                           return false;
        if (location       && !b.location.toLowerCase().includes(location))                                              return false;
        if (hospitalSearch && !b.hospital_name.toLowerCase().includes(hospitalSearch)
                           && !b.hospital_id.toString().includes(hospitalSearch))                                        return false;
        if (status         && b.status !== status)                                                                       return false;
        if (date           && b.expiry_date < date)                                                                      return false;
        return true;
    });

    if (filteredData.length === 0) {
        const searchedBloodType = document.getElementById("filterBloodType").value.trim().toUpperCase();
        const displayMessage = searchedBloodType
            ? `⚠️ No available blood for blood type ${searchedBloodType}.`
            : "⚠️ No blood units match your filters.";

        document.getElementById("inventoryTable").innerHTML = `
            <p class="muted" style="text-align:center; padding:20px;">
                ${displayMessage}<br>
                <small>Try adjusting your filters or check back later.</small>
            </p>
        `;
        return;
    }

    let html = `
        <div class="table-scroll"><table class="data-table">
            <thead><tr>
                <th>Unit ID</th><th>Blood type</th><th>Qty (ml)</th>
                <th>Status</th><th>Hospital</th><th>Location</th><th>Expiry</th>
            </tr></thead><tbody>
    `;

    filteredData.forEach(b => {
        html += `
            <tr>
                <td>${b.blood_unit_id}</td>
                <td>${b.blood_type}</td>
                <td>${b.quantity_ml}</td>
                <td><span class="status-pill">${b.status}</span></td>
                <td>${b.hospital_name}</td>
                <td>${b.location}</td>
                <td>${b.expiry_date}</td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("inventoryTable").innerHTML = html;
}

async function loadMyRequests() {
    if (!recipientProfile) return;

    const res    = await fetch(`${API_URL}/blood-requests`);
    const result = await res.json();

    const myRequests = result.data.filter(r => r.recipient_id === recipientProfile.recipient_id);

    if (myRequests.length === 0) {
        document.getElementById("requestsTable").innerHTML = "<p class=\"muted\">No blood requests found.</p>";
        return;
    }

    let html = `
        <div class="table-scroll"><table class="data-table">
            <thead><tr>
                <th>ID</th><th>Hospital</th><th>Type</th>
                <th>Qty (ml)</th><th>Priority</th><th>Status</th><th>Action</th>
            </tr></thead><tbody>
    `;

    myRequests.forEach(r => {
        html += `
            <tr>
                <td>${r.request_id}</td>
                <td>${r.hospital_name || r.hospital_id}</td>
                <td>${r.blood_type}</td>
                <td>${r.quantity_needed_ml}</td>
                <td>${r.priority_level}</td>
                <td><span class="status-pill">${r.status}</span></td>
                <td>
                    ${r.status === "Pending" ? `
                        <button type="button" class="btn btn-sm btn-danger"
                            onclick="cancelBloodRequest(${r.request_id})">Cancel</button>
                    ` : `<span class="muted">${r.status}</span>`}
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("requestsTable").innerHTML = html;
}

async function cancelBloodRequest(requestId) {
    if (!confirm("Are you sure you want to cancel this request?")) return;

    const res    = await fetch(`${API_URL}/blood-requests/${requestId}/cancel`, { method: "PUT" });
    const result = await res.json();

    if (!result.success) {
        alert(result.message || "Failed to cancel request.");
        return;
    }

    alert("Request cancelled successfully.");
    await loadMyRequests();
}

async function loadNotifications() {
    const res    = await fetch(`${API_URL}/notifications/${user.user_id}`);
    const result = await res.json();

    let html = `
        <div class="table-scroll"><table class="data-table">
            <thead><tr>
                <th>ID</th><th>Message</th><th>Type</th>
                <th>Date</th><th>Read</th><th>Action</th>
            </tr></thead><tbody>
    `;

    result.data.forEach(n => {
        html += `
            <tr>
                <td>${n.notification_id}</td>
                <td>${n.message}</td>
                <td>${n.type}</td>
                <td>${n.notification_date}</td>
                <td>${n.is_read ? "Yes" : "No"}</td>
                <td>
                    ${!n.is_read ? `
                        <button type="button" class="btn btn-sm btn-secondary"
                            onclick="markNotificationRead(${n.notification_id})">Mark read</button>
                    ` : ""}
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("notificationsBox").innerHTML = html;
}

async function markNotificationRead(notificationId) {
    await fetch(`${API_URL}/notifications/${notificationId}/read`, { method: "PUT" });
    await loadNotifications();
}

async function init() {
    await loadRecipientProfile();
    await loadBloodInventory();
    await loadMyRequests();
    await loadNotifications();
await loadHospitalsDropdown();
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("filterDate").min = today;
}

init();
