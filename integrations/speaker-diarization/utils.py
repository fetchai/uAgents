import io

import requests
import torchaudio
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook


def load_audio_from_url(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    audio_data = io.BytesIO(response.content)
    waveform, sample_rate = torchaudio.load(audio_data)
    return waveform, sample_rate


def diarization_to_dict(diarization):
    result = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        result.append({"start": turn.start, "end": turn.end, "speaker": speaker})
    return result


def perform_speaker_diarization(hf_token, audio_url):
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token,
        )

        with ProgressHook() as hook:
            waveform, sample_rate = load_audio_from_url(audio_url)
            diarization = pipeline(
                {"waveform": waveform, "sample_rate": sample_rate}, hook=hook
            )

        output = diarization_to_dict(diarization)

        print(f"Diarization completed and output is '{output}'.")
        return output

    except requests.exceptions.RequestException as e:
        print(f"Error loading audio from URL: {e}")
    except ModuleNotFoundError as e:
        print(f"Module not found: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
