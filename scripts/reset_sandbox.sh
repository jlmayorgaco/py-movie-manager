#!/bin/bash

# Root sandbox directory
SANDBOX="__sandbox__"

echo "🧹 Cleaning old sandbox..."
rm -rf "$SANDBOX"
mkdir -p "$SANDBOX/__RAW__"
mkdir -p "$SANDBOX/__VOSE__"

echo "🎬 Creating test movie directories..."

# Define a helper function
create_movie_folder() {
  DIR=$1
  shift
  mkdir -p "$DIR"
  for MOVIE in "$@"; do
    touch "$DIR/$MOVIE"
  done
}

# === RAW FOLDERS (Full versions) ===

create_movie_folder "$SANDBOX/__RAW__/[g-action][d-john-doe] Terminator Collection" \
  "Terminator 1 (1984).mkv" \
  "Terminator 2 (1991).mp4" \
  "Terminator 3 (2003).avi"

create_movie_folder "$SANDBOX/__RAW__/[g-action][d-kate-stone] Bullet Rush" \
  "Rush Hour Zero (2010).mp4"

create_movie_folder "$SANDBOX/__RAW__/[g-comedy][d-amy-smith] The Funny Pack" \
  "Joke Parade (2001).mkv" \
  "Laugh Out Loud (2003).mp4"

create_movie_folder "$SANDBOX/__RAW__/[g-comedy][d-tom-hardy] Banana Split" \
  "Fruit Fiasco (2022).avi"

create_movie_folder "$SANDBOX/__RAW__/[g-drama][d-mike-lee] Emotional Ride" \
  "Cry Again (2010).avi" \
  "Heartbreak Hotel (2012).mkv"

create_movie_folder "$SANDBOX/__RAW__/[g-drama][d-sarah-cho] Life in Motion" \
  "Slow Steps (2018).mp4"

create_movie_folder "$SANDBOX/__RAW__/[g-documentary][d-jane-roberts] Nature's Truth" \
  "Planet Wild (2020).mp4"

create_movie_folder "$SANDBOX/__RAW__/[g-documentary][d-ben-huang] AI: The Mirror" \
  "Code and Soul (2023).mkv"

create_movie_folder "$SANDBOX/__RAW__/[g-horror][d-jack-blake] Haunted Tales" \
  "Midnight Screams (2008).mkv" \
  "Bloody Basement (2009).avi"

create_movie_folder "$SANDBOX/__RAW__/[g-horror][d-helen-crow] Evil Roots" \
  "The Basement (2005).avi"

create_movie_folder "$SANDBOX/__RAW__/[g-romance][d-linda-tan] Love Happens" \
  "Kiss in Paris (2015).mp4"

create_movie_folder "$SANDBOX/__RAW__/[g-romance][d-mark-leon] Summer Heart" \
  "Sunset Boulevard (2017).mp4"

# === VOSE FOLDERS (Partial copies) ===

create_movie_folder "$SANDBOX/__VOSE__/[g-action][d-john-doe] Terminator Collection" \
  "Terminator 1 (1984).mkv"

create_movie_folder "$SANDBOX/__VOSE__/[g-comedy][d-amy-smith] The Funny Pack" \
  "Joke Parade (2001).mkv"

create_movie_folder "$SANDBOX/__VOSE__/[g-drama][d-mike-lee] Emotional Ride" \
  "Cry Again (2010).avi"

create_movie_folder "$SANDBOX/__VOSE__/[g-documentary][d-jane-roberts] Nature's Truth" \
  "Planet Wild (2020).mp4"

create_movie_folder "$SANDBOX/__VOSE__/[g-horror][d-jack-blake] Haunted Tales" \
  "Midnight Screams (2008).mkv"

create_movie_folder "$SANDBOX/__VOSE__/[g-romance][d-linda-tan] Love Happens" \
  "Kiss in Paris (2015).mp4"

echo "✅ Sandbox reset and populated!"
