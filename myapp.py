import boto3
import dotenv
import json
import jwt
import os
import hashlib
from datetime import datetime

# Initialization Stuff
dotenv.load_dotenv()

from flask import Flask, __version__, abort, render_template, redirect, url_for, request, render_template_string, redirect
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "<MYSQL_DATBASE_URI>"
db = SQLAlchemy(app)

# SQLAlchemy Classes
class Document(db.Model):
    __tablename__ = "documents"
    document_uuid = db.Column(db.String(36), primary_key=True, unique=True)
    document_type = db.Column(db.Text)
    document_id = db.Column(db.Text)
    access_level = db.Column(db.Text)
    uri = db.Column(db.Text)

class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.String(36), primary_key=True, unique=True)
    username = db.Column(db.Text)
    access_level = db.Column(db.Text)
    site = db.Column(db.Text)
    title = db.Column(db.Text)
    password_hash = db.Column(db.Text)
    password_salt = db.Column(db.Text)

# Utility Functions
def parse_s3_uri(s3_uri):
    path = s3_uri[5::]
    path_components = path.split("/")
    bucket = path_components[0]
    key_components = path_components[1::]
    key = "/".join(key_components)
    return bucket, key

def translate_doc_type(doc_type):
    to_translate = doc_type.lower()
    document_types = {
        "scp": "SCP File",
        "addenda": "Addendum File"
    }
    try:
        doc_type_name = document_types[to_translate]
    except KeyError:
        return doc_type
    else:
        return doc_type_name

# Routes
@app.route("/", methods=["GET"])
def site_home():
    return render_template("index.html")

@app.route("/auth", methods=["POST"])
def auth():
    try:
        data = request.get_json()
        username = str(data["username"])
        submitted_hash = str(data["password_hash"])
        user_info = User.query.filter_by(username=username).first()
    except KeyError:
        return json.dumps({"success": False, "error": "Error: Some or all required parameters were not provided."}), 400
    
    if user_info is None:
        return json.dumps({"success": False, "error": "Error: User Not Found."}), 400
    else:
        password_payload = user_info.user_id + user_info.username + user_info.password_salt + submitted_hash
        password_hash = hashlib.sha256(password_payload.encode('utf-8')).hexdigest()
        if password_hash != user_info.password_hash:
            return json.dumps({
                "success": False,
                "error": "Access Denied: Invalid Password.",
                "correct": user_info.password_hash,
                "calculated": password_hash
            }), 401
        else:
            jwt_secret = os.getenv("JWT_SECRET", "secret")
            auth_token_payload = {"user_id": user_info.user_id, "username": user_info.username}
            auth_token = jwt.encode(auth_token_payload, jwt_secret, algorithm="HS256").decode("utf-8")
            return json.dumps({
                "success": True,
                "auth_token": str(auth_token),
                "username": str(user_info.username),
                "access_level": str(user_info.access_level),
                "site": str(user_info.site),
                "title": str(user_info.title)
            })


@app.route("/document", methods=["POST"])
def get_scp_info():
    if bool(os.getenv("DISABLE_DOCUMENT_ACCESS", False)):
        return json.dumps({"success": False, "error": "Access Denied: Access to all documents is currently restricted."}), 403
    try:
        data = request.get_json()
        doc_id = data["doc_id"]
        doc_type = data["doc_type"]
        jwt_secret = os.getenv("JWT_SECRET", "secret")
        auth_data = jwt.decode(data["auth_token"], jwt_secret, algorithm="HS256")
    except KeyError:
        return json.dumps({"success": False, "error": "Error: Some or all required parameters were not provided."}), 400
    except jwt.exceptions.InvalidSignatureError:
        return json.dumps({"success": False, "error": "Access Denied: Invalid JWT Signature."}), 401
    except jwt.exceptions.DecodeError:
        return json.dumps({"success": False, "error": "Access Denied: Error occurred while decoding the provided JSON Web Token."}), 401
    except Exception as e:
        return json.dumps({"success": False, "error": f"Error: An error occurred while processing your request: {e}"}), 500
    else:
        user_info = User.query.filter_by(username=auth_data["username"]).first()
        if user_info is None:
            return json.dumps({"success": False, "error": "Access Denied: Unknown Username."}), 401
        else:
            doc_type_name = translate_doc_type(doc_type)
            document_info = Document.query.filter_by(document_type=doc_type_name, document_id=doc_id).first()
            if document_info is None:
                return json.dumps({"success": False, "error": f"Error: A document with type '{doc_type}' and ID '{doc_id}' does not exist."}), 404
            elif user_info.access_level < document_info.access_level:
                return json.dumps({"success": False, "error": f"Access Denied: Access level '{document_info.access_level}' or above required."})
            else:
                try:
                    f = open(f"document cache/{document_info.document_uuid}.txt", "r")
                except FileNotFoundError:
                    try:
                        document_bucket, document_key = parse_s3_uri(document_info.uri)
                        s3 = boto3.resource("s3", region_name="us-west-2")
                        obj = s3.Object(document_bucket, document_key)
                        response = obj.get()
                        body = response["Body"]
                        data = body.read().decode("utf-8")
                    except Exception as e:
                        return json.dumps({"success": False, "error": f"Error: An error occurred while processing your request: {e}"}), 500
                    else:
                        with open(f"document cache/{document_info.document_uuid}.txt", "w") as f:
                            f.write(data)
                        rendered_document = render_template_string(data, access_level=int(user_info.access_level))
                        return json.dumps({"success": True, "document": f"{rendered_document}"})
                else:
                    data = f.read()
                    f.close()
                    rendered_document = render_template_string(data, access_level=int(user_info.access_level))
                    return json.dumps({"success": True, "document": f"{rendered_document}"})

# Redirects
# @app.route("/home")
# def home_redir():
#     return redirect("/")

if __name__ == "__main__":
    app.run()