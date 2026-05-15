//const API_URL = "http://127.0.0.1:5000/api";
const API_URL = "https://blood-bank-management-system-production-0359.up.railway.app/api";
const user = JSON.parse(localStorage.getItem("bbms_user"));

let donorProfile = null;

if (!user || user.role !== "Donor") {
    window.location.href = "../index.html";
}

function logout() {
    localStorage.removeItem("bbms_user");
    window.location.href = "../index.html";
}

async function loadDonorProfile() {
    const res = await fetch(`${API_URL}/donors`);
    const result = await res.json();

    donorProfile = result.data.find(d => d.user_id === user.user_id);

    if (!donorProfile) {
        document.getElementById("profileBox").innerHTML = "Donor profile not found.";
        return;
    }

    document.getElementById("userInfo").textContent =
        `${user.full_name} (${user.email})`;

    document.getElementById("profileBox").innerHTML = `
        <table class="summary-table">
            <tr><th>Donor ID</th><td>${donorProfile.donor_id}</td></tr>
            <tr><th>Name</th><td>${donorProfile.full_name}</td></tr>
            <tr><th>Blood type</th><td><span class="status-pill">${donorProfile.blood_type}</span></td></tr>
            <tr><th>Health</th><td>${donorProfile.health_status}</td></tr>
            <tr><th>Weight</th><td>${donorProfile.weight_kg || "—"}</td></tr>
            <tr><th>Eligibility</th><td><span class="status-pill">${donorProfile.eligibility_status}</span></td></tr>
            <tr><th>Last donation</th><td>${donorProfile.last_donation_date || "No previous donation"}</td></tr>
        </table>
    `;

    document.getElementById("updateFirstName").value = donorProfile.first_name;
    document.getElementById("updateLastName").value = donorProfile.last_name;
    document.getElementById("updatePhone").value = donorProfile.phone || "";
    document.getElementById("updateHealthStatus").value = donorProfile.health_status || "Healthy";
    document.getElementById("updateWeight").value = donorProfile.weight_kg || "";
    document.getElementById("updateMedication").value = donorProfile.medication_restricted ? "true" : "false";
}

