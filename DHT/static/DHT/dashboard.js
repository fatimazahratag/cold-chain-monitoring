async function loadLatest() {
    try {
        const response = await fetch("/api/latest/");
        const data = await response.json();

        document.getElementById("lastTemp").textContent = data.temp + " °C";
        document.getElementById("lastHum").textContent = data.hum + " %";

        const lastUpdate = new Date(data.dt);
        const now = new Date();
        const diffSec = Math.floor((now - lastUpdate) / 1000);

        const hh = lastUpdate.getHours().toString().padStart(2, '0');
        const mm = lastUpdate.getMinutes().toString().padStart(2, '0');

        const timeString = `${hh}:${mm}`;

        document.getElementById("temp_time").textContent = `il y a : ${diffSec} sec (${timeString})`;
        document.getElementById("hum_time").textContent = `il y a : ${diffSec} sec (${timeString})`;

    } catch (error) {
        console.error("Erreur loadLatest :", error);
    }
}
setInterval(loadLatest, 5000);
loadLatest();