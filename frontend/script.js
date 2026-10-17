
const API_URL = window.location.origin;

let editingTransactionId = null;
let expenseChart = null;
let accessToken = null;

const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");
const authScreen = document.getElementById("auth-screen");

const loginCard = document.getElementById("login-card");
const registerCard = document.getElementById("register-card");

const registerForm = document.getElementById("register-form");
const registerError = document.getElementById("register-error");

const transactionForm = document.getElementById("transaction-form");
const logoutButton = document.getElementById("logout-btn");

function showAuthCard(card) {
    loginCard.style.display = "none";
    registerCard.style.display = "none";
    card.style.display = "block";
}

function getAuthHeaders() {
    return {
        Authorization: `Bearer ${accessToken}`
    };
}

async function authenticatedFetch(url, options = {}) {
    if (!accessToken) {
        throw new Error("Please sign in first.");
    }

    const tokenUsed = accessToken;

    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            ...getAuthHeaders()
        }
    });

    if (response.status === 401) {
        if (accessToken === tokenUsed) {
            logout();
        }

        throw new Error(
            "Session expired. Please sign in again."
        );
    }

    return response;
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document
        .getElementById("login-email")
        .value.trim();

    const password = document
        .getElementById("login-password")
        .value;

    loginError.textContent = "";
    loginError.style.color = "#dc2626";

    const button = loginForm.querySelector(
        'button[type="submit"]'
    );

    button.disabled = true;

    try {
        const response = await fetch(
            `${API_URL}/auth/login`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email,
                    password
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : "Login failed"
            );
        }

        if (!data.access_token) {
            throw new Error("No access token received");
        }

        accessToken = data.access_token;

        document.getElementById(
            "login-password"
        ).value = "";

        authScreen.style.display = "none";

        await loadDashboard();

        console.log("Login successful");

    } catch (error) {
        console.error("Login error:", error);

        if (!accessToken) {
            loginError.textContent = error.message;
        }

    } finally {
        button.disabled = false;
    }
});

async function loadSummary() {
    try {
        const response = await authenticatedFetch(
            `${API_URL}/analytics/summary`
        );

        if (!response.ok) {
            throw new Error("Failed to load summary");
        }

        const data = await response.json();

        document.getElementById("balance").textContent =
            Number(data.balance).toFixed(2);

        document.getElementById("income").textContent =
            Number(data.total_income).toFixed(2);

        document.getElementById("expenses").textContent =
            Number(data.total_expenses).toFixed(2);

    } catch (error) {
        console.error("Summary error:", error);
    }
}

async function loadTransactions() {
    try {
        const response = await authenticatedFetch(
            `${API_URL}/transactions`
        );

        if (!response.ok) {
            throw new Error(
                "Failed to load transactions"
            );
        }

        const data = await response.json();

        const tbody = document.getElementById(
            "transactions-body"
        );

        tbody.replaceChildren();

        if (data.transactions.length === 0) {
            const row = tbody.insertRow();
            const cell = row.insertCell();

            cell.colSpan = 5;
            cell.textContent = "No transactions yet.";

            return;
        }

        data.transactions.forEach(transaction => {
            const row = tbody.insertRow();

            [
                transaction.title,
                transaction.category,
                transaction.type,
                Number(transaction.amount).toFixed(2)
            ].forEach(value => {
                const cell = row.insertCell();
                cell.textContent = value;
            });

            const actionsCell = row.insertCell();

            const editButton = document.createElement("button");

            editButton.textContent = "Edit";
            editButton.className = "edit-btn";

            editButton.addEventListener("click", () => {
                editingTransactionId = transaction.id;

                document.getElementById("title").value =
                    transaction.title;

                document.getElementById("amount").value =
                    transaction.amount;

                document.getElementById("category").value =
                    transaction.category;

                document.getElementById("type").value =
                    transaction.type;

                const submitButton = transactionForm.querySelector(
                    'button[type="submit"]'
                );

                submitButton.textContent = "Save Changes";

                transactionForm.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
            });

            const deleteButton = document.createElement("button");

            deleteButton.textContent = "Delete";
            deleteButton.className = "delete-btn";

            deleteButton.addEventListener("click", async () => {
                const confirmed = confirm(
                    `Delete transaction "${transaction.title}"?`
                );

                if (!confirmed) return;

                deleteButton.disabled = true;

                try {
                    const response = await authenticatedFetch(
                        `${API_URL}/transactions/${transaction.id}`,
                        {
                            method: "DELETE"
                        }
                    );

                    if (!response.ok) {
                        throw new Error(
                            "Failed to delete transaction"
                        );
                    }

                    await loadDashboard();

                } catch (error) {
                    console.error(error);
                    alert(error.message);
                    deleteButton.disabled = false;
                }
            });

            actionsCell.appendChild(editButton);
            actionsCell.appendChild(deleteButton);
        });

    } catch (error) {
        console.error("Transactions error:", error);
    }
}

transactionForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!accessToken) {
        alert("Please sign in first.");
        authScreen.style.display = "flex";
        return;
    }

    const title = document.getElementById("title").value.trim();

    const amount = Number(
        document.getElementById("amount").value
    );

    const category = document.getElementById("category").value;
    const type = document.getElementById("type").value;

    if (!title || !Number.isFinite(amount) || amount <= 0) {
        alert("Please enter a valid title and amount.");
        return;
    }

    const transaction = {
        title,
        amount,
        category,
        type
    };

    const submitButton = transactionForm.querySelector(
        'button[type="submit"]'
    );

    submitButton.disabled = true;

    try {
        const isEditing = editingTransactionId !== null;

        const url = isEditing
            ? `${API_URL}/transactions/${editingTransactionId}`
            : `${API_URL}/transactions`;

        const response = await authenticatedFetch(url, {
            method: isEditing ? "PUT" : "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(transaction)
        });

        if (!response.ok) {
            const data = await response.json();

            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : "Failed to save transaction"
            );
        }

        const message = isEditing
            ? "Transaction updated successfully!"
            : "Transaction added successfully!";

        transactionForm.reset();

        editingTransactionId = null;
        submitButton.textContent = "Add Transaction";

        await loadDashboard();

        alert(message);

    } catch (error) {
        console.error("Transaction error:", error);
        alert(error.message);

    } finally {
        submitButton.disabled = false;
    }
});

async function loadExpenseChart() {
    try {
        const response = await authenticatedFetch(
            `${API_URL}/analytics/categories`
        );

        if (!response.ok) {
            throw new Error("Failed to load analytics");
        }

        const data = await response.json();

        const canvas = document.getElementById("expenseChart");

        if (!canvas || typeof Chart === "undefined") {
            console.error("Chart.js is not available");
            return;
        }

        const labels = data.categories.map(
            item => item.category
        );

        const values = data.categories.map(
            item => item.total
        );

        if (expenseChart) {
            expenseChart.destroy();
        }

        expenseChart = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        "#2563eb",
                        "#16a34a",
                        "#f59e0b",
                        "#ef4444",
                        "#8b5cf6",
                        "#06b6d4"
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "65%",
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });

    } catch (error) {
        console.error("Chart error:", error);
    }
}

async function loadDashboard() {
    if (!accessToken) {
        return;
    }

    await Promise.all([
        loadSummary(),
        loadTransactions(),
        loadExpenseChart()
    ]);
}

document.getElementById("show-register").addEventListener(
    "click",
    (event) => {
        event.preventDefault();

        loginError.textContent = "";
        registerError.textContent = "";

        showAuthCard(registerCard);
    }
);

document.getElementById("show-login").addEventListener(
    "click",
    (event) => {
        event.preventDefault();

        registerError.textContent = "";
        showAuthCard(loginCard);
    }
);

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = document
        .getElementById("register-name")
        .value.trim();

    const email = document
        .getElementById("register-email")
        .value.trim();

    const password = document
        .getElementById("register-password")
        .value;

    registerError.textContent = "";

    const submitButton = registerForm.querySelector(
        'button[type="submit"]'
    );

    submitButton.disabled = true;

    try {
        const response = await fetch(
            `${API_URL}/auth/register`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name,
                    email,
                    password
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : "Registration failed"
            );
        }

        registerForm.reset();

        showAuthCard(loginCard);

        document.getElementById("login-email").value =
            email;

        loginError.style.color = "#16a34a";
        loginError.textContent =
            "Account created successfully! Please sign in.";

    } catch (error) {
        registerError.textContent = error.message;

    } finally {
        submitButton.disabled = false;
    }
});

function logout() {
    accessToken = null;
    editingTransactionId = null;

    transactionForm.reset();

    const submitButton = transactionForm.querySelector(
        'button[type="submit"]'
    );

    submitButton.textContent = "Add Transaction";

    document.getElementById("balance").textContent = "0.00";
    document.getElementById("income").textContent = "0.00";
    document.getElementById("expenses").textContent = "0.00";

    const tbody = document.getElementById("transactions-body");

    tbody.replaceChildren();

    const row = tbody.insertRow();
    const cell = row.insertCell();

    cell.colSpan = 5;
    cell.textContent = "Sign in to view transactions.";

    if (expenseChart) {
        expenseChart.destroy();
        expenseChart = null;
    }

    loginForm.reset();
    loginError.textContent = "";
    loginError.style.color = "#dc2626";

    registerForm.reset();
    registerError.textContent = "";

    showAuthCard(loginCard);
    authScreen.style.display = "flex";
}

logoutButton.addEventListener("click", logout);

document.querySelectorAll(".toggle-password").forEach(button => {
    button.addEventListener("click", () => {
        const input = document.getElementById(
            button.dataset.target
        );

        if (!input) return;

        const showPassword = input.type === "password";

        input.type = showPassword ? "text" : "password";

        button.textContent = showPassword ? "Hide" : "Show";

        button.setAttribute(
            "aria-label",
            showPassword ? "Hide password" : "Show password"
        );

        button.setAttribute(
            "aria-pressed",
            String(showPassword)
        );
    });
});
