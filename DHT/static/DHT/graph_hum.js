let humChart;

async function drawHum() {
    const res = await fetch("/history/?t=" + Date.now());
    const data = await res.json();
    let raw = data.history;

    if (!raw || raw.length === 0) return;

    raw.sort((a, b) => new Date(a.dt) - new Date(b.dt));

    const labels = raw.map(item =>
        new Date(item.dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    );
    const hums = raw.map(item => item.hum);  // Humidity data

    const canvas = document.getElementById("humChart");
    const ctx = canvas.getContext("2d");

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (humChart) humChart.destroy();

    const gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, "rgba(0,0,255,0.5)");
    gradient.addColorStop(1, "rgba(0,0,255,0)");

    humChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Humidité (%)",
                data: hums,
                borderColor: "blue",
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

drawHum();
