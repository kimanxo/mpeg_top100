import requests
from settings import USERNAME, PASSWORD


def fetch_all_remote_vod(session, BASE_URL, type):
    all_episodes = []
    page = 0
    max_per_page = 100

    while True:
        url = f"{BASE_URL}/vod_json?max={max_per_page}&server_id=0&status=0&type={type}&category=0&page={page}"
        try:
            response = session.get(url)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            total = data.get("total", 0)

            all_episodes.extend(items)
            print(f"📦 Page {page} fetched: {len(items)} items.")

            # Break if we've fetched all items
            if len(all_episodes) >= total:
                break

            page += 1

        except Exception as e:
            print(f"❌ Failed to fetch page {page}: {e}")
            break

    print(f"✅ Total episodes fetched: {len(all_episodes)}")
    return all_episodes


def fetch_all_remote_series(session, BASE_URL):
    all_series = []
    page = 0
    max_per_page = 100

    while True:
        url = f"{BASE_URL}/serie_json?max={max_per_page}&page={page}"
        try:
            response = session.get(url)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            total = data.get("total", 0)

            all_series.extend(items)
            print(f"📦 Page {page} fetched: {len(items)} items.")

            # Break if we've fetched all items
            if len(all_series) >= total:
                break

            page += 1

        except Exception as e:
            print(f"❌ Failed to fetch page {page}: {e}")
            break

    print(f"✅ Total series fetched: {len(all_series)}")
    return all_series


def login(base_url, username=USERNAME, password=PASSWORD):
    session = requests.Session()
    login_url = f"{base_url}/login.php"
    login_payload = {"action": "login", "username": username, "password": password}
    try:
        login_response = session.post(login_url, json=login_payload, timeout=10)
        login_response.raise_for_status()
        print("✅ Logged in successfully")
        return session
    except requests.RequestException as e:
        print(f"❌ Login failed: {e}")
        return None


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def get_tomatoes(type: str, network: str) -> list:
    service = Service(executable_path="/usr/bin/chromedriver")  # Update path if needed
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 30)

    url = f"https://www.rottentomatoes.com/browse/{type}/affiliates:{network}~sort:popular"
    driver.get(url)

    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-qa="discovery-media-list-item-title"]')
        )
    )

    for i in range(10):
        try:
            load_more_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[data-qa="dlp-load-more-button"]')
                )
            )
            load_more_btn.click()
            time.sleep(5)
        except Exception:
            break

    movie_elements = driver.find_elements(
        By.CSS_SELECTOR, '[data-qa="discovery-media-list-item-title"]'
    )
    movies = [el.text for el in movie_elements]

    driver.quit()
    return movies


#####################################
# Available Networks:
# - netflix
# - disney-plus
# - prime-video
#####################################
# Available Types:
# - movies_at_home
# - tv_series_browse
#####################################