async function loadHospitals() {
    const search = document.getElementById("hospitalSearch").value.toLowerCase();

    const res = await fetch(`${API_URL}/hospitals`);
    const result = await res.json();

    const dropdown = document.getElementById("appointmentHospitalId");
    dropdown.innerHTML = `<option value="">Select hospital</option>`;

    let html = `
        <div class="table-scroll">
        <table class="data-table">
            <thead><tr>
                <th>ID</th>
                <th>Hospital</th>
                <th>Location</th>
                <th>Contact</th>
            </tr></thead><tbody>
    `;

    result.data.forEach(h => {
        dropdown.innerHTML += `
            <option value="${h.hospital_id}">
                ${h.hospital_name} - ${h.location}
            </option>
        `;

        const text = `${h.hospital_name} ${h.location}`.toLowerCase();
        if (search && !text.includes(search)) return;

        html += `
            <tr>
                <td>${h.hospital_id}</td>
                <td>${h.hospital_name}</td>
                <td>${h.location}</td>
                <td>${h.contact_info}</td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("hospitalsTable").innerHTML = html;
}

document.getElementById("appointmentForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    if (!donorProfile) {
        alert("Donor profile not loaded.");
        return;
    }

    if (donorProfile.eligibility_status !== "Eligible") {
        alert("You are not eligible to schedule a donation appointment.");
        return;
    }

    const res = await fetch(`${API_URL}/appointments`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            donor_id: donorProfile.donor_id,
            hospital_id: document.getElementById("appointmentHospitalId").value,
            appointment_datetime: document.getElementById("appointmentDateTime").value,
            eligibility_snapshot: donorProfile.eligibility_status,
            notes: document.getElementById("appointmentNotes").value
        })
    });

    const result = await res.json();

    if (!result.success) {
        alert(result.message || "Could not schedule appointment.");
        return;
    }

    alert(result.message || "Appointment scheduled successfully.");
    this.reset();
    await loadDonorProfile();
    await loadAppointments();
    await loadNotifications();
});

async function loadAppointments() {
    if (!donorProfile) return;

    const res = await fetch(`${API_URL}/appointments`);
    const result = await res.json();

    const myAppointments = result.data.filter(a => a.donor_id === donorProfile.donor_id);

    let html = `
        <div class="table-scroll">
        <table class="data-table">
            <thead><tr>
                <th>ID</th>
                <th>Date/Time</th>
                <th>Hospital</th>
                <th>Status</th>
                <th>Notes</th>
                <th>Action</th>
            </tr></thead><tbody>
    `;

    myAppointments.forEach(a => {
        html += `
            <tr>
                <td>${a.appointment_id}</td>
                <td>${a.appointment_datetime}</td>
                <td>${a.hospital_name}</td>
                <td><span class="status-pill">${a.status}</span></td>
                <td>${a.notes || ""}</td>
                <td>
                    ${a.status === "Scheduled" ? `
                        <button type="button" class="btn btn-sm btn-secondary"
                            onclick="cancelAppointment(${a.appointment_id})">
                            Cancel
                        </button>
                    ` : ""}
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("appointmentsTable").innerHTML = html;
}

async function cancelAppointment(appointmentId) {
    if (!confirm("Cancel this appointment?")) return;

    const res = await fetch(`${API_URL}/appointments/${appointmentId}/cancel`, {
        method: "PUT"
    });

    const result = await res.json();
    alert(result.message || "Appointment cancelled");

    await loadAppointments();
    await loadNotifications();
}

async function loadDonationHistory() {
    if (!donorProfile) return;

    const res = await fetch(`${API_URL}/donors/${donorProfile.donor_id}/history`);
    const result = await res.json();

    let html = `
        <div class="table-scroll">
        <table class="data-table">
            <thead><tr>
                <th>Donation ID</th>
                <th>Date</th>
                <th>Blood type</th>
                <th>Quantity</th>
                <th>Hospital</th>
                <th>Status</th>
            </tr></thead><tbody>
    `;

    result.data.forEach(d => {
        html += `
            <tr>
                <td>${d.donation_id}</td>
                <td>${d.donation_date}</td>
                <td>${d.blood_type}</td>
                <td>${d.quantity_ml}</td>
                <td>${d.hospital_name}</td>
                <td><span class="status-pill">${d.status}</span></td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("historyTable").innerHTML = html;
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
                    ${!n.is_read ? `
                        <button type="button" class="btn btn-sm btn-secondary"
                            onclick="markNotificationRead(${n.notification_id})">
                            Mark read
                        </button>
                    ` : ""}
                </td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;
    document.getElementById("notificationsBox").innerHTML = html;
}

document.getElementById("profileForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const response = await fetch(`${API_URL}/donors/${donorProfile.donor_id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            first_name: document.getElementById("updateFirstName").value,
            last_name: document.getElementById("updateLastName").value,
            phone: document.getElementById("updatePhone").value,
            health_status: document.getElementById("updateHealthStatus").value,
            weight_kg: document.getElementById("updateWeight").value,
            medication_restricted: document.getElementById("updateMedication").value === "true"
        })
    });

    const result = await response.json();

    if (!result.success) {
        alert(result.message || "Could not update profile");
        return;
    }

    alert("Profile updated successfully");
    await loadDonorProfile();
});

async function markNotificationRead(notificationId) {
    await fetch(`${API_URL}/notifications/${notificationId}/read`, {
        method: "PUT"
    });
    await loadNotifications();
}

async function init() {
    await loadDonorProfile();
    await loadHospitals();
    await loadAppointments();
    await loadDonationHistory();
    await loadNotifications();

    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    const minVal = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
    document.getElementById("appointmentDateTime").min = minVal;
}

init();
