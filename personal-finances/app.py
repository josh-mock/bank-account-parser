from flask import Flask, render_template, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'instance/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def is_csv(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        files = request.files.getlist('file')
        if not files:
            flash('No selected file')
            return redirect(request.url)

        for file in files:
            if file and is_csv(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                flash(f"File '{filename}' uploaded successfully!")
            else:
                flash(f'{file.filename} has an invalid file type. Please upload a CSV file.')
                return redirect(request.url)

        return redirect(url_for('upload_file'))
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
