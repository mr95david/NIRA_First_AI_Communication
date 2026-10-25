"""DESCONTINUADO (não registrado em create_app): upload de áudio e transcrição com Deepgram."""
from api.services.deepgram_service import DeepgramService
from api.utils import RECORD_FOLDER
from api.utils import RECORD_FILE
from flask import Blueprint
from flask import request
from flask import jsonify
from time import sleep
import os


deepgram_bp = Blueprint('deepgram_bp', __name__)

DEEP_API = os.getenv('DEEPGRAM_API_KEY')

deepgram_client = DeepgramService(DEEP_API)

@deepgram_bp.route('/upload', methods = ['POST'])
def uploadAudio():
    """Salva o áudio recebido (wav, mp3, m4a) em RECORD_FOLDER e devolve sua transcrição."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    allowed_extensions = {'wav', 'mp3', 'm4a'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'error': 'Formato de archivo no permitido. Solo se permiten archivos de audio'}), 400
    
    file_path = os.path.join(RECORD_FOLDER, file.filename)
    file.save(file_path)

    try:
        words = deepgram_client.transcription(file_path)
        print(words)

        return jsonify({
            'message': 'File uploaded successfully',
            'path': file_path,
            'transcription': words
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500