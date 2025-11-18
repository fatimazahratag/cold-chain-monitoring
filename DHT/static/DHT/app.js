const STATS_URL = "/stats/";

const tempAvg = document.getElementById('tempAvg');
const tempMax = document.getElementById('tempMax');
const tempMin = document.getElementById('tempMin');
const humAvg  = document.getElementById('humAvg');
const humMax  = document.getElementById('humMax');
const humMin  = document.getElementById('humMin');
const lastTemp = document.getElementById('lastTemp');
const lastHum  = document.getElementById('lastHum');
const statusEl = document.getElementById('status');
const tempIcon = document.getElementById('tempIcon');
const humIcon  = document.getElementById('humIcon');

let chart; // Chart.js instance
let currentView = 'temp'; // default

async function getStats() {
    statusEl.textContent = "Chargement...";
    try {
        const res = await fetch(STATS_URL);
        if(!res.ok) throw new Error(res.statusText);
        const data = await res.json();

        // Update cards
        tempAvg.textContent = data.temp_avg.toFixed(1) + " °C";
        tempMax.textContent = data.temp_max + " °C";
        tempMin.textContent = data.temp_min + " °C";
        humAvg.textContent  = data.hum_avg.toFixed(1) + " %";
        humMax.textContent  = data.hum_max + " %";
        humMin.textContent  = data.hum_min + " %";

        const last = data.history[data.history.length - 1];
        lastTemp.textContent = last.temp + " °C";
        lastHum.textContent  = last.hum + " %";

        // Draw chart
        drawChart(data, currentView);

        statusEl.textContent = "OK";
    } catch (err) {
        console.error(err);
        statusEl.textContent = "Erreur de chargement : " + err.message;
    }
}

function drawChart(data, view) {
    const ctx = document.getElementById('myChart').getContext('2d');
    const labels = data.history.map(e => new Date(e.dt).toLocaleString());
    const tempData = data.history.map(e => e.temp);
    const humData  = data.history.map(e => e.hum);

    if(chart) chart.destroy();

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: view === 'temp' ? [
                { label: "Température °C", data: tempData, borderColor: "red", fill: false }
            ] : [
                { label: "Humidité %", data: humData, borderColor: "blue", fill: false }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true, stepSize: view==='temp'?5:10 },
                x: {
                    ticks: {
                        maxTicksLimit: 12 // max 12 labels to avoid crowding
                    }
                }
            }
        }
    });
}


// Switch chart when clicking icons
tempIcon.addEventListener('click', () => {
    currentView = 'temp';
    getStats();
});
humIcon.addEventListener('click', () => {
    currentView = 'hum';
    getStats();
});

document.getElementById('refresh').addEventListener('click', getStats);
getStats();


document.getElementById("sendAlertBtn").addEventListener("click", function() {
    fetch("{% url 'send_email_alert' %}")
        .then(response => response.text())
        .then(data => {
            // Affiche le message dans le paragraphe
            document.getElementById("alertStatus").textContent = data;
        })
        .catch(error => {
            document.getElementById("alertStatus").textContent = "❌ Erreur lors de l’envoi de l’alerte.";
            console.error("Erreur:", error);
        });
});
