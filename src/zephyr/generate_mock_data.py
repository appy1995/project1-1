import argparse
import json
import logging
import os
import random
from datetime import datetime
from typing import Any, Dict, Hashable, List, Sequence
from uuid import uuid4

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()
logging.basicConfig(level=logging.INFO)

# ------------------------
# DEFAULT CONFIG
# ------------------------
NUM_CONCERTS = 10
NUM_MERCH = 50
NUM_NEW_ARTISTS_PER_INGEST = 3
NUM_NEW_SONGS_PER_ARTIST = 2
NUM_NEW_VENUES = 10
NUM_NEW_USERS_MASTER = 20  # new master users per ingest

sources = ["Spotify", "YouTube", "Festival"]
genres = ["Pop", "Rock", "Hip-Hop", "EDM", "Jazz", "Classical"]
merch_items = ["T-Shirt", "Hoodie", "Cap", "Poster", "Vinyl"]
STATE_FILE = "persistent_state_mock_data.json"

# ------------------------
# ARGUMENT PARSER
# ------------------------
parser = argparse.ArgumentParser(description="Generate mock music/festival data")
parser.add_argument(
    "-m",
    "--mode",
    type=str,
    default="normal",
    choices=["normal", "new_artists_only", "old_artists_only"],
    help="Mode of data generation",
)
parser.add_argument(
    "-n",
    "--num_streams",
    type=int,
    default=150,
    help="Number of streams per platform per ingest",
)
parser.add_argument(
    "-u",
    "--new_users",
    type=int,
    default=10,
    help="Number of new platform-specific users per platform",
)
args = parser.parse_args()

mode = args.mode
NUM_STREAMS = args.num_streams
NUM_NEW_USERS_PER_INGEST = args.new_users
logging.info(
    "Mode: %s, streams per platform: %s, new users per platform: %s",
    mode,
    NUM_STREAMS,
    NUM_NEW_USERS_PER_INGEST,
)

# ------------------------
# LOAD PERSISTENT STATE
# ------------------------
state: Dict[str, Any] = {}

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

for key in [
    "Spotify_users",
    "YouTube_users",
    "Festival_users",
    "Artists_pool",
    "Songs_pool",
    "Venues_pool",
    "Master_users",
]:
    if key not in state:
        state[key] = []

# ------------------------
# HELPER FUNCTIONS
# ------------------------


# --- USERS ---
def generate_master_users(num_users: int) -> List[Dict[str, Any]]:
    new_users: List[Dict[str, Any]] = []
    for _ in range(num_users):
        dob = fake.date_of_birth(minimum_age=18, maximum_age=65)
        email = fake.unique.email()
        phone = fake.phone_number() if random.random() < 0.5 else None
        new_users.append(
            {
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "date_of_birth": dob.strftime("%Y-%m-%d"),
                "country": fake.country(),
                "email": email,
                "phone": phone,
            }
        )
    return new_users


