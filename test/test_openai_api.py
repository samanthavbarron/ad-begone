
from unittest import TestCase

from pydub import AudioSegment

from ad_begone.utils import cached_transcription
from ad_begone.utils import annotate_transcription
from ad_begone.utils import get_ordered_annotations
from ad_begone.utils import find_ad_time_windows


class TestOpenAIAPI(TestCase):

    def test_make_transcription(self):
        transcription = cached_transcription("test/data/test.mp3")

    def test_annotate_transcription(self):
        transcription = cached_transcription("test/data/test.mp3")
        completion = annotate_transcription(transcription)
        get_ordered_annotations(completion)
    
    def test_find_ad_time_windows(self):
        transcription = cached_transcription("test/data/test.mp3")
        completion = annotate_transcription(transcription)

        annotations = get_ordered_annotations(completion)
        windows = find_ad_time_windows(transcription, annotations)
    
    def test_split_mp3(self):
        transcription = cached_transcription("test/data/test.mp3")
        completion = annotate_transcription(transcription)
        annotations = get_ordered_annotations(completion)
        windows = find_ad_time_windows(transcription, annotations)
        
        audio = AudioSegment.from_mp3("test/data/test.mp3")
        notif = AudioSegment.from_mp3("test/data/notif.mp3")

        kept_windows = []
        for window in windows:
            if window.segment_type == "content":
                kept_windows.append(audio[window.start * 1000: window.end * 1000])
            if window.segment_type == "ad":
                kept_windows.append(notif)
        
        audio_no_ads = AudioSegment.silent(duration=0)
        for kept_window in kept_windows:
            audio_no_ads += kept_window
        
        audio_no_ads.export("test/data/test_no_ads.mp3", format="mp3")