import os
import json
import logging
from PIL import Image, ImageDraw, ImageFont
import numpy as np

logging.basicConfig(
    filename="debug.log", level=logging.DEBUG, format="%(levelname)s - %(message)s"
)

def sanitize_filename(char) -> str:
    return char if char.isalnum() else f"char_{ord(char)}"

def ttf_to_font(ttf_path, font_size=128) -> dict:
    font = ImageFont.truetype(ttf_path, font_size)
    font_data = {}

    for char_code in range(32, 0x0250):
        char = chr(char_code)
        try:
            bbox = font.getbbox(char)
            width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            image = Image.new("L", (width, height), 0)
            draw = ImageDraw.Draw(image)
            draw.text((0, 0), char, 255, font=font)
            pixels = np.array(image)

            char_data = [width]
            visited = np.zeros((height, width), dtype=bool)
            for y in range(height):
                for x in range(width):
                    if pixels[y, x] > 0 and not visited[y, x]:
                        block_width = 1
                        block_height = 1
                        while x + block_width < width and np.all(pixels[y:y + block_height, x + block_width] > 0):
                            block_width += 1
                        while y + block_height < height and np.all(pixels[y + block_height, x:x + block_width] > 0):
                            block_height += 1
                        visited[y:y + block_height, x:x + block_width] = True
                        rotation = 0  # Default rotation value
                        char_data.append([x, y, block_width, block_height, rotation])
            font_data[char_code] = char_data
        except Exception as e:
            logging.warning(f"Failed to process character '{char}' (ASCII {char_code}): {e}")

    return font_data

def hex_to_rgb(hex) -> list:
    hex = hex.lstrip("#")
    return [int(hex[i:i + 2], 16) / 256 for i in (0, 2, 4)]

def gen_text(text, color, x, y, time, duration, scale, time_offset, depth, track, centered, font) -> list:
    color = hex_to_rgb(color)
    walls = []

    if centered:
        length = sum(font[ord(char)][0] for char in text if ord(char) in font)
        x -= length * scale / 2

    for char in text:
        if ord(char) in font:
            ch = font[ord(char)]
        else:
            logging.debug(f"Skipping unsupported or missing character: '{char}'")
            continue

        spacing = ch[0]
        for line in ch[1:]:
            obstacle = {
                "b": time,
                "x": x + line[0] * scale,
                "y": y - line[1] * scale - (line[3] * scale),
                "d": duration,
                "w": line[2] * scale,
                "h": line[3] * scale,
                "customData": {
                    "uninteractable": True,
                    "color": color,
                    "coordinates": [
                        x + line[0] * scale,
                        y - line[1] * scale - (line[3] * scale),
                    ],
                    "size": [line[2] * scale, line[3] * scale, depth],
                    "track": track,
                    "localRotation": [0, 0, line[4]]  # Add rotation data
                },
            }
            walls.append(obstacle)

        x += spacing * scale
        time += time_offset

    logging.debug(f"Generated {len(walls)} walls for text: '{text}'")
    return walls

def gen_text_geo(text, color, x, y, z, scale, depth, track, centered, font, **kwargs) -> list:
    color = hex_to_rgb(color)
    walls = []

    if centered:
        length = sum(font[ord(char)][0] for char in text if ord(char) in font)
        x -= length * scale / 2

    for char in text:
        if ord(char) in font:
            ch = font[ord(char)]
        else:
            logging.debug(f"Skipping unsupported or missing character: '{char}'")
            continue

        spacing = ch[0]
        for line in ch[1:]:
            obstacle = {
                "geometry": {
                    "type": "Cube",
                    "material": {"color": [1, 0, 0, 1], "shader": "OpaqueLight"},
                },
                "position": [
                    x + line[0] * scale,
                    y - line[1] * scale - (line[3] * scale),
                    z,
                ],
                "scale": [line[2] * scale, line[3] * scale, depth],
                "track": track,
                "rotation": [0, 0, line[4]]  # Add rotation data
            }
            obstacle.update(kwargs)
            walls.append(obstacle)

        x += spacing * scale

    logging.debug(f"Generated {len(walls)} geometric objects for text: '{text}'")
    return walls

