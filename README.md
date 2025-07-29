# QBO Report Scheduler

A simple Flask web application for scheduling automated QuickBooks Online Balance Sheet reports.

## Architecture

This application follows a simple Flask-based architecture:

- **Frontend**: HTML templates rendered by Flask with clean, user-friendly interface
- **Backend**: Python Flask web application that handles OAuth, job scheduling, and report generation
- **Two Entry Points**: Web interface for user setup + scheduled job runner for automation

## Features

### User Interface (Flask Templates)
- **Step 1**: QuickBooks OAuth login with connection status
- **Step 2**: Email and schedule configuration with existing job display
- **Modern UI**: Clean, responsive design with loading states and error handling

### Backend (Python Flask)
- **OAuth Management**: Complete QuickBooks OAuth 2.0 flow
- **Job Scheduling**: Configure automated report generation
- **Report Generation**: Query QBO Balance Sheet API and format reports
- **Email Integration**: Send formatted reports via email
- **Token Management**: Automatic token refresh and persistence

## Quick Start

### Simple Setup

```bash
# Run the build and start script
./build_and_run.sh
```

This will:
1. Set up the Python environment
2. Install dependencies
3. Start the Flask server on `http://localhost:5001`

### Manual Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Flask server
python3 app.py
```

The application will run on `http://localhost:5001`

### 3. Configure QuickBooks (Sandbox)

1. **Create Sandbox Company**: Go to [Intuit Developer Sandbox](https://developer.intuit.com/app/developer/qbo/docs/develop/sandboxes)
2. **Verify App Settings**: Ensure your Intuit app is configured for Sandbox environment
3. **Redirect URI**: Make sure `http://localhost:5001/` is listed in your app's Redirect URIs

## Usage

### User Flow

1. **Open Application**: Navigate to `http://localhost:5001`
2. **Connect QuickBooks**: Click "Connect QuickBooks" button
3. **Authorize**: Complete OAuth flow in browser
4. **Configure Job**: Enter email and schedule time
5. **Schedule**: Click "Schedule Report" to save configuration
6. **Success**: See confirmation message

### Automated Reports

The backend handles automated report generation:

```bash
# Run scheduled jobs manually
python backend/app.py run-jobs
```

## File Structure

```
qbo/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── auth_manager.py        # OAuth token management
│   ├── report_manager.py      # Report generation and scheduling
│   ├── qbo.py                # QuickBooks API client
│   ├── requirements.txt       # Python dependencies
│   ├── templates/
│   │   └── index.html        # Main web interface
│   ├── data/                 # Data storage
│   │   ├── qbo_tokens.json   # OAuth tokens
│   │   └── qbo_jobs.json     # Job configurations
│   └── venv/                 # Python virtual environment
├── build_and_run.sh          # Setup and run script
├── README.md                 # This file
└── CREDENTIALS.md           # Credential configuration
```

## Web Routes

### Main Pages
- `GET /` - Main application page
- `POST /connect` - Initiate QuickBooks OAuth
- `GET /callback` - OAuth callback handler
- `POST /configure` - Configure job schedule
- `POST /next` - Move to next step

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
python app.py
```

## Production Deployment

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### Scheduled Jobs
```bash
# Cron job (recommended)
*/5 * * * * /usr/bin/python3 /path/to/backend/app.py run-jobs

# Or systemd timer
sudo systemctl enable qbo-reports.timer
```

## Configuration

### Environment Variables
Create `.env` file in backend directory:

```env
CLIENT_ID=your_quickbooks_client_id
CLIENT_SECRET=your_quickbooks_client_secret
FLASK_ENV=production
```

### Email Configuration
Update email settings in `backend/app.py`:

```python
# Configure your email service (SendGrid, AWS SES, etc.)
def send_email_report(email, realm_id, report_data):
    # Implement your email service here
    pass
```

## Security

- OAuth tokens stored securely in JSON files
- Automatic token refresh handling
- Input validation and error handling

## Troubleshooting

### Common Issues

1. **OAuth Errors**: Check CLIENT_ID and CLIENT_SECRET
2. **Token Expired**: Backend handles automatic refresh
3. **Email Not Sending**: Implement email service in `send_email_report`

### Logs
Check backend console for API logs and error messages.

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

MIT License - see LICENSE file for details. 