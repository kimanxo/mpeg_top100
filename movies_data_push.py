import requests
from utils import fetch_all_remote_vod, get_data
import time

def categorize_top_movies(session, SERVER_ID, BASE_URL):
    try:
        # Step 1: Fetch all remote movies from the server
        remote_movies = fetch_all_remote_vod(session, BASE_URL, "movies")

        # Extract movie names -> ids from remote movies
        remote_movie_map = {}
        for movie in remote_movies:
            path = movie.get("path", "")
            if path and movie.get("id"):
                filename = path.split("/")[-1]
                name_part = filename.split("(")[0]
                normalized_name = name_part.strip().lower()
                remote_movie_map[normalized_name] = movie.get("id")

        # Step 2: Load tomatoes (top 200 movies by each service)
        print("Fetching tomatoes for netflix mvoies...")
        netflix_tomatoes = get_data("movies", "netflix")
        print("Fetched tomatoes for netflix movies.")
        time.sleep(15)  # Sleep to avoid rate limiting

        print("Fetching tomatoes for prime video movies...")
        prime_tomatoes = get_data("movies", "amazon-prime-video")
        print("Fetched tomatoes for prime video movies.")
        time.sleep(15)  # Sleep to avoid rate limiting

        print("Fetching tomatoes for disney+ movies...")
        disney_tomatoes = get_data("movies", "disney-plus")
        print("Fetched tomatoes for disney plus movies.")
        time.sleep(15)  # Sleep to avoid rate limiting

        # Helper function to normalize movie names
        def normalize_name(name):
            return name.strip().lower()

        # Function to match tomatoes against fetched movies
        def match_movies(remote_map, tomatoes):
            matches = []
            for tomato_name in tomatoes:
                normalized_name = normalize_name(tomato_name)
                if normalized_name in remote_map:
                    matches.append(
                        {"name": tomato_name, "id": remote_map[normalized_name]}
                    )
            return matches

        # Match movies for each service
        print("Matching tomatoes with remote vod...")
        netflix_matches = match_movies(remote_movie_map, netflix_tomatoes)
        print(f"Netflix Matches ({len(netflix_matches)})")
        prime_matches = match_movies(remote_movie_map, prime_tomatoes)
        print(f"Prime Video Matches ({len(prime_matches)})")
        disney_matches = match_movies(remote_movie_map, disney_tomatoes)
        print(f"Disney+ Matches ({len(disney_matches)})")

        # Fetch existing categories
        print("Fetching existing categories from the server...")
        cat_url = f"{BASE_URL}/category_json?nolist=1&max=0&type=33"
        cat_response = session.get(cat_url)
        cat_response.raise_for_status()
        cat_data = cat_response.json()
        existing_categories = cat_data.get("items", [])

        # Build list of existing categories with names and ids
        existing_categories_list = [
            {"name": cat.get("nm"), "id": cat.get("id")}
            for cat in existing_categories
            if cat.get("nm") and cat.get("id")
        ]

        # Define target categories to delete
        target_categories = ["top 100 netflix", "top 100 prime", "top 100 disney"]

        # Delete target categories if they exist
        for target_name in target_categories:
            normalized_target = target_name.strip().lower()
            matched_category = next(
                (
                    cat
                    for cat in existing_categories_list
                    if cat["name"].strip().lower() == normalized_target
                ),
                None,
            )
            if matched_category:
                cat_id = matched_category["id"]
                delete_url = f"{BASE_URL}/category_json?id={cat_id}&action=delete"
                try:
                    delete_response = session.get(delete_url)
                    if delete_response.status_code == 200:
                        print(
                            f"✅ Deleted category '{target_name}'  successfully."
                        )
                    else:
                        print(
                            f"❌ Failed to delete category '{target_name}' (ID: {cat_id}): {delete_response.status_code} - {delete_response.text}"
                        )
                except Exception as delete_exc:
                    print(
                        f"❌ Error deleting category '{target_name}' (ID: {cat_id}): {delete_exc}"
                    )
            else:
                print(f"ℹ️ Category '{target_name}' does not exist.")

        # Create new categories and build a category map
        category_map = {}
        for cat_name in target_categories:
            form_data = {
                "action": "add",
                "name": cat_name,
                "title": cat_name,
                "type": 33,
                "flag_adult": "off",
                "server_id": SERVER_ID,
            }
            try:
                res = session.post(
                    f"{BASE_URL}/category_item", data=form_data, timeout=10
                )
                res.raise_for_status()
                cat_id = res.json().get("id") or res.text
                print(f"✅ Created category: '{cat_name}'")
                category_map[cat_name.lower()] = cat_id
            except requests.RequestException as e:
                print(f"❌ Failed to create category '{cat_name}': {e}")

        # Step: Add matched movies to their respective categories
        category_matches = {
            target_categories[0]: netflix_matches,
            target_categories[1]: prime_matches,
            target_categories[2]: disney_matches,
        }

        for cat_name, matches in category_matches.items():
            matched_movie_ids = [str(item["id"]) for item in matches]
            if matched_movie_ids:
                category_id = category_map.get(cat_name.lower())
                if category_id:
                    payload = {
                        "action": "edit",
                        "category_id": category_id,
                        "list": ",".join(matched_movie_ids) + ",",
                    }
                    try:
                        res = session.post(
                            f"{BASE_URL}/category_item", data=payload, timeout=15
                        )
                        res.raise_for_status()
                        print(
                            f"✅ Category '{cat_name}' (ID: {category_id}) updated with {len(matched_movie_ids)} movies"
                        )
                    except requests.RequestException as e:
                        print(f"❌ Failed to update category ID {category_id}: {e}")
                else:
                    print(f"⚠️ Category ID for '{cat_name}' not found.")
            else:
                print(f"⚠️ No matched movies for '{cat_name}'.")

    except Exception as e:
        print(f"❌ Error: {e}")
