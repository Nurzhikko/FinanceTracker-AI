
const API_URL = window.location.origin;
let editingTransactionId = null;

async function loadSummary() {
    try {
        const response = await fetch(
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
        const response = await fetch(
            `${API_URL}/transactions`
        );

        if (!response.ok) {
            throw new Error("Failed to load transactions");
        }

        const data = await response.json();

        const tbody = document.getElementById(
            "transactions-body"
        );

        tbody.replaceChildren();

        if (data.transactions.length === 0) {
            const row = tbody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 6;
            cell.textContent = "No transactions yet.";
            return;
        }

        
data.transactions.forEach(transaction => {
    const row = tbody.insertRow();

    [
        transaction.id,
        transaction.title,
        transaction.category,
        transaction.type,
        Number(transaction.amount).toFixed(2)
    ].forEach(value => {
        const cell = row.insertCell();
        cell.textContent = value;
    });

    const actionsCell = row.insertCell();

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
            const response = await fetch(
                `${API_URL}/transactions/${transaction.id}`,
                { method: "DELETE" }
            );

            if (!response.ok) {
                throw new Error("Failed to delete transaction");
            }

            await loadDashboard();

        } catch (error) {
            console.error(error);
            alert("Could not delete transaction.");
            deleteButton.disabled = false;
        }
    });
    
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

    const submitButton = document.querySelector(
        '#transaction-form button[type="submit"]'
    );

    submitButton.textContent = "Save Changes";

    document.getElementById("transaction-form")
        .scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
});


actionsCell.appendChild(editButton);

    actionsCell.appendChild(deleteButton);
});


    } catch (error) {
        console.error("Transactions error:", error);
    }
}

async function loadDashboard() {
    await Promise.all([
        loadSummary(),
        loadTransactions(),
        loadExpenseChart()
    ]);
}

document.addEventListener(
    "DOMContentLoaded",
    loadDashboard
);



const transactionForm = document.getElementById(
    "transaction-form"
);

transactionForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const title = document.getElementById("title").value.trim();
    const amount = Number(document.getElementById("amount").value);
    const category = document.getElementById("category").value;
    const type = document.getElementById("type").value;

    if (!title || !Number.isFinite(amount) || amount <= 0) {
        alert("Please enter a valid title and amount.");
        return;
    }

    const transaction = {
        title: title,
        amount: amount,
        category: category,
        type: type
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

        const response = await fetch(url, {
            method: isEditing ? "PUT" : "POST",
            headers: {
            "Content-Type": "application/json"
            },
            body: JSON.stringify(transaction)
});


        if (!response.ok) {
            throw new Error("Failed to save transaction");
        }

        
        const successMessage = isEditing
            ? "Transaction updated successfully!"
            : "Transaction added successfully!";

        transactionForm.reset();

        editingTransactionId = null;
        submitButton.textContent = "Add Transaction";

        await loadDashboard();

        alert(successMessage);



    } catch (error) {
        console.error("Transaction error:", error);
        alert("Could not save transaction. Please try again.");

    } finally {
        submitButton.disabled = false;
    }
});



let expenseChart = null;

async function loadExpenseChart() {
    try {
        const response = await fetch(
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
                labels: labels,
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
