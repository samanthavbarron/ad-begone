<p align="center">
  <img src="logo.svg" alt="ad-begone logo" width="256" />
</p>

# ad-begone

I hate ads. I especially hate ads when I'm listening to a podcast first thing in the morning.

This Python package provides a CLI tool, `adwatch`, that watches a directory for MP3 files, detects ads in them, and removes them. It is intended for use with [Audiobookshelf](https://www.audiobookshelf.org/), which provides exactly this sort of directory.

## How it works

1. **Transcribe** -- Uses OpenAI's Whisper API to transcribe podcast audio into timestamped segments
2. **Annotate** -- Sends segments to the GPT-4o Chat Completions API to classify each segment as content or ad
3. **Trim** -- Removes ad segments and inserts a short [notification sound](https://github.com/samanthavbarron/ad-begone/blob/main/src/ad_begone/notif.mp3) where ads were removed

## Prerequisites

- Python 3.12+
- [ffmpeg](https://ffmpeg.org/) (required by pydub for audio processing)
- An [OpenAI API key](https://platform.openai.com/api-keys) set as `OPENAI_API_KEY` in your environment

## Usage

```bash
pip install .
```

`adwatch` runs in a loop, scanning for new MP3 files and processing them:

```bash
adwatch --directory /path/to/podcasts
```

To process a single file:

```bash
python -m ad_begone.remove_ads episode.mp3
```

## Docker

```bash
# Set your API key in .env or export it
export OPENAI_API_KEY=sk-...

# Place podcast files in ./podcasts/
docker compose up
```

The compose configuration mounts `./podcasts` to `/data` inside the container and runs with `restart: unless-stopped`.

## License

[GPL-3.0](LICENSE)