def assign_platforms(
    master_users: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    platform_users: Dict[str, List[Dict[str, Any]]] = {
        "Spotify": [],
        "YouTube": [],
        "Festival": [],
    }
    for user in master_users:
        num_platforms = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
        platforms = random.sample(["Spotify", "YouTube", "Festival"], num_platforms)
        for platform in platforms:
            platform_id = f"{uuid4().hex}"
            extra_attr: Dict[str, Any] = {}
            if platform == "Spotify":
                extra_attr["username"] = fake.user_name()
            elif platform == "YouTube":
                extra_attr["region"] = fake.state()
            elif platform == "Festival":
                extra_attr["city"] = fake.city()
            platform_users[platform].append(
                {
                    "user_id": platform_id,
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "date_of_birth": user["date_of_birth"],
                    "country": user["country"],
                    "email": user["email"],
                    "phone": user["phone"],
                    **extra_attr,
                }
            )
    return platform_users


# --- ARTISTS & SONGS ---
def generate_new_artists(num_artists: int) -> List[str]:
    return [fake.name() for _ in range(num_artists)]


def generate_songs_for_artist(artist: str, num_songs: int) -> List[Dict[str, Any]]:
    songs: List[Dict[str, Any]] = []
    for _ in range(num_songs):
        title = fake.sentence(nb_words=3).replace(".", "")
        release_date = fake.date_between(start_date="-5y", end_date="today")
        songs.append(
            {
                "title": title,
                "artist": artist,
                "genre": random.choice(genres),
                "duration": random.randint(120, 360),
                "release_date": release_date.strftime("%Y-%m-%d"),
            }
        )
    return songs


def generate_songs_for_platform(
    source: str, songs_pool: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    songs: List[Dict[str, Any]] = []
    for song in songs_pool:
        song_id = f"{uuid4().hex}"
        duration_val = song["duration"]
        # if source == "YouTube":
        #     duration_val = f"{duration_val // 60}:{duration_val % 60:02d}"
        genre_val = song["genre"] if source != "Festival" else None
        songs.append(
            {
                "song_id": song_id,
                "title": song["title"],
                "artist": song["artist"],
                "genre": genre_val,
                "duration": duration_val,
                "release_date": song["release_date"],
                "platform": source,
            }
        )
    return songs


# --- STREAMS ---
def generate_streams(
    users_df: pd.DataFrame, songs_df: pd.DataFrame, num_streams: int
) -> pd.DataFrame:
    streams: List[Dict[str, Any]] = []
    num_songs = len(songs_df)
    if num_songs == 0:
        return pd.DataFrame()
    base_weights = np.linspace(1, num_songs, num=num_songs)
    base_weights /= base_weights.sum()
    for _ in range(num_streams):
        user = users_df.sample(1).iloc[0]
        random_factor = np.random.uniform(0.5, 1.5, size=num_songs)
        weights = base_weights * random_factor
        weights /= weights.sum()
        song = songs_df.sample(1, weights=weights).iloc[0]
        timestamp = fake.date_time_between(start_date="-30d", end_date="now")
        duration_listened = (
            random.randint(5, song["duration"])
            if song["platform"] != "festival"
            else None
        )
        streams.append(
            {
                "stream_id": f"{uuid4().hex}",
                "user_id": user["user_id"],
                "song_id": song["song_id"],
                "platform": song["platform"],
                "timestamp": timestamp,
                "duration_listened": duration_listened,
            }
        )
    return pd.DataFrame(streams)


# --- FESTIVAL ---
def generate_venues(num_venues: int) -> List[Dict[str, Any]]:
    venues: List[Dict[str, Any]] = []
    start_id = len(state["Venues_pool"]) + 1
    for i in range(num_venues):
        venues.append(
            {
                "venue_id": f"V{start_id + i}",
                "name": f"{fake.company()} Arena",
                "city": fake.city(),
                "country": fake.country(),
                "capacity": random.randint(10, 100),
            }
        )
    return venues


def generate_concerts(venues_pool: List[Dict[str, Any]]) -> pd.DataFrame:
    concerts: List[Dict[str, Any]] = []
    if not state["Artists_pool"] or not venues_pool:
        return pd.DataFrame()
    for i in range(NUM_CONCERTS):
        artist = random.choice(state["Artists_pool"])
        venue = random.choice(venues_pool)
        date = fake.date_between(start_date="-2y", end_date="today")
        attendance = random.randint(10, venue["capacity"])
        concerts.append(
            {
                "concert_id": f"C{i + 1}",
                "artist": artist,
                "venue_id": venue["venue_id"],
                "venue_name": venue["name"],
                "date": date,
                "attendance": attendance,
            }
        )
    return pd.DataFrame(concerts)


def generate_festival_attendees(
    concerts_df: pd.DataFrame,
    existing_users: Sequence[dict[Hashable, Any]],
) -> pd.DataFrame:
    attendees_rows: list[dict[str, Any]] = []
    user_pool: list[dict[str, Any]] = [
        {str(k): v for k, v in user.items()} for user in existing_users
    ]

    for _, concert in concerts_df.iterrows():
        attendance = int(concert["attendance"])

        while len(user_pool) < attendance:
            user_pool.append(
                {
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "date_of_birth": fake.date_of_birth(
                        minimum_age=18,
                        maximum_age=65,
                    ).strftime("%Y-%m-%d"),
                    "country": fake.country(),
                    "email": fake.unique.email(),
                    "phone": fake.phone_number() if random.random() < 0.5 else None,
                    "city": fake.city(),
                }
            )

        for user in random.sample(user_pool, attendance):
            attendee = user.copy()
            attendee["concert_id"] = concert["concert_id"]
            attendee["venue_id"] = concert["venue_id"]
            attendee["venue_name"] = concert["venue_name"]
            attendees_rows.append(attendee)

    return pd.DataFrame(attendees_rows)


def generate_merch(concerts_df: pd.DataFrame) -> pd.DataFrame:
    merch: List[Dict[str, Any]] = []
    currencies = ["USD", "EUR", "GBP"]
    for _ in range(NUM_MERCH):
        if concerts_df.empty:
            continue
        concert = concerts_df.sample(1).iloc[0]
        start_date = concert["date"]
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        merch.append(
            {
                "sale_id": f"{uuid4().hex}",
                "artist": concert["artist"],
                "item_name": random.choice(merch_items),
                "quantity": random.randint(1, 50),
                "price": round(random.uniform(10, 100), 2),
                "currency": random.choice(currencies),
                "concert_id": concert["concert_id"],
                "timestamp": fake.date_time_between(
                    start_date=start_date, end_date="now"
                ),
            }
        )
    return pd.DataFrame(merch)


# ------------------------
# ADD NEW ARTISTS IF MODE ALLOWS
# ------------------------
new_artists: List[str] = []
if mode in ["normal", "new_artists_only"]:
    new_artists = generate_new_artists(NUM_NEW_ARTISTS_PER_INGEST)
    state["Artists_pool"].extend(new_artists)
    for artist in new_artists:
        state["Songs_pool"].extend(
            generate_songs_for_artist(artist, NUM_NEW_SONGS_PER_ARTIST)
        )

# ------------------------
# DETERMINE SONGS POOL BASED ON MODE
# ------------------------
if mode == "new_artists_only":
    songs_pool = [s for s in state["Songs_pool"] if s["artist"] in new_artists]
elif mode == "old_artists_only":
    songs_pool = [s for s in state["Songs_pool"] if s["artist"] not in new_artists]
else:
    songs_pool = state["Songs_pool"]

# ------------------------
# GENERATE MASTER USERS AND ASSIGN PLATFORMS
# ------------------------
new_master_users = generate_master_users(NUM_NEW_USERS_MASTER)
state["Master_users"].extend(new_master_users)
platform_users = assign_platforms(state["Master_users"])

# ------------------------
# GENERATE & SAVE DATA
# ------------------------
ingest_date = datetime.today().strftime("%Y-%m-%d")
timestamp = datetime.now().strftime("%H%M%S")
base_folder = os.path.join("data", "raw", f"ingest={ingest_date}_{timestamp}")
os.makedirs(base_folder, exist_ok=True)

for source in sources:
    users_df = pd.DataFrame(platform_users[source])
    state[f"{source}_users"].extend(platform_users[source])
    folder = os.path.join(base_folder, source.lower())
    os.makedirs(folder, exist_ok=True)

    if source == "Festival":
        if not state["Venues_pool"]:
            state["Venues_pool"].extend(generate_venues(NUM_NEW_VENUES))
        venues_df = pd.DataFrame(state["Venues_pool"])
        venues_df.to_csv(os.path.join(folder, "festival_venues.csv"), index=False)

        if not state["Artists_pool"]:
            new_artists = generate_new_artists(NUM_NEW_ARTISTS_PER_INGEST)
            state["Artists_pool"].extend(new_artists)
            for artist in new_artists:
                state["Songs_pool"].extend(
                    generate_songs_for_artist(artist, NUM_NEW_SONGS_PER_ARTIST)
                )

        concerts_df = generate_concerts(state["Venues_pool"])
        if not concerts_df.empty:
            concerts_df["date"] = concerts_df["date"].astype(str)
        concerts_df.to_csv(os.path.join(folder, "festival_concerts.csv"), index=False)

        attendees_df = generate_festival_attendees(
            concerts_df,
            users_df.to_dict("records"),  # pyright: ignore[reportUnknownMemberType]
        )
        if "user_id" in attendees_df.columns:
            attendees_df = attendees_df.drop(columns=["user_id"])
        attendees_df.to_csv(os.path.join(folder, "festival_attendees.csv"), index=False)

        merch_df = generate_merch(concerts_df)
        merch_df.to_csv(os.path.join(folder, "festival_merch.csv"), index=False)
    else:
        users_df.to_csv(
            os.path.join(folder, f"{source.lower()}_users.csv"), index=False
        )
        songs_df = pd.DataFrame(generate_songs_for_platform(source, songs_pool))
        streams_df = generate_streams(users_df, songs_df, NUM_STREAMS)
        songs_df.to_csv(
            os.path.join(folder, f"{source.lower()}_songs.csv"), index=False
        )
        streams_df.to_csv(
            os.path.join(folder, f"{source.lower()}_streams.csv"), index=False
        )

# ------------------------
# SAVE PERSISTENT STATE
# ------------------------
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

# ------------------------
# SAVE METADATA
# ------------------------
metadata: Dict[str, Any] = {
    "ingest_date": ingest_date,
    "mode": mode,
    "num_streams_per_platform": NUM_STREAMS,
    "num_new_users_per_platform": NUM_NEW_USERS_PER_INGEST,
    "num_new_master_users": NUM_NEW_USERS_MASTER,
    "num_new_artists_added": len(new_artists),
    "total_users": {src: len(state[f"{src}_users"]) for src in sources},
    "total_master_users": len(state["Master_users"]),
    "total_artists": len(state["Artists_pool"]),
    "total_songs": len(state["Songs_pool"]),
    "total_venues": len(state["Venues_pool"]),
}

with open(os.path.join(base_folder, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=4)

logging.info("Mock data generated in folder: %s", base_folder)
logging.info("Metadata saved: %s", metadata)
