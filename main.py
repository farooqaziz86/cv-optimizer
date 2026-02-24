import os
import requests
import anthropic
from flask import Flask, render_template_string, request

app = Flask(__name__)

CV_DOC_ID = "1CKzwOMJLt85-t8k8b2hTKQUZ6Ak_U4Q2_kKF7aSuH7M"

def get_cv_content():
    url = f"https://docs.google.com/document/d/{CV_DOC_ID}/export?format=txt"
    response = requests.get(url)
    return response.text

def optimize_cv(cv_content, job_description):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = f"""You are an expert CV writer and ATS optimization specialist.

STRICT RULES:
1. DO NOT change the structure or format of the CV
2. DO NOT add or remove any sections
3. DO NOT change job titles, company names, dates, or locations
4. DO NOT invent any new experience or achievements
5. ONLY reword bullet points to naturally include relevant keywords from the job description
6. Keep the same number of bullet points per role
7. Maintain a professional, human tone - not robotic
8. Focus on matching terminology and keywords from the job posting

STRUCTURE TO PRESERVE:
- Name and contact info (keep exactly as is)
- WORK EXPERIENCE section with same companies, titles, dates
- PROJECT EXPERIENCE section with same projects, titles, dates
- EDUCATION section (keep exactly as is)
- SKILLS & INTERESTS section (you may add 2-3 relevant skills if they match the job)

MY CURRENT CV:
{cv_content}

JOB DESCRIPTION:
{job_description}

OUTPUT THE OPTIMIZED CV (same structure, optimized wording):"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CV Optimizer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f7fa; }
        h1 { color: #2c3e50; text-align: center; }
        .subtitle { text-align: center; color: #7f8c8d; margin-bottom: 30px; }
        form, .result-box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #34495e; }
        textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; margin-bottom: 20px; resize: vertical; font-family: inherit; }
        textarea:focus { outline: none; border-color: #3498db; }
        button { width: 100%; padding: 15px; background: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; }
        button:hover { background: #2980b9; }
        button:disabled { background: #bdc3c7; cursor: not-allowed; }
        .loading { display: none; text-align: center; margin-top: 20px; color: #7f8c8d; }
        .error { background: #fee; color: #c0392b; padding: 15px; border-radius: 6px; margin-bottom: 20px; }
        .tips { background: #e8f6ff; padding: 15px; border-radius: 6px; margin-top: 20px; font-size: 13px; color: #2c3e50; }
        .result-box h2 { color: #27ae60; margin-top: 0; }
        .cv-output { white-space: pre-wrap; font-family: 'Times New Roman', serif; font-size: 14px; line-height: 1.6; background: #fafafa; padding: 20px; border: 1px solid #ddd; border-radius: 6px; max-height: 600px; overflow-y: auto; }
        .copy-btn { background: #27ae60; margin-top: 15px; }
        .copy-btn:hover { background: #219a52; }
        .steps { background: #fff3cd; padding: 15px; border-radius: 6px; margin-top: 15px; font-size: 13px; }
        .steps strong { display: block; margin-bottom: 8px; }
    </style>
</head>
<body>
    <h1>CV Optimizer</h1>
    <p class="subtitle">Paste a job description and get an ATS-optimized CV</p>
    
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    
    {% if optimized_cv %}
    <div class="result-box">
        <h2>Your Optimized CV</h2>
        <div class="cv-output" id="cvOutput">{{ optimized_cv }}</div>
        <button class="copy-btn" onclick="copyCV()">Copy to Clipboard</button>
        <div class="steps">
            <strong>Next Steps:</strong>
            1. Click "Copy to Clipboard" above<br>
            2. Open your Google Doc CV<br>
            3. Select all (Ctrl+A) and paste (Ctrl+V)<br>
            4. Download as PDF: File → Download → PDF
        </div>
    </div>
    {% endif %}
    
    <form method="POST" id="cvForm">
        <label for="job_url">Job URL (optional)</label>
        <textarea name="job_url" id="job_url" rows="1" placeholder="https://linkedin.com/jobs/..."></textarea>
        <label for="job_description">Job Description *</label>
        <textarea name="job_description" id="job_description" rows="15" placeholder="Paste the full job description here..." required>{{ job_description if job_description else '' }}</textarea>
        <button type="submit" id="submitBtn">Optimize My CV</button>
        <div class="loading" id="loading">Optimizing... 20-30 seconds...</div>
    </form>
    
    <div class="tips"><strong>Tips:</strong> Copy the ENTIRE job description including requirements. Your CV structure stays the same - only wording gets optimized for ATS keywords.</div>
    
    <script>
        document.getElementById('cvForm').addEventListener('submit', function() {
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').textContent = 'Processing...';
            document.getElementById('loading').style.display = 'block';
        });
        
        function copyCV() {
            const cvText = document.getElementById('cvOutput').innerText;
            navigator.clipboard.writeText(cvText).then(function() {
                const btn = document.querySelector('.copy-btn');
                btn.textContent = 'Copied!';
                btn.style.background = '#1e8449';
                setTimeout(() => {
                    btn.textContent = 'Copy to Clipboard';
                    btn.style.background = '#27ae60';
                }, 2000);
            });
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        job_description = request.form.get('job_description', '').strip()
        if not job_description:
            return render_template_string(HTML_TEMPLATE, error="Please paste a job description", optimized_cv=None, job_description=None)
        try:
            cv_content = get_cv_content()
            optimized_cv = optimize_cv(cv_content, job_description)
            return render_template_string(HTML_TEMPLATE, error=None, optimized_cv=optimized_cv, job_description=job_description)
        except Exception as e:
            return render_template_string(HTML_TEMPLATE, error=f"Error: {str(e)}", optimized_cv=None, job_description=job_description)
    return render_template_string(HTML_TEMPLATE, error=None, optimized_cv=None, job_description=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
