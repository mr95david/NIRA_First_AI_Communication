"""Transcrição de áudio com Deepgram (descontinuado)."""
from deepgram import DeepgramClient
from deepgram import PrerecordedOptions
from deepgram import FileSource
from typing import Union
from typing import AnyStr
from os import PathLike

class DeepgramService:
    def __init__(self, api_key: AnyStr) -> None:
        self.client = DeepgramClient(api_key)

        self.options_ = PrerecordedOptions(
            model = "nova-2",
            smart_format = True,
            language = 'pt-br',
        )

    def transcription(self, file_name: Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]):
        """Transcreve um arquivo wav; devolve o texto ou {'error': ...} se falhar."""
        try:
            with open(file_name,"rb") as audio:
                source: FileSource = {"buffer": audio, "mimetype": "audio/wav"}
                response = self.client.listen.prerecorded.v("1").transcribe_file(source, self.options_)

            return response.results["channels"][0]["alternatives"][0]["transcript"]

        except Exception as e:
            return {"error": str(e)}
        
        