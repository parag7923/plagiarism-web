from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os
import zipfile
import fitz
import difflib
import shutil
import easyocr

app = Flask(__name__)
socketio = SocketIO(app)

# Function to extract ZIP and count PDF files
def extract_zip(file_path, extract_to='uploads'):
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return len([f for f in os.listdir(extract_to) if f.endswith('.pdf')])

# Function to extract text from PDFs
def extract_text_from_pdf(pdf_path, reader, file_index, total_files):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            image = page.get_pixmap()
            image.save('temp_page.png')
            result = reader.readtext('temp_page.png', detail=0)
            text += ' '.join(result) + '\n'
        doc.close()
        os.remove('temp_page.png')
    except Exception as e:
        return f"Error: {e}"
    return text

# Function to detect plagiarism and group similar files
def detect_plagiarism(texts, file_names):
    plagiarism_groups = []
    visited = [False] * len(texts)

    for i in range(len(texts)):
        if visited[i]:
            continue

        group = [file_names[i]]
        visited[i] = True
        for j in range(i + 1, len(texts)):
            similarity = difflib.SequenceMatcher(None, texts[i], texts[j]).ratio()
            if similarity > 0.7:
                group.append(file_names[j])
                visited[j] = True

        if len(group) > 1:
            plagiarism_groups.append(group)

    no_plagiarism_files = [file_names[i] for i in range(len(file_names)) if not visited[i]]
    return plagiarism_groups, no_plagiarism_files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"})
    
    if file and file.filename.endswith('.zip'):
        file_path = os.path.join('uploads', 'uploaded.zip')
        os.makedirs('uploads', exist_ok=True)
        file.save(file_path)
        num_files = extract_zip(file_path)
        return jsonify({"success": True, "num_files": num_files})
    
    return jsonify({"error": "Invalid file type"})

# SocketIO handler to process files and send progress
@socketio.on('process_files')
def process_files(data):
    extract_to = 'uploads'
    pdf_files = [f for f in os.listdir(extract_to) if f.endswith('.pdf')]
    reader = easyocr.Reader(['en'])

    texts = []
    file_names = []
    
    # Start processing files
    total_files = len(pdf_files)
    for i, pdf in enumerate(pdf_files):
        text = extract_text_from_pdf(os.path.join(extract_to, pdf), reader, i+1, total_files)
        texts.append(text)
        file_names.append(pdf)

        # Send real-time progress update
        progress = (i + 1) / total_files * 100
        emit('progress_update', {'progress': progress})

    plagiarism_groups, no_plagiarism_files = detect_plagiarism(texts, file_names)
    
    # Clean up the directory
    shutil.rmtree(extract_to)

    # Send the results and no plagiarism files
    emit('processing_complete', {'plagiarism_groups': plagiarism_groups, 'no_plagiarism_files': no_plagiarism_files})

if __name__ == '__main__':
    socketio.run(app, debug=True)
