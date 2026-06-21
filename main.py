import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
import smtplib

# LISTA SERWISÓW DO MONITOROWANIA
URL_LIST = [
    "https://www.otodom.pl/pl/wyniki/wynajem/lokal/malopolskie/krakow/krakow/krakow?limit=36&areaMin=35&by=DEFAULT&direction=DESC",
    # Tutaj w przyszłości dopiszesz link z OLX lub Morizon
]

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("CREATE TABLE IF NOT EXISTS sent_links (url TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def send_email(link):
    sender_email = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    
    msg = EmailMessage()
    msg.set_content(f"Nowa oferta: {link}")
    msg['Subject'] = "Nowy lokal w Krakowie!"
    msg['From'] = sender_email
    msg['To'] = sender_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Błąd wysyłki: {e}")

def check_offers():
    headers = {'User-Agent': 'Mozilla/5.0'}
    conn = sqlite3.connect(DB_NAME)
    
    for url in URL_LIST:
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Selektor dla Otodom (jeśli dodasz OLX, selektor może wymagać zmiany!)
            links = [a['href'] for a in soup.select('a[data-cy="listing-item-link"]')]
            
            for link in links:
                full_link = f"https://www.otodom.pl{link}" if link.startswith('/') else link
                if not conn.execute("SELECT 1 FROM sent_links WHERE url=?", (full_link,)).fetchone():
                    print(f"Nowa oferta: {full_link}")
                    send_email(full_link)
                    conn.execute("INSERT INTO sent_links VALUES (?)", (full_link,))
                    conn.commit()
        except Exception as e:
            print(f"Błąd przy URL {url}: {e}")
            
    conn.close()

if __name__ == "__main__":
    init_db()
    check_offers()
