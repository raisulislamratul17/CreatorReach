import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import csv
import io

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///leads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db = SQLAlchemy(app)

from services.youtube_service import YouTubeService
from services.analyzer import LeadAnalyzer
from services.scraper import SocialScraper
from services.ai_enrichment import AIEnrichment

youtube_service = YouTubeService()
analyzer = LeadAnalyzer()
scraper = SocialScraper()
ai_enrichment = AIEnrichment()


class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String(255), unique=True, nullable=False)
    channel_name = db.Column(db.String(255), nullable=False)
    channel_url = db.Column(db.String(500), nullable=False)
    subscriber_count = db.Column(db.Integer, nullable=False)
    total_videos = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    recent_videos = db.Column(db.JSON, nullable=True)
    avg_views = db.Column(db.Integer, nullable=True)
    engagement_ratio = db.Column(db.Float, nullable=True)
    upload_frequency_score = db.Column(db.Float, nullable=True)
    engagement_score = db.Column(db.Float, nullable=True)
    growth_signal = db.Column(db.Float, nullable=True)
    activity_score = db.Column(db.Float, nullable=True)
    niche = db.Column(db.String(100), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, nullable=True)
    instagram = db.Column(db.String(255), nullable=True)
    twitter = db.Column(db.String(255), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(500), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'channel_name': self.channel_name,
            'channel_url': self.channel_url,
            'subscriber_count': self.subscriber_count,
            'total_videos': self.total_videos,
            'description': self.description,
            'recent_videos': self.recent_videos,
            'avg_views': self.avg_views,
            'engagement_ratio': self.engagement_ratio,
            'upload_frequency_score': self.upload_frequency_score,
            'engagement_score': self.engagement_score,
            'growth_signal': self.growth_signal,
            'activity_score': self.activity_score,
            'niche': self.niche,
            'summary': self.summary,
            'tags': self.tags,
            'instagram': self.instagram,
            'twitter': self.twitter,
            'linkedin': self.linkedin,
            'website': self.website,
            'email': self.email,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/search', methods=['POST'])
def search_channels():
    data = request.get_json()
    keyword = data.get('keyword', '')
    max_results = data.get('max_results', 50)
    
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400
    
    try:
        # Fetch channels from YouTube API
        channels_data = youtube_service.search_channels(keyword, max_results)
        
        leads_created = 0
        for channel_data in channels_data:
            # Check if lead already exists
            existing = Lead.query.filter_by(channel_id=channel_data['channel_id']).first()
            if existing:
                continue
            
            # Analyze the channel
            analyzed_data = analyzer.analyze_channel(channel_data)
            if not analyzed_data:
                continue
            
            # Extract social links
            social_data = scraper.extract_social_links(channel_data.get('description', ''))
            
            # AI enrichment (optional)
            try:
                ai_data = ai_enrichment.enrich_channel(
                    channel_data.get('description', ''),
                    channel_data.get('recent_videos', [])
                )
            except Exception as e:
                ai_data = {'niche': 'Unknown', 'summary': '', 'tags': []}
            
            # Create lead
            lead = Lead(
                channel_id=channel_data['channel_id'],
                channel_name=channel_data['channel_name'],
                channel_url=channel_data['channel_url'],
                subscriber_count=channel_data['subscriber_count'],
                total_videos=channel_data['total_videos'],
                description=channel_data.get('description', ''),
                recent_videos=channel_data.get('recent_videos', []),
                avg_views=analyzed_data.get('avg_views'),
                engagement_ratio=analyzed_data.get('engagement_ratio'),
                upload_frequency_score=analyzed_data.get('upload_frequency_score'),
                engagement_score=analyzed_data.get('engagement_score'),
                growth_signal=analyzed_data.get('growth_signal'),
                activity_score=analyzed_data.get('activity_score'),
                niche=ai_data.get('niche', 'Unknown'),
                summary=ai_data.get('summary', ''),
                tags=ai_data.get('tags', []),
                instagram=social_data.get('instagram'),
                twitter=social_data.get('twitter'),
                linkedin=social_data.get('linkedin'),
                website=social_data.get('website'),
                email=social_data.get('email')
            )
            
            db.session.add(lead)
            leads_created += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'leads_created': leads_created,
            'message': f'Found and added {leads_created} new leads'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/leads', methods=['GET'])
def get_leads():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filters
    min_subs = request.args.get('min_subscribers', type=int)
    max_subs = request.args.get('max_subscribers', type=int)
    niche = request.args.get('niche')
    min_activity = request.args.get('min_activity_score', type=float)
    status = request.args.get('status')
    
    query = Lead.query
    
    if min_subs is not None:
        query = query.filter(Lead.subscriber_count >= min_subs)
    if max_subs is not None:
        query = query.filter(Lead.subscriber_count <= max_subs)
    if niche:
        query = query.filter(Lead.niche.ilike(f'%{niche}%'))
    if min_activity is not None:
        query = query.filter(Lead.activity_score >= min_activity)
    if status:
        query = query.filter(Lead.status == status)
    
    # Order by activity score desc
    query = query.order_by(Lead.activity_score.desc().nullslast())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'leads': [lead.to_dict() for lead in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@app.route('/api/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    return jsonify(lead.to_dict())


@app.route('/api/leads/<int:lead_id>', methods=['PUT'])
def update_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json()
    
    if 'status' in data:
        lead.status = data['status']
    
    db.session.commit()
    
    return jsonify(lead.to_dict())


@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    
    return jsonify({'message': 'Lead deleted successfully'})


@app.route('/api/leads/<int:lead_id>/approve', methods=['POST'])
def approve_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    lead.status = 'approved'
    db.session.commit()
    
    return jsonify(lead.to_dict())


@app.route('/api/leads/<int:lead_id>/reject', methods=['POST'])
def reject_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    lead.status = 'rejected'
    db.session.commit()
    
    return jsonify(lead.to_dict())


@app.route('/api/leads/export', methods=['GET'])
def export_leads():
    status = request.args.get('status')
    
    query = Lead.query
    if status:
        query = query.filter(Lead.status == status)
    
    leads = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Channel Name', 'Channel URL', 'Subscribers', 'Total Videos', 'Niche',
        'Activity Score', 'Engagement Ratio', 'Email', 'Instagram', 'Twitter',
        'LinkedIn', 'Website', 'Status', 'Summary'
    ])
    
    for lead in leads:
        writer.writerow([
            lead.channel_name,
            lead.channel_url,
            lead.subscriber_count,
            lead.total_videos,
            lead.niche,
            lead.activity_score,
            lead.engagement_ratio,
            lead.email,
            lead.instagram,
            lead.twitter,
            lead.linkedin,
            lead.website,
            lead.status,
            lead.summary
        ])
    
    output.seek(0)
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=leads.csv'}
    )


@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_leads = Lead.query.count()
    pending_leads = Lead.query.filter_by(status='pending').count()
    approved_leads = Lead.query.filter_by(status='approved').count()
    rejected_leads = Lead.query.filter_by(status='rejected').count()
    
    # Get niche distribution
    from sqlalchemy import func
    niche_counts = db.session.query(
        Lead.niche, func.count(Lead.id)
    ).group_by(Lead.niche).all()
    
    return jsonify({
        'total_leads': total_leads,
        'pending_leads': pending_leads,
        'approved_leads': approved_leads,
        'rejected_leads': rejected_leads,
        'niche_distribution': {niche: count for niche, count in niche_counts}
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
