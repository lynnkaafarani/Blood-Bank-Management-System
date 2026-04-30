const API_URL = "http://127.0.0.1:5000/api";

const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();
        const message = document.getElementById("message");

        try {
            const response = await fetch(`${API_URL}/login`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (!result.success) {
                message.textContent = result.message || "Login failed";
                return;
            }

            localStorage.setItem("bbms_user", JSON.stringify(result.user));

            if (result.user.role === "Administrator") {
                window.location.href = "admin/admin.html";
            } else if (result.user.role === "HospitalStaff") {
                window.location.href = "staff/staff.html";
            } else if (result.user.role === "Donor") {
                window.location.href = "donor/donor.html";
            } else if (result.user.role === "Recipient") {
                window.location.href = "recipient/recipient.html";
            }

        } catch (err) {
            message.textContent = "Server error. Make sure backend is running.";
        }
    });
}

const signupForm = document.getElementById("signupForm");

if (signupForm) {
    signupForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const role = document.getElementById("signupRole").value;

        const payload = {
            first_name: document.getElementById("signupFirstName").value,
            last_name: document.getElementById("signupLastName").value,
            age: document.getElementById("signupAge").value,
            gender: document.getElementById("signupGender").value,
            email: document.getElementById("signupEmail").value,
            password: document.getElementById("signupPassword").value,
            phone: document.getElementById("signupPhone").value,
            blood_type: document.getElementById("signupBloodType").value
        };

        let endpoint = "";

        if (role === "Donor") {
            endpoint = "/donors/register";
            payload.weight_kg = document.getElementById("signupWeight").value;
            payload.health_status = "Healthy";
            payload.medication_restricted = false;
        } else if (role === "Recipient") {
            endpoint = "/recipients/register";
            payload.medical_condition = document.getElementById("signupCondition").value;
        } else {
            alert("Select Donor or Recipient");
            return;
        }

        try {
            const response = await fetch(`${API_URL}${endpoint}`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (!result.success) {
                alert(result.message || "Signup failed");
                return;
            }

            alert("Account created successfully. You can now login.");
            this.reset();

        } catch (err) {
            alert("Server error. Could not create account.");
        }
    });
}