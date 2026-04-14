# CreatorReach

A full-stack Python Flask application that discovers small but active YouTube creators for video editing client outreach.

## Features

- **Channel Discovery**: Search YouTube by keywords to find relevant channels
- **Smart Filtering**: Automatically filters channels by subscriber count (500-50K), upload frequency, and engagement
- **Lead Scoring**: Calculates activity scores based on upload frequency, engagement ratio, and growth signals
- **Social Extraction**: Automatically extracts Instagram, Twitter, LinkedIn, website links, and email addresses from channel descriptions
- **AI Enrichment**: Classifies channel niches and generates tags like "high potential" or "needs consistency"
- **Lead Management**: Approve, reject, and export leads to CSV
- **Modern Dashboard**: Clean Vercel-inspired UI with filters and pagination

## Tech Stack

- **Backend**: Flask, Flask-SQLAlchemy, Flask-CORS
- **Database**: SQLite
- **APIs**: YouTube Data API v3, Optional OpenAI/Claude integration
- **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript

## Project Structure

```
.
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── services/
│   ├── __init__.py
│   ├── youtube_service.py      # YouTube API integration
│   ├── analyzer.py             # Lead filtering & scoring logic
│   ├── scraper.py              # Social link extraction
│   └── ai_enrichment.py        # AI-powered niche classification
├── templates/
│   └── dashboard.html          # Main dashboard UI
└── instance/
    └── leads.db                # SQLite database (auto-created)
```

## Setup Instructions

### 1. Clone and Navigate to Project

```bash
cd youtube-lead-generator
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **YouTube Data API v3**
4. Create credentials (API Key)
5. Copy the API key

### 5. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API keys
YOUTUBE_API_KEY=your_youtube_api_key_here
```

Optional API keys for AI enrichment:
```bash
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### 6. Run the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

## Usage

### Dashboard

Open your browser and navigate to `http://localhost:5000`

### Search for Channels

1. Click **"Search Channels"** button
2. Enter a keyword (e.g., "gaming", "study vlog", "tech reviews")
3. Select max results (20, 50, or 100)
4. Click **Search**

The app will:
- Search YouTube for relevant videos
- Extract unique channels
- Filter channels by criteria (500-50K subs, recent uploads, engagement > 0.1)
- Analyze and score each channel
- Extract social links and contact info
- Save leads to the database

### Manage Leads

- **Filter**: Use filters for subscriber range, niche, status, and activity score
- **Approve/Reject**: Click checkmark to approve, X to reject
- **View Details**: Click the eye icon to see full channel information
- **Export**: Click **Export CSV** to download leads

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard UI |
| POST | `/api/search` | Search and add new leads |
| GET | `/api/leads` | Get leads with filters & pagination |
| GET | `/api/leads/<id>` | Get single lead details |
| PUT | `/api/leads/<id>` | Update lead status |
| DELETE | `/api/leads/<id>` | Delete a lead |
| POST | `/api/leads/<id>/approve` | Approve lead |
| POST | `/api/leads/<id>/reject` | Reject lead |
| GET | `/api/leads/export` | Export leads to CSV |
| GET | `/api/stats` | Get lead statistics |

## Filtering Logic

Channels are automatically filtered based on:

- **Subscriber Count**: 500 to 50,000 (sweet spot for video editing clients)
- **Video Count**: At least 5 videos
- **Recent Uploads**: Uploaded within last 14 days
- **Engagement Ratio**: Average views / subscribers > 0.1

## Scoring System

**Activity Score (0-100)** is calculated from:
- **Upload Frequency Score (30%)**: How often they upload
- **Engagement Score (40%)**: Views and engagement ratio
- **Growth Signal (30%)**: Recent performance vs older videos

## AI Enrichment Tags

The system automatically tags leads with:
- **"high potential"** - High activity and engagement
- **"needs consistency"** - Irregular upload schedule
- **"low editing quality"** - Basic indicators in titles/descriptions
- **"consistent uploader"** - Regular upload schedule
- **"high production value"** - Professional indicators

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `YOUTUBE_API_KEY` | Yes | YouTube Data API key |
| `OPENAI_API_KEY` | No | OpenAI API for AI enrichment |
| `ANTHROPIC_API_KEY` | No | Anthropic Claude API for AI enrichment |
| `FLASK_ENV` | No | Set to `development` for debug mode |
| `FLASK_DEBUG` | No | Set to `True` for auto-reload |

## Notes

- The YouTube API has quota limits (10,000 units/day for free tier)
- Each search costs 100 units, channel details cost 1 unit per channel
- The app filters at the API level when possible to save quota
- SQLite database is stored in `instance/leads.db`

## License

MIT License
