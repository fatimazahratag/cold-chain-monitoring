// Crée un objet Audio pour le son d'alerte
const alertSound = new Audio("{% static 'DHT/sounds/alert.mp3' %}");
alertSound.loop = true; // boucle le son

let userStopped = false; // flag pour savoir si l'utilisateur a stoppé l'alerte

// bouton pour arrêter l'alerte
const stopBtn = document.getElementById('stopAlertBtn');
stopBtn.addEventListener('click', () => {
    alertSound.pause();
    alertSound.currentTime = 0;
    userStopped = true; // bloque le son même si les seuils sont dépassés
    stopBtn.style.display = 'none';
});

// Fonction qui vérifie les valeurs et joue le son si nécessaire
async function checkAlerts() {
  try {
    const response = await fetch("/api/latest/");
    const data = await response.json();

    // Définir les seuils critiques
    const tempMin = 2;   // température min
    const tempMax = 8;   // température max
    const humMin = 30;   // humidité min
    const humMax = 70;   // humidité max

    // Vérifie si les valeurs sont hors seuils
    if ((data.temperature < tempMin || data.temperature > tempMax ||
         data.humidity < humMin || data.humidity > humMax) && !userStopped) {
      if (alertSound.paused) {
          alertSound.play(); // joue le son si pas déjà en train
          stopBtn.style.display = 'inline-block'; // afficher le bouton
          console.log("⚠ Alerte critique ! Son joué.");
      }
    } else {
      // si tout est OK, on arrête le son et réinitialise userStopped
      if (!alertSound.paused) {
          alertSound.pause();
          alertSound.currentTime = 0;
      }
      userStopped = false;
      stopBtn.style.display = 'none';
    }

  } catch (err) {
    console.error("Erreur lors de la vérification des alertes :", err);
  }
}

// Vérifie les mesures toutes les 5 secondes
setInterval(checkAlerts, 5000);
checkAlerts();
