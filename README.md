# ad-begone

I hate ads. I especially hate ads when I'm listening to a podcast first thing in the morning.

This python package provides a simple command line utility, `adwatch` which watches a given directory for MP3 files, detects ads in them, and removes them. It is intended for use with [Audiobookshelf](https://www.audiobookshelf.org/), which provides exactly this sort of directory.

The way this tool works is by using OpenAI's Whisper Speech-To-Text transcription service, along with the OpenAI Chat Completions API. The latter takes the transcription from the former in chunks of segments, and uses OpenAI's tool functionality to point specifically to where the ads begin and end. Then we can split the MP3 into different parts, drop the ads, and recombine. It also adds a short [bell-like notification](https://github.com/samanthavbarron/ad-begone/blob/main/src/ad_begone/notif.mp3) where ads were removed.

In my testing most of the billing usage from OpenAI's API is due to the Whisper transcription service. Removing ads on a ~20 minute podcast cost me about $0.30, so roughly $1/hour. That's a bit steep for frequent use in my opinion, but since the bottleneck is the transcription and the [Whisper model is open source](https://github.com/openai/whisper), the costs could likely be improved.

# Usage

```bash
# Install the package
pip install .
# Usage with arguments, default is 600 seconds between checking for new mp3 files
adwatch --directory=directory/to/watch --sleep=600
# Or just a path
adwatch .
# No directory defaults to current directory
adwatch
```