def parse_lrc(file_path) -> tuple:
    lyrics = []
    tags = {}
    offset = 0
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("["):
                if ":" in line and not "<" in line:
                    tag, value = line[1:].split(":", 1)
                    if tag in ["ti", "ar", "al", "by", "au", "length", "offset", "re", "ve", "tool", "#"]:
                        tags[tag] = value.strip(" ]\n")
                        if tag == "offset":
                            try:
                                offset = float(tags["offset"]) / 1000
                            except ValueError:
                                logging.warning(f"Invalid offset value: {tags['offset']}. Using 0.")
                else:
                    parts = line.split("]")
                    time_str = parts[0][1:]
                    words = parts[1].strip().split("<")
                    for word in words:
                        if ">" in word:
                            time_word, text = word.split(">", 1)
                            try:
                                minutes, seconds = map(float, time_word.split(":"))
                                time = minutes * 60 + seconds + offset
                                lyrics.append((time, text.strip()))
                            except ValueError:
                                logging.warning(f"Invalid time format: {time_word}. Skipping word: {word}")
    return tags, lyrics

def create_text_from_lrc(lrc_file, color, x, y, z, scale, depth, track, centered, font, geo=False) -> list:
    tags, lyrics = parse_lrc(lrc_file)
    bpm = 160
    beat_duration = 60 / bpm
    walls = []

    for i, (time, text) in enumerate(lyrics):
        beat_time = time / beat_duration
        duration_seconds = (lyrics[i + 1][0] - time) if i < len(lyrics) - 1 else 10
        duration_beats = duration_seconds / beat_duration

        if geo:
            walls.extend(gen_text_geo(text, color, x, y, z, scale, depth, track, centered, font))
        else:
            walls.extend(gen_text(text, color, x, y, beat_time, duration_beats, scale, 0.001, depth, track, centered, font))

    return walls

