/**
 * SentiAI Pro - Main Application JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
    // Mobile Sidebar Toggle
    const sidebar = document.getElementById("sidebar");
    const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");

    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener("click", function () {
            sidebar.classList.toggle("show");
        });
    }

    if (sidebarCloseBtn && sidebar) {
        sidebarCloseBtn.addEventListener("click", function () {
            sidebar.classList.remove("show");
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", function (event) {
        if (
            window.innerWidth < 992 &&
            sidebar &&
            sidebar.classList.contains("show") &&
            !sidebar.contains(event.target) &&
            sidebarToggleBtn &&
            !sidebarToggleBtn.contains(event.target)
        ) {
            sidebar.classList.remove("show");
        }
    });

    // Delete single record handler from recent table
    document.querySelectorAll(".delete-btn").forEach((btn) => {
        btn.addEventListener("click", async function () {
            const recordId = this.getAttribute("data-id");
            if (!recordId) return;

            if (!confirm("Are you sure you want to delete this record?")) {
                return;
            }

            try {
                const res = await fetch(`/api/history/delete/${recordId}`, {
                    method: "POST"
                });
                const data = await res.json();
                if (data.success) {
                    const row = document.getElementById(`row-${recordId}`);
                    if (row) {
                        row.style.transition = "all 0.3s ease";
                        row.style.opacity = "0";
                        setTimeout(() => row.remove(), 300);
                    }
                    showToast("Record deleted successfully", "info");
                } else {
                    alert(data.error || "Failed to delete record");
                }
            } catch (err) {
                alert("Network error while deleting record");
            }
        });
    });
});

/**
 * Shows Bootstrap Toast Notification
 * @param {string} message - Toast text
 * @param {string} type - 'success' | 'danger' | 'warning' | 'info'
 */
function showToast(message, type = "success") {
    const toastEl = document.getElementById("liveToast");
    if (!toastEl) return;

    const toastText = document.getElementById("toastText");
    const toastIcon = document.getElementById("toastIcon");

    toastText.textContent = message;

    // Reset background and icon classes
    toastEl.className = "toast align-items-center text-white border-0 shadow";
    let iconClass = "bi bi-check-circle-fill";

    if (type === "success") {
        toastEl.classList.add("bg-success");
        iconClass = "bi bi-check-circle-fill";
    } else if (type === "danger") {
        toastEl.classList.add("bg-danger");
        iconClass = "bi bi-exclamation-triangle-fill";
    } else if (type === "warning") {
        toastEl.classList.add("bg-warning", "text-dark");
        iconClass = "bi bi-exclamation-circle-fill";
    } else if (type === "info") {
        toastEl.classList.add("bg-info", "text-dark");
        iconClass = "bi bi-info-circle-fill";
    }

    if (toastIcon) {
        toastIcon.className = `${iconClass} fs-5`;
    }

    const toast = new bootstrap.Toast(toastEl, { delay: 3500 });
    toast.show();
}
