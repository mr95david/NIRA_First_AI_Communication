from api import db

class users(db.Model):
    """Usuário do sistema. Sua pasta de dados é criada em user_path/ ao registrá-lo."""
    __tablename__ = 'data_users'
    id_value = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    profession = db.Column(db.String(50), nullable=False)
    sexo = db.Column(db.String(50), nullable=False)
    # Caminhos dos dados do usuário
    user_path = db.Column(db.String(200), nullable=False)
    audio_path = db.Column(db.String(200), nullable=False)
    transcription_path = db.Column(db.String(200), nullable=False)
    ia_path = db.Column(db.String(200), nullable=False)