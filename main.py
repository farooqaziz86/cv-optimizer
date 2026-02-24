import os
import requests
import anthropic
from flask import Flask, render_template_string, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
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
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    
    doc = SimpleDocTemplate(
        temp_file.name,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        name='CVName',
        fontSize=16,
        fontName='Helvetica-Bold',
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='CVContact',
        fontSize=9,
        fontName='Helvetica',
        spaceAfter=12,
        textColor='#333333'
    ))
    styles.add(ParagraphStyle(
        name='CVSection',
        fontSize=11,
        fontName='Helvetica-Bold',
        spaceBefore=14,
        spaceAfter=8,
        borderPadding=(0, 0, 3, 0)
    ))
    styles.add(ParagraphStyle(
        name='CVJob',
        fontSize=10,
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name='CVText',
        fontSize=10,
        fontName='Helvetica',
        spaceAfter=3,
        leading=12
    ))
    styles.add(ParagraphStyle(
        name='CVBullet',
        fontSize=10,
        fontName='Helvetica',
        leftIndent=12,
        spaceAfter=3,
        leading=12,
        bulletIndent=0
    ))
    
    story = []
    lines = cv_text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 6))
        elif line.startswith('Farooq'):
            story.append(Paragraph(line, styles['CVName']))
        elif '|' in line and i < 3:
            story.append(Paragraph(line, styles['CVContact']))
        elif line == line.upper() and len(line) > 3 and not any(char.isdigit() for char in line):
            story.append(Paragraph(f'<u>{line}</u>', styles['CVSection']))
        elif line.startswith('•') or line.startswith('-') or line.startswith('●'):
            bullet_text = line[1:].strip()
            story.append(Paragraph(f'• {bullet_text}', styles['CVBullet']))
        elif any(year in line for year in ['2020', '2021', '2022', '2023', '2024', '2025', '2019', '2018', '2013', '2009']):
            story.append(Paragraph(line, styles['CVJob']))
        else:
            story.append(Paragraph(line, styles['CVText']))
    
    doc.build(story)
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
    <h1>CV Optimizer</h1>
    <p class="subtitle">Paste a job description and get an ATS-optimized PDF</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="POST" id="cvForm">
        <label for="job_url">Job URL (optional)</label>
        <textarea name="job_url" id="job_url" rows="1" placeholder="https://linkedin.com/jobs/..."></textarea>
        <label for="job_description">Job Description *</label>
        <textarea name="job_description" id="job_description" rows="15" placeholder="Paste the full job description here..." required></textarea>
        <button type="submit" id="submitBtn">Optimize My CV and Download PDF</button>
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
```

5. Click **"Commit changes"**

---

**Then update `requirements.txt`:**

1. Click on **`requirements.txt`**
2. Click the **pencil icon** to edit
3. Replace everything with:
```
flask==3.0.0
anthropic==0.45.0
requests==2.31.0
reportlab==4.1.0
gunicorn==21.2.0
