
"""
Desktop Gym Pet - Complete MVP

Features:
1. Desktop virtual pet window.
2. Start / Pause / Reset timer.
3. Uses two squat sprite images as animation frames.
4. Every 2 seconds = 1 squat rep.
5. Lower-body reps increase from squat.
6. Character physique level increases every 100 lower reps.
7. Saves progress into data/pet_state.json.
8. Always-on-top small desktop pet window.

Required files:
- Squat starting_pgrm.png
- squat ending_pgrm.png

Put this Python file in the same folder as those two images, or edit SPRITE_START
and SPRITE_END below to match your file locations.

Install dependency:
    pip install pillow

Run:
    python desktop_gym_pet.py
"""

from __future__ import annotations

import json
import time
import tkinter as tk
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from PIL import Image, ImageTk


# =========================
# App Settings
# =========================

APP_TITLE = "Desktop Gym Pet"
WINDOW_WIDTH = 360
WINDOW_HEIGHT = 460

REP_INTERVAL_SECONDS = 2
REPS_PER_LEVEL = 100

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SAVE_FILE = DATA_DIR / "pet_state.json"

# Change these if your image names are different.
SPRITE_START = BASE_DIR / "Squat starting_pgrm.png"
SPRITE_END = BASE_DIR / "squat ending_pgrm.png"


# =========================
# Data Model
# =========================

@dataclass
class PetState:
    total_seconds: int = 0

    upper_reps: int = 0
    lower_reps: int = 0

    upper_level: int = 1
    lower_level: int = 1

    def update_levels(self) -> None:
        self.upper_level = max(1, self.upper_reps // REPS_PER_LEVEL + 1)
        self.lower_level = max(1, self.lower_reps // REPS_PER_LEVEL + 1)


def load_state() -> PetState:
    if not SAVE_FILE.exists():
        return PetState()

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return PetState(**data)
    except (json.JSONDecodeError, TypeError):
        return PetState()


def save_state(state: PetState) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with open(SAVE_FILE, "w", encoding="utf-8") as file:
        json.dump(asdict(state), file, indent=4)


# =========================
# Main App
# =========================

class DesktopGymPet:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        # Makes it feel like a desktop pet.
        self.root.attributes("-topmost", True)

        self.state = load_state()

        self.running = False
        self.last_tick_time: Optional[float] = None
        self.last_rep_time: Optional[float] = None

        self.animation_index = 0
        self.animation_frames: list[ImageTk.PhotoImage] = []

        self.build_ui()
        self.load_sprites()
        self.refresh_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # =========================
    # UI
    # =========================

    def build_ui(self) -> None:
        self.title_label = tk.Label(
            self.root,
            text="Desktop Gym Pet",
            font=("Arial", 18, "bold")
        )
        self.title_label.pack(pady=10)

        self.pet_label = tk.Label(self.root)
        self.pet_label.pack(pady=10)

        self.timer_label = tk.Label(
            self.root,
            text="Time: 00:00:00",
            font=("Arial", 14)
        )
        self.timer_label.pack(pady=4)

        self.rep_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 12),
            justify="left"
        )
        self.rep_label.pack(pady=8)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(
            button_frame,
            text="Start",
            width=8,
            command=self.start
        )
        self.start_button.grid(row=0, column=0, padx=4)

        self.pause_button = tk.Button(
            button_frame,
            text="Pause",
            width=8,
            command=self.pause
        )
        self.pause_button.grid(row=0, column=1, padx=4)

        self.reset_button = tk.Button(
            button_frame,
            text="Reset",
            width=8,
            command=self.reset
        )
        self.reset_button.grid(row=0, column=2, padx=4)

        self.info_label = tk.Label(
            self.root,
            text="Current exercise: Squat\nEvery 2 seconds = 1 lower-body rep",
            font=("Arial", 9),
            justify="center"
        )
        self.info_label.pack(pady=8)

    # =========================
    # Sprite / Animation
    # =========================

    def load_sprites(self) -> None:
        self.animation_frames.clear()

        for path in [SPRITE_START, SPRITE_END]:
            if not path.exists():
                raise FileNotFoundError(
                    f"Cannot find sprite image: {path}\n"
                    "Make sure the image is in the same folder as this Python file."
                )

            image = Image.open(path).convert("RGBA")

            # Resize while keeping the image ratio.
            image.thumbnail((260, 220), Image.LANCZOS)

            # Optional: make black background transparent.
            # Your current images have a black background, so this helps them look cleaner.
            image = self.make_black_transparent(image)

            self.animation_frames.append(ImageTk.PhotoImage(image))

    def make_black_transparent(self, image: Image.Image) -> Image.Image:
        """
        Converts near-black pixels to transparent.

        This is useful because your current sprite images have a black background.
        If you want to keep the black background, return image directly instead.
        """
        image = image.convert("RGBA")
        pixels = image.getdata()

        new_pixels = []
        for red, green, blue, alpha in pixels:
            if red < 25 and green < 25 and blue < 25:
                new_pixels.append((red, green, blue, 0))
            else:
                new_pixels.append((red, green, blue, alpha))

        image.putdata(new_pixels)
        return image

    def update_sprite(self) -> None:
        if not self.animation_frames:
            return

        frame = self.animation_frames[self.animation_index]
        self.pet_label.config(image=frame)
        self.pet_label.image = frame

    # =========================
    # Timer Logic
    # =========================

    def start(self) -> None:
        if self.running:
            return

        self.running = True
        now = time.time()
        self.last_tick_time = now
        self.last_rep_time = now
        self.tick()

    def pause(self) -> None:
        self.running = False
        save_state(self.state)
        self.refresh_ui()

    def reset(self) -> None:
        self.running = False
        self.state = PetState()
        save_state(self.state)
        self.animation_index = 0
        self.refresh_ui()

    def tick(self) -> None:
        if not self.running:
            return

        now = time.time()

        if self.last_tick_time is not None:
            elapsed_seconds = int(now - self.last_tick_time)
            if elapsed_seconds > 0:
                self.state.total_seconds += elapsed_seconds
                self.last_tick_time = now

        if self.last_rep_time is not None:
            if now - self.last_rep_time >= REP_INTERVAL_SECONDS:
                self.complete_squat_rep()
                self.last_rep_time = now

        # Animation speed: switch frame every 300 ms.
        self.animation_index = 1 - self.animation_index

        self.refresh_ui()
        self.root.after(300, self.tick)

    def complete_squat_rep(self) -> None:
        self.state.lower_reps += 1
        self.state.update_levels()
        save_state(self.state)

    # =========================
    # Display
    # =========================

    def refresh_ui(self) -> None:
        hours = self.state.total_seconds // 3600
        minutes = (self.state.total_seconds % 3600) // 60
        seconds = self.state.total_seconds % 60

        self.timer_label.config(
            text=f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

        next_lower = REPS_PER_LEVEL - (self.state.lower_reps % REPS_PER_LEVEL)
        next_upper = REPS_PER_LEVEL - (self.state.upper_reps % REPS_PER_LEVEL)

        self.rep_label.config(
            text=(
                f"Lower reps: {self.state.lower_reps}\n"
                f"Lower physique level: {self.state.lower_level}\n"
                f"Next lower boost: {next_lower} reps\n\n"
                f"Upper reps: {self.state.upper_reps}\n"
                f"Upper physique level: {self.state.upper_level}\n"
                f"Next upper boost: {next_upper} reps"
            )
        )

        self.update_sprite()

    def close(self) -> None:
        save_state(self.state)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    app = DesktopGymPet()
    app.run()
