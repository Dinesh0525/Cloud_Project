from flask import Flask, render_template, request
import boto3
import requests

app = Flask(__name__)

# AWS credentials and region configuration
AWS_REGION = 'central-ca'


# Initialize S3 and Transcribe clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
transcribe_client = boto3.client('transcribe', region_name=AWS_REGION)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio_file' not in request.files:
        return "No audio file provided", 400
    
    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        return "No selected file", 400
    
    # Upload audio file to S3
    audio_file_key = 'audio/' + audio_file.filename
    s3_client.upload_fileobj(audio_file, 'project1inputbucket', audio_file_key)

    # Start transcription job
    transcribe_response = transcribe_client.start_transcription_job(
        TranscriptionJobName='TranscriptionJob',
        LanguageCode='en-US',
        MediaFormat='wav',
        Media={
            'MediaFileUri': f's3://your_bucket_name/{audio_file_key}'
        }
    )   

    # Get transcription job status
    job_status = transcribe_client.get_transcription_job(
        TranscriptionJobName=transcribe_response['TranscriptionJob']['TranscriptionJobName']
    )

    # Wait until the job is completed
    while job_status['TranscriptionJob']['TranscriptionJobStatus'] not in ['COMPLETED', 'FAILED']:
        job_status = transcribe_client.get_transcription_job(
            TranscriptionJobName=transcribe_response['TranscriptionJob']['TranscriptionJobName']
        )

    # If the job is successful, get the transcript
    if job_status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        transcript_uri = job_status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        transcript = requests.get(transcript_uri).json()
        transcript_text = transcript['results']['transcripts'][0]['transcript']
        return render_template('result.html', transcript=transcript_text)
    else:
        return "Transcription job failed", 500

if __name__ == '__main__':
    app.run(debug=True)
