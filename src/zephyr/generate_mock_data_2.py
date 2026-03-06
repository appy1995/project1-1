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
# GENERATE ARTISTS
# ------------------------

artists: list[dict[str, Any]] = []

for _i in range(1, NUM_ARTISTS + 1):
    artists.append(
        {
            "artist_name": fake.name(),
            "country": fake.country(),
            "debut_year": random.randint(1990, 2023),
        }
    )

artists_df = pd.DataFrame(artists)

# ------------------------
# GENERATE MASTER SONG CATALOG
# ------------------------

songs: list[dict[str, Any]] = []

for idx, _artist in artists_df.iterrows():
    for _ in range(NUM_SONGS_PER_ARTIST):
        songs.append(
            {
                "title": fake.sentence(nb_words=3).replace(".", ""),
                "artist_index": idx,  # used later to map to artist_id
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
    artists_df: pd.DataFrame,
) -> None:
    fake.unique.clear()

    # ------------------------
    # CREATE PLATFORM ARTIST IDS
    # ------------------------
    artists_platform = artists_df.copy().reset_index(drop=True)
    artists_platform["artist_id"] = [
        f"{prefix}_A{i + 1:04d}" for i in range(len(artists_platform))
    ]

    artists_platform = artists_platform[
        ["artist_id", "artist_name", "country", "debut_year"]
    ]

    # ------------------------
    # SONGS
    # ------------------------
    songs_df = master_songs_df.copy().reset_index(drop=True)

    songs_df["song_id"] = [f"{prefix}{i + 1:04d}" for i in range(len(songs_df))]

    songs_df["artist_id"] = artists_platform.loc[
        songs_df["artist_index"], "artist_id"
    ].to_numpy()

    songs_df = songs_df[
        ["song_id", "title", "artist_id", "genre", "duration", "release_date"]
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

    artists_platform.to_csv(
        os.path.join(base_folder, f"{platform_name}_artists.csv"), index=False
    )

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
    generate_platform_data(platform_name, prefix, master_songs_df, artists_df)
