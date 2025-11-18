let chart;

async function drawTemp() {
    const res = await fetch("/history/?t=" + Date.now());
    const data = await res.json();
    let raw = data.history;

    if (!raw || raw.length === 0) return;

    raw.sort((a, b) => new Date(a.dt) - new Date(b.dt));

    const labels = raw.map(item =>
        new Date(item.dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    );
    const temps = raw.map(item => item.temp);

    const canvas = document.getElementById("tempChart");
    const ctx = canvas.getContext("2d");

    // FULL CANVAS CLEAR
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (chart) chart.destroy();

    // Gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, "rgba(255,0,0,0.5)");
    gradient.addColorStop(1, "rgba(255,0,0,0)");

    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Température (°C)",
                data: temps,
                borderColor: "red",
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.35,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

drawTemp();
