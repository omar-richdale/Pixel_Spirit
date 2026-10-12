# Pixel Spirit

Three pixel and phosphor pieces about Omar, of Agadir: a digital guy in an AI world.
Every page is a single static HTML file. Open it in a browser, or serve the folder with
any static host (GitHub Pages works as is).

| Folder | What it is |
|---|---|
| [`ten-thousand-mouths/`](ten-thousand-mouths/) | A four-minute pixel-art film. Omar, keeper of the agadir, walks from Agadir to face the Grey Sovereign, Lord of Ten Thousand Mouths. Dialogue in speech bubbles, a boss fight, and a score synthesized live with Web Audio (oud in the Hijaz mode, bendir, choir, timpani, chiptune). |
| [`digital-guy/`](digital-guy/) | A 52-second motion piece. Omar as 72x90 phosphor pixels inside a soft, continuous WebGL world, in five scenes that end in an ordered dither. |
| [`old-light-observatory/`](old-light-observatory/) | An interactive portfolio set on a phosphor radar: each memory is a point of light, placed by how long ago it happened. |
| [`tools/`](tools/) | `phosphor.py`, which turns a photo into a green or amber terminal ID card, and `build.py`, which rebuilds the self-contained pages. |

## Run locally

```bash
python -m http.server 8000
# then open http://localhost:8000/ten-thousand-mouths/
```

Sound starts only after a click, as browsers require. In the film, click the scene or press
Space to hurry the words; the chapter buttons sit at the bottom.

## Rebuild

`ten-thousand-mouths/src.html` and `digital-guy/src.html` are the editable sources. Their
pixel data (`avatar.b64`, `portrait.txt`) is derived from a photo and is substituted in by:

```bash
python tools/build.py
```

## Credits

Fonts from Google Fonts: Cinzel, EB Garamond, Silkscreen, VT323, Hanken Grotesk,
IBM Plex Mono. All music and sound is generated in the browser; no audio files are used.
