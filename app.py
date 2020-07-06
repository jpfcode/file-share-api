from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku
import io
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    'SQLALCHEMY_DATABASE_URI')

db = SQLAlchemy(app)
ma = Marshmallow(app)

heroku = Heroku(app)
CORS(app)


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    file_type = db.Column(db.String(), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __init__(self, name, file_type, data, user_id):
        self.name = name
        self.file_type = file_type
        self.data = data
        self.user_id = user_id


class FileSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "file_type")


file_schema = FileSchema()
files_schema = FileSchema(many=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    files = db.relationship("File", cascade="all,delete",
                            backref="user", lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password")


user_schema = UserSchema()
users_schema = UserSchema(many=True)


@app.route("/file/add", methods=["POST"])
def add_file():
    name = request.form.get('name')
    file_type = request.form.get('type')
    data = request.files.get('data')

    new_file = File(name, file_type, data.read())
    db.session.add(new_file)
    db.session.commit()

    return jsonify("File added successfully")


@app.route("/file/get/data", methods=["GET"])
def get_file_data():
    file_data = db.session.query(File).all()
    return jsonify(files_schema.dump(file_data))


@app.route("/file/get/<id>", methods=["GET"])
def get_file(id):
    file_data = db.session.query(File).filter(File.id == id).first()
    return send_file(
        io.BytesIO(file_data.data),
        attachment_filename=file_data.name,
        mimetype=file_data.file_type
    )


@app.route("/file/delete/<id>", methods=["DELETE"])
def delete_file(id):
    file_data = db.session.query(File).filter(File.id == id).first()
    db.session.delete(file_data)
    db.session.commit()
    return jsonify("File deleted successfully")

# python repl
# >>> from app import db
# >>> db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
