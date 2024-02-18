from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import requests
import json
import os
from werkzeug.utils import secure_filename
import base64
import logging

# Defining a folder to store uploaded files
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_verification_response(id=None):
    url = "https://verify.vouched.id/api/jobs"
    
    headers = {
        "accept": "application/json; charset=utf-8",
        "X-API-Key": "TFk5Ig-X-~hXf2kRzMMbinS8__SFTZ"
    }
    
    params = {}
    if id is not None:
        params["id"] = id

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        status_code = response.status_code
        message = 'Data fetched successfully.'
    else:
        data = None
        status_code = response.status_code
        message = f'Failed to fetch data. Status code: {status_code}'
    
    response_data = {
        'status': status_code,
        'data': data,
        'message': message
    }
    
    # Save response to JSON file
    with open('responses/verification_response.json', 'w') as f:
        json.dump(response_data, f, indent=4)
    
    return response_data


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def submit_verification_job(firstName, lastName, email, phone, idPhoto_path):
    url = "https://verify.vouched.id/api/jobs"
    headers = {
        "accept": "application/json; charset=utf-8",
        "content-type": "application/json",
        "X-API-Key": "TFk5Ig-X-~hXf2kRzMMbinS8__SFTZ"
    }
    payload = {
        "type": "id-verification",
        "params": {
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "phone": phone,
            "idPhoto": idPhoto_path  # Passing the file path instead of FileStorage object
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        status_code = response.status_code
        message = 'Verification job submitted successfully.'
    else:
        data = None
        status_code = response.status_code
        error_message = response.json()["errors"][0]["message"]  # Extracting the error message
        message = f'Failed to submit verification job. Status code: {status_code}. Error: {error_message}'

    response_data = {
        'status': status_code,
        'data': data,
        'message': message
    }
    
    return response_data


def download_job_pdf(job_id, confidences=True):
    url = f"https://verify.vouched.id/api/jobs/{job_id}/download"
    headers = {
        "accept": "application/json; charset=utf-8",
        "X-API-Key": "TFk5Ig-X-~hXf2kRzMMbinS8__SFTZ"
    }
    params = {
        "confidences": confidences
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        pdf_data = response.json().get("pdf", None)
        if pdf_data:
            return {
                'status': 200,
                'data': pdf_data,
                'message': 'PDF downloaded successfully.'
            }
    else:
        return {
            'status': response.status_code,
            'data': None,
            'message': f'Failed to download PDF. Status code: {response.status_code}'
        }


def verify_ssn(firstName, lastName, email, phone, ssn, dob, address):
    url = "https://verify.vouched.id/api/private-ssn/verify"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": "TFk5Ig-X-~hXf2kRzMMbinS8__SFTZ"
    }
    payload = {
        "firstName": firstName,
        "lastName": lastName,
        "phone": phone,
        "ssn": ssn,
        "email": email,
        "dob": dob,
        "address": address
    }
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        status_code = response.status_code
        message = 'SSN verification successful.'
    else:
        data = None
        status_code = response.status_code
        error_message = response.json()["errors"][0]["message"]  # Extracting the error message
        message = f'SSN verification failed. Status code: {status_code}. Error: {error_message}'

    response_data = {
        'status': status_code,
        'data': data,
        'message': message
    }
    
    return response_data


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_verification_response', methods=['GET', 'POST'])
def get_verification_response_route():
    if request.method == 'POST':
        if 'id' in request.form:
            id = request.form['id']
            response_data = get_verification_response(id=id)
        else:
            response_data = get_verification_response()  # Fetch all verifications

        return render_template('response.html', response=response_data)
    else:
        # Handle GET request (initial page load)
        return render_template('index.html')


@app.route('/submit_verification_jobs', methods=['GET', 'POST'])  
def submit_verification_jobs():
    if request.method == 'POST':
        # Extract form data
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        phone = request.form['phone']
        
        # Check if the post request has the file part
        if 'idPhoto' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        idPhoto = request.files['idPhoto']
        
        # If user does not select file, browser also submit an empty part without filename
        if idPhoto.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        # If the file exists and is allowed
        if idPhoto and allowed_file(idPhoto.filename):
            # Generate a secure filename to prevent filename clashes and save the file
            filename = secure_filename(idPhoto.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Create the UPLOAD_FOLDER directory if it does not exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            idPhoto.save(filepath)
            
            # Call the submit_verification_job function with the file path
            result = submit_verification_job(firstName, lastName, email, phone, filepath)
            
            # Return the result to the template
            return render_template('submitjobsreponse.html', response=result)
        else:
            flash('Allowed file types are png, jpg, jpeg, gif')
            return redirect(request.url)
    else:
        # If a GET request is made to this route, render the form
        return render_template('submitjobs.html')
    

@app.route('/download_job_pdf', methods=['GET', 'POST'])
def download_job():
    if request.method == 'POST':
        job_id = request.args.get('id')
        confidences = request.args.get('confidences', default=True, type=bool)
        
        # Call the function to get the PDF data
        pdf_result = download_job_pdf(job_id, confidences)
        if pdf_result['status'] == 200:
            # Decode the base64-encoded PDF data
            pdf_data = base64.b64decode(pdf_result['data'])
            # Create a temporary file path to save the PDF
            temp_file = f'temp_job_{job_id}.pdf'
            # Write the PDF data to the temporary file
            with open(temp_file, 'wb') as f:
                f.write(pdf_data)
            # Return the PDF file as an attachment
            return send_file(temp_file, as_attachment=True)
        else:
            return pdf_result['message']
    # Render the template for GET requests
    return render_template('downloadjobpdf.html')


# Route for verifying SSN
@app.route('/verify_ssn', methods=['GET', 'POST'])  # Allow both GET and POST requests
def verify_ssn_route():
    if request.method == 'POST':
        # Extract form data
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        phone = request.form['phone']
        ssn = request.form['ssn']
        dob = request.form['dob']
        address = request.form['address']
        
        # Call the verify_ssn function with the form data
        result = verify_ssn(firstName, lastName, email, phone, ssn, dob, address)
        
        # Render the verifyssn.html template and pass the response data as context
        return render_template('verifyssnresponse.html', response=result)
    else:
        # If a GET request is made to this route, render the form
        return render_template('verifyssn.html')


@app.route('/verify_dob', methods=['GET','POST'])
def verify_dob():
    print("Matched Path:", request.path)
    if request.method == 'POST':
        # Extract form data
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        phone = request.form['phone']
        dob = request.form['dob']
        
        # Make a POST request to the DOB verification API
        url = "https://verify.vouched.id/api/dob/verify"
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "X-API-Key": "TFk5Ig-X-~hXf2kRzMMbinS8__SFTZ"
        }
        payload = {
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "phone": phone,
            "dob": dob
        }
        response = requests.post(url, json=payload, headers=headers)
        
        # Process the response
        if response.status_code == 200:
            result = response.json()
            return render_template('dob_verification_result.html', result=result)
        else:
            error_message = response.json()["errors"][0]["message"]
            return f"Error: {error_message}", 500
    else:
        return "Method Not Allowed", 405


@app.route('/route_urls')
def route_urls():
    return render_template('vertical_tabs.html')

# Add cache-control headers for static files
@app.after_request
def add_cache_control(response):
    if "Cache-Control" not in response.headers:
        response.headers["Cache-Control"] = "no-store"
    return response
   

if __name__ == '__main__':
    # result = submit_verification_job("Louis", "White", "mamaloco79@gmail.com", "+16822979509")
    # print(result)
    app.run(debug=True)
