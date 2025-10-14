#!/usr/bin/env python3
"""
Production Airtable Dashboard for Render Deployment
"""

import os
import ssl
import urllib3
import requests
from flask import Flask, render_template_string, request, jsonify
from pyairtable import Api
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings and verification for corporate proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Monkey-patch requests library to always disable SSL verification
_original_request = requests.Session.request
def _patched_request(self, method, url, **kwargs):
    kwargs['verify'] = False
    return _original_request(self, method, url, **kwargs)
requests.Session.request = _patched_request

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration - Use environment variables
AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID:
    print("❌ ERROR: Missing environment variables!")
    print(f"AIRTABLE_TOKEN: {'✅ Set' if AIRTABLE_TOKEN else '❌ Missing'}")
    print(f"AIRTABLE_BASE_ID: {'✅ Set' if AIRTABLE_BASE_ID else '❌ Missing'}")
    print("Please add these in your Render Environment settings.")
    raise ValueError("Missing required environment variables: AIRTABLE_TOKEN and AIRTABLE_BASE_ID")

# Initialize Airtable API
api = Api(AIRTABLE_TOKEN)
base = api.base(AIRTABLE_BASE_ID)

# Dashboard HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HSE Statistics Report - Trojan Construction Group</title>
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --container-bg: white;
            --text-color: #2c3e50;
            --section-bg: #f8f9fa;
            --border-color: #e9ecef;
            --input-bg: white;
        }
        [data-theme="dark"] {
            --bg-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            --container-bg: #34495e;
            --text-color: #ecf0f1;
            --section-bg: #2c3e50;
            --border-color: #34495e;
            --input-bg: #2c3e50;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: var(--bg-gradient);
            min-height: 100vh;
            transition: all 0.3s ease;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: var(--container-bg);
            color: var(--text-color);
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: all 0.3s ease;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .content {
            padding: 40px;
        }
        .form-section {
            margin-bottom: 40px;
            padding: 30px;
            background: var(--section-bg);
            border-radius: 10px;
            border-left: 5px solid #007bff;
            transition: all 0.3s ease;
        }
        .form-section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #34495e;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-size: 16px;
            background: var(--input-bg);
            color: var(--text-color);
            transition: all 0.3s ease;
            box-sizing: border-box;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.25);
        }
        .btn {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,123,255,0.3);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .table-selector {
            margin-bottom: 30px;
            text-align: center;
        }
        .table-btn {
            display: inline-block;
            margin: 10px;
            padding: 15px 25px;
            background: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s;
            font-weight: 600;
        }
        .table-btn:hover, .table-btn.active {
            background: #007bff;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,123,255,0.3);
        }
        .theme-btn, .about-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid rgba(255,255,255,0.3);
            padding: 10px 15px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
            backdrop-filter: blur(10px);
        }
        .theme-btn:hover, .about-btn:hover {
            background: rgba(255,255,255,0.3);
            border-color: rgba(255,255,255,0.5);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .about-btn.active {
            background: rgba(255,255,255,0.4);
            border-color: rgba(255,255,255,0.6);
        }
        @media (max-width: 768px) {
            .content { padding: 20px; }
            .form-section { padding: 20px; }
            .header h1 { font-size: 2em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="position: absolute; top: 20px; right: 20px; display: flex; align-items: center; gap: 15px;">
                <button onclick="toggleTheme()" class="theme-btn" title="Toggle Dark/Light Theme">🌓</button>
                <button onclick="showAbout()" class="about-btn" title="About HSE Statistics Report">📚 About</button>
            </div>
            <img src="https://trojanconstruction.group/storage/subsidiaries/August2022/PG0Hzw1iVnUOQAiyYYuS.png" alt="Trojan Construction Group" style="height: 120px; margin-bottom: 20px; max-width: 90%; object-fit: contain;">
            <h1>HSE STATISTICS REPORT</h1>
            <p>Streamlined Data Management Interface</p>
        </div>
        <div class="content">
            <div class="table-selector" id="tableSelector">
                <!-- Table buttons will be populated by JavaScript -->
            </div>
            
            <div id="formContainer">
                <!-- Forms will be populated by JavaScript -->
            </div>
            
            <div id="aboutContainer" style="display: none;">
                <div class="form-section">
                    <h2>📚 About HSE Statistics Report</h2>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                        <h3>🏗️ Trojan Construction Group HSE Management</h3>
                        <p>A comprehensive Health, Safety & Environment statistics reporting system built with Python API client library for Airtable, providing wrappers around Airtable's REST API to simplify CRUD operations, filtering and pagination.</p>
                        
                        <h3>📜 License</h3>
                        <p>MIT license, permissive for both open and proprietary use.</p>
                        
                        <h3>✨ HSE Features</h3>
                        <ul>
                            <li>🏗️ Health, Safety & Environment data management</li>
                            <li>📊 Training & Competency Register tracking</li>
                            <li>📝 Dynamic form generation for HSE records</li>
                            <li>🔍 Smart field validation for safety compliance</li>
                            <li>💾 Streamlined incident and training reporting</li>
                            <li>🎯 Specialized training table optimizations</li>
                            <li>🔒 Secure data handling for sensitive HSE information</li>
                        </ul>
                        
                        <h3>🛠️ Built With</h3>
                        <ul>
                            <li>Python Flask - Web framework</li>
                            <li>pyairtable - Airtable API client</li>
                            <li>Gunicorn - WSGI HTTP Server</li>
                            <li>Modern HTML5/CSS3/JavaScript</li>
                        </ul>
                        
                        <div style="margin-top: 20px; padding: 15px; background: #e3f2fd; border-radius: 6px;">
                            <strong>🌐 Repository:</strong> <a href="https://github.com/s6ft256/airtablepy3" target="_blank" style="color: #1976d2; text-decoration: none;">github.com/s6ft256/airtablepy3</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
        </div>
    </div>

    <script>
        let currentTable = '';
        let tableSchemas = {};

        // Load tables and theme on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadTheme();
            loadTables();
        });

        async function loadTables() {
            showLoading(true);
            try {
                console.log('Fetching tables from /api/tables...');
                const response = await fetch('/api/tables');
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('Tables data received:', data);
                
                if (data.success) {
                    tableSchemas = data.schemas;
                    displayTableButtons(data.tables);
                    if (data.tables.length > 0) {
                        loadTable(data.tables[0].id, data.tables[0].name);
                    }
                } else {
                    console.error('API returned error:', data.error);
                    showMessage(data.error || 'Failed to load tables', 'error');
                }
            } catch (error) {
                console.error('Error loading tables:', error);
                const errorMessage = error.message || 'Unknown error occurred';
                showMessage(`Failed to connect to Airtable: ${errorMessage}`, 'error');
                
                // Show additional help for SSL errors
                if (errorMessage.includes('SSL') || errorMessage.includes('certificate')) {
                    showMessage('SSL Certificate issue detected. Please check environment variables.', 'error');
                }
            } finally {
                showLoading(false);
            }
        }

        function displayTableButtons(tables) {
            const selector = document.getElementById('tableSelector');
            const tableButtons = tables.map(table => {
                const escapedId = table.id.replace(/'/g, "\\'");
                const escapedName = table.name.replace(/'/g, "\\'");
                return `<a href="#" class="table-btn" onclick="loadTable('${escapedId}', '${escapedName}')">${table.name}</a>`;
            }).join('');
            
            selector.innerHTML = tableButtons;
        }

        async function loadTable(tableId, tableName) {
            currentTable = tableId;
            showLoading(true);
            
            // Update active button states
            document.querySelectorAll('.table-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.about-btn').forEach(btn => btn.classList.remove('active'));
            if (window.event && window.event.target) {
                window.event.target.classList.add('active');
            }
            
            // Hide about section
            document.getElementById('aboutContainer').style.display = 'none';
            
            try {
                const response = await fetch(`/api/form/${tableId}`);
                const data = await response.json();
                
                if (data.success) {
                    displayForm(data.form, tableName);
                } else {
                    showMessage(data.error || 'Failed to load form', 'error');
                }
            } catch (error) {
                console.error('Error loading form:', error);
                showMessage('Failed to load form', 'error');
            } finally {
                showLoading(false);
            }
        }

        function displayForm(formHtml, tableName) {
            // Hide about section and show form
            document.getElementById('aboutContainer').style.display = 'none';
            document.getElementById('formContainer').style.display = 'block';
            
            document.getElementById('formContainer').innerHTML = `
                <div class="form-section">
                    <h2>📝 Add New Record to ${tableName}</h2>
                    <div id="message" style="display: none;"></div>
                    <form onsubmit="submitForm(event)" id="dataForm">
                        ${formHtml}
                        <button type="submit" class="btn">💾 Save Record</button>
                    </form>
                </div>
            `;
        }

        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }
        
        function loadTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
        }

        function showAbout() {
            // Update active button states
            document.querySelectorAll('.table-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.about-btn').forEach(btn => btn.classList.add('active'));
            
            // Hide form and show about section
            document.getElementById('formContainer').style.display = 'none';
            document.getElementById('aboutContainer').style.display = 'block';
        }

        async function submitForm(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const data = {};
            
            // Convert FormData to object, handling multiple values for the same key
            for (let [key, value] of formData.entries()) {
                if (data[key]) {
                    if (!Array.isArray(data[key])) {
                        data[key] = [data[key]];
                    }
                    data[key].push(value);
                } else {
                    data[key] = value;
                }
            }
            
            showLoading(true);
            try {
                const response = await fetch(`/api/submit/${currentTable}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage('✅ Record saved successfully!', 'success');
                    document.getElementById('dataForm').reset();
                } else {
                    showMessage(`❌ Error: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error('Error submitting form:', error);
                showMessage('❌ Failed to save record', 'error');
            } finally {
                showLoading(false);
            }
        }

        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }

        function showMessage(message, type) {
            const messageDiv = document.getElementById('message');
            if (messageDiv) {
                messageDiv.className = type;
                messageDiv.textContent = message;
                messageDiv.style.display = 'block';
                
                // Auto-hide success messages
                if (type === 'success') {
                    setTimeout(() => {
                        messageDiv.style.display = 'none';
                    }, 5000);
                }
            } else {
                // Fallback: show alert if message div not found
                alert(`${type.toUpperCase()}: ${message}`);
                console.error('Message div not found, using alert fallback');
            }
        }
    </script>
</body>
</html>
"""

def get_field_type(field):
    """Determine the appropriate input type for a field"""
    field_type = field.get('type', 'singleLineText')
    
    type_mapping = {
        'singleLineText': 'text',
        'email': 'email',
        'url': 'url',
        'multilineText': 'textarea',
        'number': 'number',
        'currency': 'number',
        'percent': 'number',
        'date': 'date',
        'dateTime': 'datetime-local',
        'phoneNumber': 'tel',
        'singleSelect': 'select',
        'multipleSelects': 'select',
        'checkbox': 'checkbox',
        'rating': 'number',
        'richText': 'textarea'
    }
    
    return type_mapping.get(field_type, 'text')

def serialize_field_options(options):
    """Safely serialize field options to JSON-compatible format"""
    if options is None:
        return None
    
    try:
        # Handle different types of options objects
        if hasattr(options, '__dict__'):
            # Convert object to dict
            result = {}
            for key, value in options.__dict__.items():
                if not key.startswith('_'):  # Skip private attributes
                    try:
                        # Try to serialize the value
                        import json
                        json.dumps(value)  # Test if it's serializable
                        result[key] = value
                    except (TypeError, ValueError):
                        # If not serializable, convert to string
                        result[key] = str(value)
            return result
        elif isinstance(options, dict):
            return options
        else:
            return str(options)
    except Exception:
        return None

def should_exclude_field(field):
    """Check if field should be excluded from forms"""
    field_type = field.get('type', '')
    field_name = field.get('name', '').lower()
    
    # Exclude computed fields
    computed_types = [
        'formula', 'rollup', 'lookup', 'count', 'createdTime', 
        'lastModifiedTime', 'createdBy', 'lastModifiedBy', 'autoNumber'
    ]
    
    if field_type in computed_types:
        return True
        
    # Exclude auto-generated fields
    auto_fields = ['record id', 'id', 'created time', 'modified time']
    if any(auto in field_name for auto in auto_fields):
        return True
        
    return False

def generate_field_html(field, table_name):
    """Generate HTML for a form field"""
    if should_exclude_field(field):
        return ""
    
    field_name = field['name']
    field_type = get_field_type(field)
    field_id = f"field_{field_name.replace(' ', '_').replace('(', '').replace(')', '').replace('&', '')}"
    
    # Special handling for Training table - convert select fields to text
    is_training_table = 'training' in table_name.lower() and 'competency' in table_name.lower()
    if is_training_table and field_type == 'select':
        field_type = 'text'
    
    html_parts = [f'<div class="form-group">']
    html_parts.append(f'<label for="{field_id}">{field_name}</label>')
    
    if field_type == 'textarea':
        html_parts.append(f'<textarea id="{field_id}" name="{field_name}" rows="4"></textarea>')
    elif field_type == 'select' and not is_training_table:
        # Handle serialized options safely
        options = []
        field_options = field.get('options', {})
        if isinstance(field_options, dict):
            choices = field_options.get('choices', [])
            if isinstance(choices, list):
                options = choices
        
        html_parts.append(f'<select id="{field_id}" name="{field_name}">')
        html_parts.append('<option value="">-- Select an option --</option>')
        for option in options:
            if isinstance(option, dict):
                option_name = option.get('name', str(option))
            else:
                option_name = str(option)
            html_parts.append(f'<option value="{option_name}">{option_name}</option>')
        html_parts.append('</select>')
    elif field_type == 'checkbox':
        html_parts.append(f'<input type="checkbox" id="{field_id}" name="{field_name}" value="true">')
    elif field_type == 'number':
        step = '0.01' if field.get('type') in ['currency', 'percent'] else '1'
        html_parts.append(f'<input type="number" id="{field_id}" name="{field_name}" step="{step}">')
    else:
        html_parts.append(f'<input type="{field_type}" id="{field_id}" name="{field_name}">')
    
    html_parts.append('</div>')
    return ''.join(html_parts)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/test')
def test_connection():
    """Simple test endpoint"""
    return jsonify({
        'success': True,
        'message': 'API is working!',
        'token_set': bool(AIRTABLE_TOKEN),
        'base_id_set': bool(AIRTABLE_BASE_ID)
    })

@app.route('/api/tables')
def get_tables():
    """Get list of all tables and their schemas"""
    try:
        tables = []
        schemas = {}
        
        for table in base.schema().tables:
            table_info = {
                'id': table.id,
                'name': table.name
            }
            tables.append(table_info)
            
            # Store schema for form generation
            schemas[table.id] = {
                'name': table.name,
                'fields': [
                    {
                        'name': field.name,
                        'type': field.type,
                        'options': serialize_field_options(getattr(field, 'options', None))
                    }
                    for field in table.fields
                ]
            }
        
        return jsonify({
            'success': True,
            'tables': tables,
            'schemas': schemas
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/form/<table_id>')
def get_form(table_id):
    """Generate form HTML for a specific table"""
    try:
        table = base.table(table_id)
        schema = base.schema().table(table_id)
        
        form_html = []
        for field in schema.fields:
            field_dict = {
                'name': field.name,
                'type': field.type,
                'options': getattr(field, 'options', None)
            }
            field_html = generate_field_html(field_dict, schema.name)
            if field_html:
                form_html.append(field_html)
        
        return jsonify({
            'success': True,
            'form': ''.join(form_html)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/submit/<table_id>', methods=['POST'])
def submit_record(table_id):
    """Submit a new record to the specified table"""
    try:
        data = request.get_json()
        table = base.table(table_id)
        
        # Clean the data - remove empty values and handle special cases
        clean_data = {}
        for key, value in data.items():
            if value and str(value).strip():
                # Handle checkbox fields
                if value == 'true':
                    clean_data[key] = True
                elif value == 'false':
                    clean_data[key] = False
                else:
                    clean_data[key] = value
        
        if not clean_data:
            raise ValueError("No valid data provided")
        
        # Create the record
        record = table.create(clean_data)
        
        return jsonify({
            'success': True,
            'record_id': record['id'],
            'message': 'Record created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)