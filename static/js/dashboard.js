/**
 * SentiAI Pro - Dashboard Charts and Real-time Metric Updates using Chart.js
 */

document.addEventListener("DOMContentLoaded", function () {
    let pieChartInstance = null;
    let barChartInstance = null;
    let timelineChartInstance = null;

    const data = window.dashboardData || {
        total: 0,
        positive: 0,
        negative: 0,
        neutral: 0,
        positive_pct: 0,
        negative_pct: 0,
        neutral_pct: 0,
        avg_confidence: 0,
        timeline: {}
    };

    // Color definitions
    const colors = {
        positive: "#10b981",
        neutral: "#64748b",
        negative: "#ef4444",
        positiveLight: "rgba(16, 185, 129, 0.15)",
        neutralLight: "rgba(100, 116, 139, 0.15)",
        negativeLight: "rgba(239, 68, 68, 0.15)"
    };

    initCharts(data);

    // Refresh Dashboard button
    const refreshBtn = document.getElementById("refreshDashboardBtn");
    const refreshIcon = document.getElementById("refreshIcon");

    if (refreshBtn) {
        refreshBtn.addEventListener("click", async function () {
            if (refreshIcon) refreshIcon.classList.add("spin");
            try {
                const res = await fetch("/api/stats");
                const json = await res.json();
                if (json.success) {
                    updateDashboardUI(json.data);
                    showToast("Dashboard metrics refreshed", "success");
                }
            } catch (err) {
                showToast("Failed to refresh dashboard data", "danger");
            } finally {
                if (refreshIcon) refreshIcon.classList.remove("spin");
            }
        });
    }

    function initCharts(stats) {
        initPieChart(stats);
        initBarChart(stats);
        initTimelineChart(stats.timeline || {});
    }

    function initPieChart(stats) {
        const ctx = document.getElementById("sentimentPieChart");
        if (!ctx) return;

        // If no records yet, show empty placeholder slice
        const total = stats.total || 0;
        const counts = total > 0 
            ? [stats.positive, stats.neutral, stats.negative] 
            : [1, 1, 1];
        const bgColors = total > 0
            ? [colors.positive, colors.neutral, colors.negative]
            : ["#e2e8f0", "#cbd5e1", "#e2e8f0"];

        pieChartInstance = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["Positive", "Neutral", "Negative"],
                datasets: [{
                    data: counts,
                    backgroundColor: bgColors,
                    borderWidth: 2,
                    borderColor: "#ffffff",
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "72%",
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                if (total === 0) return " No data yet";
                                const label = context.label || "";
                                const val = context.raw || 0;
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${label}: ${val} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    function initBarChart(stats) {
        const ctx = document.getElementById("sentimentBarChart");
        if (!ctx) return;

        barChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["Positive", "Neutral", "Negative"],
                datasets: [{
                    label: "Review Count",
                    data: [stats.positive, stats.neutral, stats.negative],
                    backgroundColor: [colors.positive, colors.neutral, colors.negative],
                    borderRadius: 8,
                    maxBarThickness: 50
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` Count: ${ctx.raw} reviews`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: "#f1f5f9" }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    function initTimelineChart(timelineObj) {
        const ctx = document.getElementById("sentimentTimelineChart");
        if (!ctx) return;

        let labels = Object.keys(timelineObj);
        if (labels.length === 0) {
            labels = ["Today"];
            timelineObj = { "Today": { positive: 0, neutral: 0, negative: 0 } };
        }

        const posData = labels.map(l => (timelineObj[l] ? timelineObj[l].positive : 0));
        const neuData = labels.map(l => (timelineObj[l] ? timelineObj[l].neutral : 0));
        const negData = labels.map(l => (timelineObj[l] ? timelineObj[l].negative : 0));

        timelineChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Positive",
                        data: posData,
                        borderColor: colors.positive,
                        backgroundColor: colors.positiveLight,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: "Neutral",
                        data: neuData,
                        borderColor: colors.neutral,
                        backgroundColor: colors.neutralLight,
                        tension: 0.3,
                        fill: false,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: "Negative",
                        data: negData,
                        borderColor: colors.negative,
                        backgroundColor: colors.negativeLight,
                        tension: 0.3,
                        fill: false,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top",
                        labels: { boxWidth: 12, font: { size: 12 } }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: "#f1f5f9" }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    function updateDashboardUI(stats) {
        // Update metric values
        document.getElementById("statTotal").textContent = stats.total;
        document.getElementById("statPosCount").textContent = stats.positive;
        document.getElementById("statPosPct").textContent = `${stats.positive_pct}%`;
        document.getElementById("progressPos").style.width = `${stats.positive_pct}%`;

        document.getElementById("statNegCount").textContent = stats.negative;
        document.getElementById("statNegPct").textContent = `${stats.negative_pct}%`;
        document.getElementById("progressNeg").style.width = `${stats.negative_pct}%`;

        document.getElementById("statNeuCount").textContent = stats.neutral;
        document.getElementById("statNeuPct").textContent = `${stats.neutral_pct}%`;
        document.getElementById("progressNeu").style.width = `${stats.neutral_pct}%`;

        const avgLabel = document.getElementById("avgConfLabel");
        if (avgLabel) avgLabel.textContent = `${stats.avg_confidence}%`;

        document.getElementById("pieLegendPos").textContent = stats.positive;
        document.getElementById("pieLegendNeu").textContent = stats.neutral;
        document.getElementById("pieLegendNeg").textContent = stats.negative;

        // Update Pie Chart
        if (pieChartInstance) {
            const counts = stats.total > 0 
                ? [stats.positive, stats.neutral, stats.negative] 
                : [1, 1, 1];
            pieChartInstance.data.datasets[0].data = counts;
            pieChartInstance.update();
        }

        // Update Bar Chart
        if (barChartInstance) {
            barChartInstance.data.datasets[0].data = [stats.positive, stats.neutral, stats.negative];
            barChartInstance.update();
        }

        // Update Timeline
        if (timelineChartInstance && stats.timeline) {
            const labels = Object.keys(stats.timeline);
            if (labels.length > 0) {
                timelineChartInstance.data.labels = labels;
                timelineChartInstance.data.datasets[0].data = labels.map(l => stats.timeline[l].positive);
                timelineChartInstance.data.datasets[1].data = labels.map(l => stats.timeline[l].neutral);
                timelineChartInstance.data.datasets[2].data = labels.map(l => stats.timeline[l].negative);
                timelineChartInstance.update();
            }
        }
    }
});
