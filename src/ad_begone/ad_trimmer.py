from openai.types.audio.transcription_verbose import TranscriptionVerbose
from openai.types.chat.parsed_chat_completion import ParsedChatCompletion

from .models import Window
from .utils import (
    cached_annotate_transcription,
    cached_transcription,
    find_ad_time_windows,
    get_ordered_annotations,
    _remove_ads,
)


class AdTrimmer:

    def __init__(self, file_name: str):
        self.file_name = file_name
        if not file_name.endswith(".mp3"):
            raise ValueError("File name must end with .mp3")
        self.transcription_cache_file = file_name + ".transcription.json"
        self.segments_cache_file = file_name + ".segments.json"

    def transcription(self) -> TranscriptionVerbose:
        return cached_transcription(
            file_name=self.file_name,
            file_transcription=self.transcription_cache_file,
        )

    def segments_completion(self) -> ParsedChatCompletion:
        return cached_annotate_transcription(
            transcription=self.transcription(),
            file_name=self.segments_cache_file,
        )

    def get_time_windows(self) -> list[Window]:
        annotations = get_ordered_annotations(self.segments_completion())
        return find_ad_time_windows(self.transcription(), annotations)

    def remove_ads(
        self,
        out_name: str | None = None,
        notif_name: str = "src/ad_begone/notif.mp3",
    ):
        _remove_ads(
            file_name=self.file_name,
            out_name=out_name,
            notif_name=notif_name,
            file_name_transcription_cache=self.transcription_cache_file,
        )