// const API_URL = "http://127.0.0.1:5000/api";
const API_URL = "https://blood-bank-management-system-production-0359.up.railway.app/api";

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
const signupRole = document.getElementById("signupRole");

if (signupRole) {
    signupRole.addEventListener("change", function () {

        const donorFields = document.getElementById("donorFields");
        const recipientFields = document.getElementById("recipientFields");

        const signupWeight = document.getElementById("signupWeight");
        const signupCondition = document.getElementById("signupCondition");
        const signupAge = document.getElementById("signupAge");

        if (this.value === "Donor") {

            signupAge.min = 18;

            donorFields.style.display = "block";
            recipientFields.style.display = "none";

            signupWeight.required = true;
            signupWeight.min = 45;

            signupCondition.required = false;
            signupCondition.value = "";

        } else if (this.value === "Recipient") {

            signupAge.min = 1;

            donorFields.style.display = "none";
            recipientFields.style.display = "block";

            signupWeight.required = false;
            signupWeight.value = "";

            signupCondition.required = true;

        } else {

            signupAge.min = 1;

            donorFields.style.display = "none";
            recipientFields.style.display = "none";

            signupWeight.required = false;
            signupCondition.required = false;

            signupWeight.value = "";
            signupCondition.value = "";
        }
    });
}

if (signupForm) {
    signupForm.addEventListener("submit", async function(e) {

        e.preventDefault();

        const role = document.getElementById("signupRole").value;
        const age = Number(document.getElementById("signupAge").value);
        const weight = Number(document.getElementById("signupWeight").value);

        if (role === "Donor" && age < 18) {
            alert("Donors must be at least 18 years old.");
            return;
        }

        if (role === "Donor" && weight < 45) {
            alert("Donor weight must be at least 45 kg.");
            return;
        }

        const payload = {
            first_name: document.getElementById("signupFirstName").value,
            last_name: document.getElementById("signupLastName").value,
            age: age,
            gender: document.getElementById("signupGender").value,
            email: document.getElementById("signupEmail").value.trim().toLowerCase(),
            password: document.getElementById("signupPassword").value,
            phone: document.getElementById("signupPhone").value,
            blood_type: document.getElementById("signupBloodType").value
        };

        let endpoint = "";

        if (role === "Donor") {

            endpoint = "/donors/register";

            payload.weight_kg = weight;
            payload.health_status = "Healthy";
            payload.medication_restricted = false;

        } else if (role === "Recipient") {

            endpoint = "/recipients/register";

            payload.medical_condition =
                document.getElementById("signupCondition").value;

        }else if (result.user.role === "MinistryOfHealth") {
    window.location.href = "ministry/ministry.html";
}
        else {

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

            document.getElementById("donorFields").style.display = "none";
            document.getElementById("recipientFields").style.display = "none";

        } catch (err) {

            alert("Server error. Could not create account.");
        }
    });
}

/* =========================================
   PASSWORD VISIBILITY
========================================= */

const togglePassword = document.getElementById("togglePassword");
const passwordInput = document.getElementById("password");

if (togglePassword && passwordInput) {

    togglePassword.addEventListener("click", function () {

        passwordInput.type =
            passwordInput.type === "password"
                ? "text"
                : "password";
    });
}

const toggleSignupPassword =
    document.getElementById("toggleSignupPassword");

const signupPassword =
    document.getElementById("signupPassword");

if (toggleSignupPassword && signupPassword) {

    toggleSignupPassword.addEventListener("click", function () {

        signupPassword.type =
            signupPassword.type === "password"
                ? "text"
                : "password";
    });
}