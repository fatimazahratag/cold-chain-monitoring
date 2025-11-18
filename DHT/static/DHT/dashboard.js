async function loadLatest() {
    const res = await fetch("/latest/");
    const data = await res.json();

    document.getElementById("tempValue").textContent = data.temp + " °C";
    document.getElementById("humValue").textContent = data.hum + " %";

    const dt = new Date(data.dt);
    const diff = Math.floor((Date.now() - dt.getTime()) / 1000);

    document.getElementById("tempAgo").textContent = "Il y a " + diff + " sec";
    document.getElementById("humAgo").textContent = "Il y a " + diff + " sec";
}

loadLatest();
setInterval(loadLatest, 5000);
