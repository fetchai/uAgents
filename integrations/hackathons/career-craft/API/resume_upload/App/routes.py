import base64
import io
from docx import Document
from supabase import create_client
from flask import Flask, request, jsonify, Blueprint
import os
# Supabase credentials

#putting the supabase url and key here so that they are accessable during evaluation
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def base64_to_docx(base64_string, filename):

    binary_data = base64.b64decode(base64_string)
    docx_buffer = io.BytesIO(binary_data)
    docx_doc = Document(docx_buffer)
    docx_doc.save(filename)

def upload_to_supabase(filename, bucket_name, folder_name):
    with open(filename, 'rb') as file:
        file_data = file.read()

    response = supabase.storage.from_("resume").upload(
        file=file_data,
        path=f"{folder_name}/{filename}"
    )
    res = supabase.storage.from_('resume').get_public_url(f"{folder_name}/{filename}")
    print(res)
    return res


bucket_name = "SUPABASE_BUCKET_NAME"
folder_name = "SUPABASE_FOLDER_NAME"

main = Blueprint('main', __name__)

@main.route('/upload', methods=['POST'])
def upload_file():
    
    base64_string = request.json['base64_string']
    filename = request.json['filename']
    base64_to_docx(base64_string, filename)
    out = upload_to_supabase(filename, bucket_name, folder_name)
    
    return jsonify({"response": out})

