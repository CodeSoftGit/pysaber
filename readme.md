# PySaber
A Beat Saber framework written in Python.

## Features
### Compression
Significantly reduce your wall count without losing quality!
### TTF Font Support
Load TTF files to use any font you want. Arial? Comic Sans? Ghostly Panic? If it's a TTF file, it should work!
### Synced Lyrics Support
Generate styled text from synchronized lyrics in LRC files.
### Customizable Text Generation
Generate text with customizable parameters including color, position, scale, depth, and track.
### Geometric Text Generation
Generate text using geometric objects with customizable materials and shaders.
### Difficulty Management
Easily manage and modify beatmaps using the `Beatmap` and `Difficulty` classes.
### Multi-Language Support
Generate text in multiple languages with Unicode support.

## Example Usage
```
if __name__ == "__main__":
    beatmap = Beatmap(
        r"CustomWIPLevels\Underneath the Tree\Info.dat"
    )
    print(beatmap.difficulties)
    map_data = beatmap.loadDifficulty("ExpertPlusStandard")

    lrc_file = "lyrics.lrc"
    color = "#FF0000"
    x, y, z = 0, 5, 0
    scale = 0.01
    depth = 0.001
    track = "lyrics"
    centered = True
    geo = False

    font = ttf_to_font("Comic Sans MS.ttf", 128)
    map_data.obstacles = append_values(
        map_data.obstacles,
        create_text_from_lrc(
            lrc_file, color, x, y, z, scale, depth, track, centered, font, geo
        ),
    )
```