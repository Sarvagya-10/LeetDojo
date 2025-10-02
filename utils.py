import json
import os
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
import streamlit as st

def initialize_json_files():
    """Initialize JSON files if they don't exist"""
    
    # Initialize user_stats.json
    if not os.path.exists('user_stats.json'):
        default_stats = {
            "username": "Brother's Name",
            "xp": 0,
            "rank": "Artisan",
            "daily_streak": 0,
            "last_active_date": datetime.now().strftime("%Y-%m-%d"),
            "heatmap_data": {}
        }
        save_user_stats(default_stats)
    
    # Initialize user_progress.json
    if not os.path.exists('user_progress.json'):
        default_progress = {
            "completed_subtopics": [],
            "total_subtopics_practiced": 0
        }
        save_user_progress(default_progress)
    
    # Initialize saved_questions.json
    if not os.path.exists('saved_questions.json'):
        save_saved_questions([])

def load_syllabus():
    """Load syllabus from JSON file"""
    try:
        with open('syllabus.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("syllabus.json file not found. Please ensure it's in the project directory.")
        return {"syllabus": {}}

def load_user_stats():
    """Load user statistics from JSON file"""
    try:
        with open('user_stats.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_user_progress():
    """Load user progress from JSON file"""
    try:
        with open('user_progress.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_saved_questions():
    """Load saved questions from JSON file"""
    try:
        with open('saved_questions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_user_stats(stats):
    """Save user statistics to JSON file"""
    with open('user_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)

def save_user_progress(progress):
    """Save user progress to JSON file"""
    with open('user_progress.json', 'w') as f:
        json.dump(progress, f, indent=2)

def save_saved_questions(questions):
    """Save questions list to JSON file"""
    with open('saved_questions.json', 'w') as f:
        json.dump(questions, f, indent=2)

def update_stats(is_correct):
    """Update user statistics after answering a question"""
    stats = load_user_stats()
    
    # Update XP
    if is_correct:
        stats['xp'] += 10
    else:
        stats['xp'] += 5
    
    # Update heatmap data
    today = datetime.now().strftime("%Y-%m-%d")
    if today in stats['heatmap_data']:
        stats['heatmap_data'][today] += 1
    else:
        stats['heatmap_data'][today] = 1
    
    # Update streak
    last_active = datetime.strptime(stats['last_active_date'], "%Y-%m-%d")
    current_date = datetime.now()
    
    if (current_date - last_active).days == 1:
        # Consecutive day
        stats['daily_streak'] += 1
    elif (current_date - last_active).days > 1:
        # Streak broken
        stats['daily_streak'] = 1
    # If same day, keep streak as is
    
    stats['last_active_date'] = today
    save_user_stats(stats)

def update_progress(subtopic_name):
    """Update user progress after completing a subtopic"""
    progress = load_user_progress()
    
    if subtopic_name not in progress['completed_subtopics']:
        progress['completed_subtopics'].append(subtopic_name)
        progress['total_subtopics_practiced'] = len(progress['completed_subtopics'])
        save_user_progress(progress)

def check_for_rank_up():
    """Check if user should rank up and update rank if needed"""
    progress = load_user_progress()
    stats = load_user_stats()
    
    ranks = ["Artisan", "Peasant", "Ronin", "Samurai", "Daimyo", "Shogun", "Emperor", "Demigod", "Engineer"]
    
    # Check if eligible for rank up (every 10 subtopics)
    if progress['total_subtopics_practiced'] % 10 == 0 and progress['total_subtopics_practiced'] > 0:
        current_rank_index = ranks.index(stats['rank'])
        if current_rank_index < len(ranks) - 1:
            new_rank = ranks[current_rank_index + 1]
            stats['rank'] = new_rank
            save_user_stats(stats)
            return new_rank
    
    return None

def generate_question_from_api(subtopic_name):
    """Generate a question using Hugging Face API"""
    
    # Get API key from environment
    api_key = os.getenv("HUGGINGFACE_API_KEY", "default_key")
    
    # Construct the prompt
    prompt = f"""Generate a unique, JEE-Mains level multiple-choice question on the subtopic of '{subtopic_name}'. 
    Provide the question text, four distinct options (A, B, C, D) where only one is correct, 
    the letter of the correct option, and a detailed explanation. The explanation should describe 
    the solution step-by-step and also mention common pitfalls related to the incorrect options. 
    
    Format the output as a JSON object with the following structure:
    {{
        "question_text": "The actual question here",
        "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
        "correct_answer": "B. Option 2",
        "detailed_explanation": "Step-by-step explanation here"
    }}"""
    
    # Hugging Face API endpoint
    api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Try to parse the generated text as JSON
            try:
                # Extract JSON from the response
                generated_text = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
                
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
                
                if json_match:
                    question_data = json.loads(json_match.group())
                    return question_data
                else:
                    # Fallback: create a structured question
                    return create_fallback_question(subtopic_name)
                    
            except (json.JSONDecodeError, KeyError):
                return create_fallback_question(subtopic_name)
        
        else:
            st.error(f"API Error: {response.status_code}")
            return create_fallback_question(subtopic_name)
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return create_fallback_question(subtopic_name)

def create_fallback_question(subtopic_name):
    """Create a fallback question when API fails"""
    return {
        "question_text": f"Sample question for {subtopic_name}: What is the fundamental concept underlying this topic?",
        "options": [
            "A. Option 1 - Basic principle",
            "B. Option 2 - Advanced concept",
            "C. Option 3 - Related theory",
            "D. Option 4 - Alternative approach"
        ],
        "correct_answer": "A. Option 1 - Basic principle",
        "detailed_explanation": f"This is a sample question for {subtopic_name}. In a real scenario, this would contain a detailed step-by-step explanation of the concept, common mistakes students make, and how to avoid them. The explanation would also cover the fundamental principles underlying this subtopic and how it relates to other concepts in the syllabus."
    }

def create_activity_heatmap(heatmap_data):
    """Create a LeetCode-style activity heatmap"""
    
    # Generate dates for the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    dates = []
    values = []
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        dates.append(date_str)
        values.append(heatmap_data.get(date_str, 0))
        current_date += timedelta(days=1)
    
    # Create weeks data for proper heatmap layout
    weeks = []
    week_days = []
    week_values = []
    
    for i, (date, value) in enumerate(zip(dates, values)):
        day_of_week = datetime.strptime(date, "%Y-%m-%d").weekday()
        week_number = i // 7
        
        if len(weeks) <= week_number:
            weeks.extend([[] for _ in range(week_number - len(weeks) + 1)])
            week_days.extend([[] for _ in range(week_number - len(week_days) + 1)])
            week_values.extend([[] for _ in range(week_number - len(week_values) + 1)])
        
        weeks[week_number].append(date)
        week_days[week_number].append(day_of_week)
        week_values[week_number].append(value)
    
    # Create the heatmap using plotly
    fig = go.Figure()
    
    for week_idx, (week_dates, days, week_vals) in enumerate(zip(weeks, week_days, week_values)):
        for day_idx, (date, day, val) in enumerate(zip(week_dates, days, week_vals)):
            color_intensity = min(val / 5.0, 1.0) if val > 0 else 0  # Scale color based on activity
            color = f"rgba(0, 255, 65, {color_intensity})" if val > 0 else "rgba(100, 100, 100, 0.3)"
            
            fig.add_trace(go.Scatter(
                x=[week_idx],
                y=[6 - day],  # Reverse to match calendar layout
                mode='markers',
                marker=dict(
                    size=15,
                    color=color,
                    symbol='square',
                    line=dict(width=1, color='white')
                ),
                hovertemplate=f"Date: {date}<br>Questions: {val}<extra></extra>",
                showlegend=False
            ))
    
    # Update layout
    fig.update_layout(
        title="Activity Heatmap - Past Year",
        xaxis=dict(
            title="Weeks",
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            title="",
            showgrid=False,
            zeroline=False,
            tickvals=[0, 1, 2, 3, 4, 5, 6],
            ticktext=['Sun', 'Sat', 'Fri', 'Thu', 'Wed', 'Tue', 'Mon'],
            side='left'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=200,
        margin=dict(l=50, r=20, t=40, b=20)
    )
    
    return fig
