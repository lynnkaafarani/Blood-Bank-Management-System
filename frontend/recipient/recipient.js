//const API_URL = "http://127.0.0.1:5000/api";
const API_URL = https://blood-bank-management-system-production-0359.up.railway.app/api;
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
    const date = document.getElementById("filterDate").value;
    const status = document.getElementById("filterStatus").value;

    const res = await fetch(`${API_URL}/blood-inventory`);
    const result = await res.json();

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

    result.data.forEach(b => {
        if (bloodType && !b.blood_type.toLowerCase().includes(bloodType)) return;
        if (location && !b.location.toLowerCase().includes(location)) return;
        if (status && b.status !== status) return;
        if (date && b.expiry_date < date) return;

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

document.getElementById("requestForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    if (!recipientProfile) {
        alert("Recipient profile not loaded.");
        return;
    }

    const response = await fetch(`${API_URL}/blood-requests`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            recipient_id: recipientProfile.recipient_id,
            hospital_id: document.getElementById("requestHospitalId").value,
            blood_type: document.getElementById("requestBloodType").value,
            quantity_needed_ml: document.getElementById("requestQuantity").value,
            priority_level: document.getElementById("requestPriority").value
        })
    });

    const result = await response.json();

    if (!result.success) {
        alert(result.message || "Could not submit request.");
        return;
    }

    alert("Blood request submitted successfully.");
    this.reset();

    await loadMyRequests();
    await loadNotifications();
});

async function loadMyRequests() {
    if (!recipientProfile) return;

    const res = await fetch(`${API_URL}/blood-requests`);
    const result = await res.json();

    const myRequests = result.data.filter(r => r.recipient_id === recipientProfile.recipient_id);

    let html = `
        <div class="table-scroll">
        <table class="data-table">
            <thead><tr>
                <th>Request ID</th>
                <th>Blood type</th>
                <th>Quantity</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Hospital</th>
                <th>Date</th>
                <th>Action</th>
            </tr></thead><tbody>
    `;

    myRequests.forEach(r => {
        html += `
            <tr>
                <td>${r.request_id}</td>
                <td>${r.blood_type}</td>
                <td>${r.quantity_needed_ml}</td>
                <td><span class="status-pill">${r.priority_level}</span></td>
                <td><span class="status-pill">${r.status}</span></td>
                <td>${r.hospital_name}</td>
                <td>${r.request_date}</td>
                <td>
                    ${r.status === "Pending"
                        ? `<button type="button" class="btn btn-sm btn-danger" onclick="cancelRequest(${r.request_id})">Cancel</button>`
                        : ""}
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("requestsTable").innerHTML = html;
}

async function cancelRequest(requestId) {
    if (!confirm("Cancel this blood request?")) return;

    await fetch(`${API_URL}/blood-requests/${requestId}/cancel`, {
        method: "PUT"
    });

    await loadMyRequests();
    await loadNotifications();
}

async function loadNotifications() {
    const res = await fetch(`${API_URL}/notifications/${user.user_id}`);
    const result = await res.json();

    let html = `
        <div class="table-scroll">
        <table class="data-table">
            <thead><tr>
                <th>ID</th>
                <th>Message</th>
                <th>Type</th>
                <th>Date</th>
                <th>Read</th>
                <th>Action</th>
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
                    <button type="button" class="btn btn-sm btn-secondary" onclick="markNotificationRead(${n.notification_id})">Mark read</button>
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("notificationsBox").innerHTML = html;
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