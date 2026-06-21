import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
import smtplib

# KONFIGURACJA
URL = "https://www.otodom.pl/pl/wyniki/wynajem/lokal/malopolskie/krakow/krakow/krakow?limit=36&areaMin=35&by=DEFAULT&direction=DESC"
DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("CREATE TABLE IF NOT EXISTS sent_links (url TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def send_email(link):
    sender_email = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    
    if not sender_email or not password:
        print("Błąd: Brak ustawionych zmiennych środowiskowych EMAIL_USER lub EMAIL_PASS")
        return

    msg = EmailMessage()
    msg.set_content(f"Nowa oferta na Otodom: {link}")
    msg['Subject'] = "Nowy lokal w Krakowie!"
    msg['From'] = sender_email
    msg['To'] = sender_email # Wysyłasz do siebie

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, password)
            smtp.send_message(msg)
        print(f"Wysłano maila: {link}")
    except Exception as e:
        print(f"Błąd wysyłania maila: {e}")

def check_for_new_offers():
    # Nagłówki udające przeglądarkę, aby zmniejszyć szansę na zablokowanie
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Szukanie linków do ogłoszeń
        links = [a['href'] for a in soup.select('a[data-cy="listing-item-link"]')]
        
        conn = sqlite3.connect(DB_NAME)
        for link in links:
            # Otodom czasem zwraca linki relatywne, czasem absolutne
            full_link = f"https://www.otodom.pl{link}" if link.startswith('/') else link
            
            # Sprawdzenie czy już wysłaliśmy ten link
            if not conn.execute("SELECT 1 FROM sent_links WHERE url=?", (full_link,)).fetchone():
                send_email(full_link)
                conn.execute("INSERT INTO sent_links VALUES (?)", (full_link,))
        
        conn.commit()
        conn.close()
        print("Sprawdzanie zakończone.")
        
    except Exception as e:
        print(f"Błąd podczas pobierania strony: {e}")

if __name__ == "__main__":
    init_db()
    check_for_new_offers()
