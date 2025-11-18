# Cold Chain Monitoring

## Contexte
Projet IoT pour un laboratoire d'analyses médicales. Permet de surveiller en temps réel la température (2–8 °C) et l'humidité des réfrigérateurs pour garantir la qualité des échantillons.

## Objectifs
- Lire la température et l’humidité via un capteur DHT11 connecté à un ESP8266.
- Envoyer les mesures toutes les 20 minutes vers un backend Django REST API.
- Afficher les données dans un tableau de bord web avec React et Chart.js.
- Déclencher des alertes (Email, Telegram, WhatsApp) en cas de dépassement de seuil.
- Gérer les tickets et assurer la traçabilité complète des incidents.

## Technologies
- **Matériel :** ESP8266 (NodeMCU), DHT11  
- **Backend :** Django + Django REST Framework  
- **Frontend :** React + Chart.js / HTML-CSS  
- **Base de données :** SQLite (dev), PostgreSQL (prod)  
- **Notifications :** SMTP, Telegram Bot API, WhatsApp Cloud API  


## Instructions
1. Brancher le capteur DHT11 à l’ESP8266.
2. Configurer le WiFi dans le code ESP8266.
3. Lancer le backend Django (`python manage.py runserver`).
4. Lancer le frontend React (`npm start`).
5. Surveiller les températures et humidités via le dashboard.

<img width="1084" height="665" alt="Screenshot 2025-11-18 184600" src="https://github.com/user-attachments/assets/6939b6f4-3000-4848-9fed-131fb648b267" />
<img width="1148" height="674" alt="Screenshot 2025-11-18 184544" src="https://github.com/user-attachments/assets/77030266-17f4-48f3-a147-e03910c6629f" />
<img width="837" height="232" alt="Screenshot 2025-11-18 184532" src="https://github.com/user-attachments/assets/09be9531-eb02-42ae-85bb-95282bc9f79c" />
<img width="1031" height="347" alt="Screenshot 2025-11-18 184510" src="https://github.com/user-attachments/assets/f62782a6-7e22-4350-a0ec-4c00540e0331" />
<img width="1240" height="570" alt="Screenshot 2025-11-18 184412" src="https://github.com/user-attachments/assets/e6cdeeaf-d4fc-431a-afc2-f12ceb82606f" />
