import os
import requests
import anthropic
from flask import Flask, render_template_string, request, send_file
from weasyprint import HTML
import tempfile

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

def create_pdf(cv_text):
    lines = cv_text.split('\n')
    html_content = []
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        if not line:
            html_content.append('<div class="spacer"></div>')
        elif line == line.upper() and len(line) > 3 and not any(char.isdigit() for char in line):
            html_content.append(f'<h2>{line}</h2>')
        elif line.startswith('•') or line.startswith('-') or line.startswith('●'):
            bullet_text = line[1:].strip()
            html_content.append(f'<li>{bullet_text}</li>')
        elif '|' in line and lines.index(original_line) < 3:
            html_content.append(f'<div class="contact">{line}</div>')
        elif any(year in line for year in ['2020', '2021', '2022', '2023', '2024', '2025', '2019', '2018', '2013', '2009']):
            html_content.append(f'<div class="job-line">{line}</div>')
        elif line.startswith('Farooq'):
            html_content.append(f'<h1>{line}</h1>')
        else:
            html_content.append(f'<p>{line}</p>')
    
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ margin: 1.2cm 1.5cm; size: A4; }}
            body {{ font-family: 'Times New Roman', Times, serif; font-size: 10.5pt; line-height: 1.4; color: #000; }}
            h1 {{ font-size: 18pt; margin: 0 0 5px 0; font-weight: bold; }}
            .contact {{ font-size: 10pt; margin-bottom: 15px; color: #333; }}
            h2 {{ font-size: 11pt; font-weight: bold; margin: 18px 0 10px 0; padding-bottom: 3px; border-bottom: 1px solid #000; }}
            .job-line {{ margin: 8px 0 3px 0; font-size: 10.5pt; }}
            p {{ margin: 3px 0; text-align: left; }}
            li {{ margin: 4px 0 4px 20px; text-align: left; list-style-type: disc; }}
            .spacer {{ height: 8px; }}
        </style>
    </head>
    <body>{''.join(html_content)}</body>
    </html>
    """
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    HTML(string=final_html).write_pdf(temp_file.name)
    return temp_file.name

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CV Optimizer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f7fa; }
        h1 { color: #2c3e50; text-align: center; }
        .subtitle { text-align: center; color: #7f8c8d; margin-bottom: 30px; }
        form { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #34495e; }
        textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; margin-bottom: 20px; resize: vertical; }
        textarea:focus { outline: none; border-color: #3498db; }
        button { width: 100%; padding: 15px; background: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; }
        button:hover { background: #2980b9; }
        button:disabled { background: #bdc3c7; cursor: not-allowed; }
        .loading { display: none; text-align: center; margin-top: 20px; color: #7f8c8d; }
        .error { background: #fee; color: #c0392b; padding: 15px; border-radius: 6px; margin-bottom: 20px; }
        .tips { background: #e8f6ff; padding: 15px; border-radius: 6px; margin-top: 20px; font-size: 13px; color: #2c3e50; }
    </style>
</head>
<body>
    <h1>📄 CV Optimizer</h1>
    <p class="subtitle">Paste a job description and get an ATS-optimized PDF</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="POST" id="cvForm">
        <label for="job_url">Job URL (optional)</label>
        <textarea name="job_url" id="job_url" rows="1" placeholder="https://linkedin.com/jobs/..."></textarea>
        <label for="job_description">Job Description *</label>
        <textarea name="job_description" id="job_description" rows="15" placeholder="Paste the full job description here..." required></textarea>
        <button type="submit" id="submitBtn">🚀 Optimize My CV and Download PDF</button>
        <div class="loading" id="loading">Optimizing... 20-30 seconds...</div>
    </form>
    <div class="tips"><strong>Tips:</strong> Copy the ENTIRE job description. Your CV structure stays the same - only wording gets optimized.</div>
    <script>
        document.getElementById('cvForm').addEventListener('submit', function() {
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').textContent = 'Processing...';
            document.getElementById('loading').style.display = 'block';
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        job_description = request.form.get('job_description', '').strip()
        if not job_description:
            return render_template_string(HTML_TEMPLATE, error="Please paste a job description")
        try:
            cv_content = get_cv_content()
            optimized_cv = optimize_cv(cv_content, job_description)
            pdf_path = create_pdf(optimized_cv)
            return send_file(pdf_path, as_attachment=True, download_name='Farooq_Aziz_CV.pdf', mimetype='application/pdf')
        except Exception as e:
            return render_template_string(HTML_TEMPLATE, error=f"Error: {str(e)}")
    return render_template_string(HTML_TEMPLATE, error=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