class Difficulty:
    def new_bpm_event(self, bpm, time):
        self.bpmEvents.append({"b": time, "m": bpm})

    def new_rotation_event(self, beat, time, magnitude):
        self.rotationEvents.append({"b": time, "e": beat, "r": magnitude})

    def new_color_note(self, b, x, y, c, d, a, customData={}):
        self.colorNotes.append({"b": b, "x": x, "y": y, "c": c, "d": d, "a": a, "customData": customData})

    def new_bomb(self, b, x, y, customData={}):
        self.bombNotes.append({"b": b, "x": x, "y": y, "customData": customData})

    def new_obstacle(self, b, d, x, y, w, h, customData={}):
        self.obstacles.append({"b": b, "d": d, "x": x, "y": y, "w": w, "h": h, "customData": customData})

    def new_slider(self, c, b, x, y, d, mu, tb, tx, ty, tc, tmu, m, customData={}):
        self.sliders.append({"c": c, "b": b, "x": x, "y": y, "d": d, "mu": mu, "tb": tb, "tx": tx, "ty": ty, "tc": tc, "tmu": tmu, "m": m, "customData": customData})

    def new_burst_slider(self, c, b, x, y, d, mu, tb, tx, ty, sc, s, customData={}):
        self.burstSliders.append({"c": c, "b": b, "x": x, "y": y, "d": d, "mu": mu, "tb": tb, "tx": tx, "ty": ty, "sc": sc, "s": s, "customData": customData})

    def new_event(self, b, et, i, f, customData={}):
        self.basicBeatmapEvents.append({"b": b, "type": et, "value": i, "f": f, "customData": customData})

    def new_color_boost_event(self, b, o):
        self.colorBoostBeatmapEvents.append({"b": b, "o": o})

    def __init__(self, diffname, diffpath, suggestions, requirements):
        self.diffname = diffname
        self.diffpath = diffpath
        self.suggestions = suggestions
        self.requirements = requirements

        self.bpmEvents = []
        self.rotationEvents = []
        self.colorNotes = []
        self.bombNotes = []
        self.obstacles = []
        self.sliders = []
        self.burstSliders = []
        self.basicBeatmapEvents = []
        self.colorBoostBeatmapEvents = []
        self.waypoints = []
        self.basicEventTypesWithKeywords = {}
        self.lightColorEventBoxGroups = []
        self.lightRotationEventBoxGroups = []
        self.lightTranslationEventBoxGroups = []
        self.useNormalEventsAsCompatibleEvents = False
        self.customData = {}

        with open(diffpath, "r") as f:
            map_data = json.load(f)

        self.bpmEvents = map_data.get("bpmEvents", self.bpmEvents)
        self.rotationEvents = map_data.get("rotationEvents", self.rotationEvents)
        self.colorNotes = map_data.get("colorNotes", self.colorNotes)
        self.bombNotes = map_data.get("bombNotes", self.bombNotes)
        self.obstacles = map_data.get("obstacles", self.obstacles)
        self.sliders = map_data.get("sliders", self.sliders)
        self.burstSliders = map_data.get("burstSliders", self.burstSliders)
        self.basicBeatmapEvents = map_data.get("basicBeatmapEvents", self.basicBeatmapEvents)
        self.colorBoostBeatmapEvents = map_data.get("colorBoostBeatmapEvents", self.colorBoostBeatmapEvents)
        self.waypoints = map_data.get("waypoints", self.waypoints)
        self.basicEventTypesWithKeywords = map_data.get("basicEventTypesWithKeywords", self.basicEventTypesWithKeywords)
        self.lightColorEventBoxGroups = map_data.get("lightColorEventBoxGroups", self.lightColorEventBoxGroups)
        self.lightRotationEventBoxGroups = map_data.get("lightRotationEventBoxGroups", self.lightRotationEventBoxGroups)
        self.lightTranslationEventBoxGroups = map_data.get("lightTranslationEventBoxGroups", self.lightTranslationEventBoxGroups)
        self.useNormalEventsAsCompatibleEvents = map_data.get("useNormalEventsAsCompatibleEvents", self.useNormalEventsAsCompatibleEvents)
        self.customData = map_data.get("customData", self.customData)

    def __repr__(self) -> str:
        return f"Difficulty(diffname={self.diffname}, diffpath={self.diffpath}, suggestions={self.suggestions}, requirements={self.requirements})"

    def to_json(self) -> str:
        return json.dumps({
            "version": "3.3.0",
            "bpmEvents": self.bpmEvents,
            "rotationEvents": self.rotationEvents,
            "colorNotes": self.colorNotes,
            "bombNotes": self.bombNotes,
            "obstacles": self.obstacles,
            "sliders": self.sliders,
            "burstSliders": self.burstSliders,
            "basicBeatmapEvents": self.basicBeatmapEvents,
            "colorBoostBeatmapEvents": self.colorBoostBeatmapEvents,
            "waypoints": self.waypoints,
            "basicEventTypesWithKeywords": self.basicEventTypesWithKeywords,
            "lightColorEventBoxGroups": self.lightColorEventBoxGroups,
            "lightRotationEventBoxGroups": self.lightRotationEventBoxGroups,
            "lightTranslationEventBoxGroups": self.lightTranslationEventBoxGroups,
            "useNormalEventsAsCompatibleEvents": self.useNormalEventsAsCompatibleEvents,
        }, indent=4)

class Beatmap:
    def __init__(self, infopath="Info.dat"):
        with open(infopath, "r") as f:
            self.infopath = infopath
            self.info = json.load(f)
            self.difficulties = []
            folder = os.path.dirname(infopath)
            for diffset in self.info["_difficultyBeatmapSets"]():
                for diff in diffset["_difficultyBeatmaps"]():
                    diffpath = os.path.join(folder, diff["_beatmapFilename"])
                    self.difficulties.append(
                        Difficulty(
                            diffname=f"{diff['_difficulty']}{diffset['_beatmapCharacteristicName']}",
                            diffpath=diffpath,
                            suggestions=diff["_customData"].get("_suggestions", []),
                            requirements=diff["_customData"].get("_requirements", []),
                        )
                    )

    def loadDifficulty(self, diffname) -> Difficulty:
        for difficulty in self.difficulties:
            if difficulty.diffname == diffname:
                return difficulty
        raise ValueError(f"Difficulty '{diffname}' not found in the beatmap.")

    def save(self) -> None:
        with open(self.infopath, "w") as f:
            json.dump(self.info, f, indent=4)
        for difficulty in self.difficulties:
            with open(difficulty.diffpath, "w") as f:
                f.write(difficulty.to_json())

def append_values(obj, toAppend) -> list:
    obj.extend(toAppend)
    return obj