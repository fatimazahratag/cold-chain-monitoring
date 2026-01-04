# -*- coding: utf-8 -*-
import os
import sys
import json
import django
import paho.mqtt.client as mqtt
import time
import signal

# 🔹 Config Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projet.settings")
django.setup()

from DHT.models import Dht11

class DHTSubscriber:
    def __init__(self):
        self.client = None
        self.running = True
        self.message_count = 0
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[{time.strftime('%H:%M:%S')}] ✅ Connecté au broker MQTT")
            client.subscribe("salle1/dht11")
            print(f"[{time.strftime('%H:%M:%S')}] 📡 Abonné au topic: salle1/dht11")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Erreur connexion MQTT, code: {rc}")
            # Tentative de reconnexion
            time.sleep(5)
            client.reconnect()
    
    def on_message(self, client, userdata, msg):
        try:
            self.message_count += 1
            payload = msg.payload.decode('utf-8')
            print(f"\n[{time.strftime('%H:%M:%S')}] 📨 Message #{self.message_count}")
            print(f"   Topic: {msg.topic}")
            print(f"   Données: {payload}")
            
            # Décodage JSON
            data = json.loads(payload)
            temp = data.get('t')
            hum = data.get('h')
            
            # Validation basique
            if temp is None or hum is None:
                print(f"   ⚠️  Données manquantes")
                return
            
            # Conversion en float
            temp = float(temp)
            hum = float(hum)
            
            # Enregistrement dans la base de données
            Dht11.objects.create(temp=temp, humidity=hum)
            print(f"   💾 Sauvegardé: {temp}°C, {hum}%")
            
        except json.JSONDecodeError as e:
            print(f"   ❌ Erreur JSON: {e}")
        except ValueError as e:
            print(f"   ❌ Erreur conversion: {e}")
        except Exception as e:
            print(f"   ❌ Erreur inattendue: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Déconnecté inopinément, reconnexion...")
            time.sleep(5)
            try:
                client.reconnect()
            except:
                pass
    
    def start(self):
        print(f"[{time.strftime('%H:%M:%S')}] 🚀 Démarrage du subscriber DHT11...")
        
        # Configuration du client MQTT
        self.client = mqtt.Client(client_id=f"django_dht_{int(time.time())}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Configuration de reconnexion automatique
        self.client.reconnect_delay_set(min_delay=1, max_delay=60)
        
        try:
            # Connexion au broker
            self.client.connect("192.168.1.3", 1883, 60)
            
            # Boucle principale
            self.client.loop_start()
            
            print(f"[{time.strftime('%H:%M:%S')}] 👂 En écoute des messages...")
            print(f"[{time.strftime('%H:%M:%S')}] 📊 Messages toutes les 20s (ESP delay)")
            print("-" * 50)
            
            # Boucle infinie pour maintenir le programme en vie
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n[{time.strftime('%H:%M:%S')}] 🛑 Arrêt demandé...")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Erreur critique: {e}")
        finally:
            self.stop()
    
    def stop(self):
        self.running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        print(f"\n[{time.strftime('%H:%M:%S')}] 👋 Subscriber arrêté")
        print(f"[{time.strftime('%H:%M:%S')}] 📊 Total messages traités: {self.message_count}")

def signal_handler(sig, frame):
    print(f"\n[{time.strftime('%H:%M:%S')}] Signal d'interruption reçu")
    sys.exit(0)

if __name__ == "__main__":
    # Gestion des signaux pour un arrêt propre
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    subscriber = DHTSubscriber()
    subscriber.start()