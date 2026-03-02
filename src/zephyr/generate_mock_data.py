import os
import random
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()

# ------------------------
# CONFIG
# ------------------------
PLATFORMS = {"spotify": "S", "youtube": "Y", "deezer": "D"}

NUM_ARTISTS = 10
NUM_SONGS_PER_ARTIST = 5
NUM_USERS = 100
NUM_STREAMS = 10000

GENRES = ["Pop", "Rock", "Hip-Hop", "EDM", "Jazz", "Classical"]

# ------------------------
# GENERATE MASTER SONG CATALOG (NO IDS)
# ------------------------


artists = [fake.name() for _ in range(NUM_ARTISTS)]

songs: list[dict[str, Any]] = []

for artist in artists:
    for _ in range(NUM_SONGS_PER_ARTIST):
        songs.append(
            {
                "title": fake.sentence(nb_words=3).replace(".", ""),
                "artist": artist,
                "genre": random.choice(GENRES),
                "duration": random.randint(120, 360),
                "release_date": fake.date_between("-5y", "today").strftime("%Y-%m-%d"),
            }
        )

master_songs_df = pd.DataFrame(songs)


# ------------------------
# FUNCTION PER PLATFORM
# ------------------------


def generate_platform_data(
    platform_name: str,
    prefix: str,
    master_songs_df: pd.DataFrame,
) -> None:
    fake.unique.clear()

    # ------------------------
    # CREATE PLATFORM-SPECIFIC SONG IDS
    # ------------------------
    songs_df = master_songs_df.copy().reset_index(drop=True)
    songs_df["song_id"] = [f"{prefix}{i + 1:04d}" for i in range(len(songs_df))]

    songs_df = songs_df[
        ["song_id", "title", "artist", "genre", "duration", "release_date"]
    ]

    # ------------------------
    # USERS
    # ------------------------
    users: list[dict[str, Any]] = []

    for i in range(1, NUM_USERS + 1):
        users.append(
            {
                "user_id": f"{prefix}_U{i:04d}",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.unique.email(),
                "country": fake.country(),
                "date_of_birth": fake.date_of_birth(
                    minimum_age=18, maximum_age=65
                ).strftime("%Y-%m-%d"),
            }
        )

    users_df = pd.DataFrame(users)

    # ------------------------
    # STREAMS
    # ------------------------
    weights = np.linspace(1, len(songs_df), len(songs_df))
    weights /= weights.sum()

    streams: list[dict[str, Any]] = []

    for i in range(1, NUM_STREAMS + 1):
        user = users_df.sample(1).iloc[0]
        song = songs_df.sample(1, weights=weights).iloc[0]

        streams.append(
            {
                "stream_id": f"{prefix}_STR{i:05d}",
                "user_id": user["user_id"],
                "song_id": song["song_id"],
                "timestamp": fake.date_time_between("-30d", "now"),
                "duration_listened": random.randint(5, song["duration"]),
            }
        )

    streams_df = pd.DataFrame(streams)

    # ------------------------
    # SAVE RAW FILES
    # ------------------------
    base_folder = os.path.join("data", "raw", platform_name)
    os.makedirs(base_folder, exist_ok=True)

    users_df.to_csv(
        os.path.join(base_folder, f"{platform_name}_users.csv"), index=False
    )
    songs_df.to_csv(
        os.path.join(base_folder, f"{platform_name}_songs.csv"), index=False
    )
    streams_df.to_csv(
        os.path.join(base_folder, f"{platform_name}_streams.csv"), index=False
    )


# ------------------------
# RUN FOR ALL PLATFORMS
# ------------------------
for platform_name, prefix in PLATFORMS.items():
    generate_platform_data(platform_name, prefix, master_songs_df)
