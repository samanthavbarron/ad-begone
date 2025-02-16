
from unittest import TestCase

from ad_begone.ad_trimmer import AdTrimmer
from ad_begone.utils import (
    cached_annotate_transcription,
    cached_transcription,
    find_ad_time_windows,
    get_ordered_annotations,
    split_mp3,
)


class TestOpenAIAPI(TestCase):

    def test_make_transcription(self):
        transcription = cached_transcription("test/data/test.mp3")

    def test_annotate_transcription(self):
        transcription = cached_transcription("test/data/test.mp3")
        completion = cached_annotate_transcription(transcription, file_name="test/data/test_annotation_completion.json")
        get_ordered_annotations(completion)
    
    def test_find_ad_time_windows(self):
        transcription = cached_transcription("test/data/test.mp3")
        completion = cached_annotate_transcription(transcription, file_name="test/data/test_annotation_completion.json")

        annotations = get_ordered_annotations(completion)
        windows = find_ad_time_windows(transcription, annotations)
    
    def test_split_mp3(self):
        split_mp3(
            file_name="test/data/test.mp3",
            out_name="test/data/test_no_ads.mp3",
            file_name_transcription_cache="test/data/test_annotation_completion.json",
        )

class TestAdTrimmer(TestCase):
    
    def test_transcription(self):
        trimmer = AdTrimmer("test/data/test.mp3")
        trimmer.split_mp3("test/data/test_no_ads.mp3")