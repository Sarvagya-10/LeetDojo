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
            "username": "GURU",
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

    # Initialize performance_analytics.json
    if not os.path.exists('performance_analytics.json'):
        default_analytics = {
            "question_history": [],
            "subtopic_stats": {},
            "chapter_stats": {},
            "subject_stats": {}
        }
        save_performance_analytics(default_analytics)

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

def load_performance_analytics():
    """Load performance analytics from JSON file"""
    # Define the default structure to ensure all keys are present
    default_analytics = {
        "question_history": [],
        "subtopic_stats": {},
        "chapter_stats": {},
        "subject_stats": {}
    }
    try:
        with open('performance_analytics.json', 'r') as f:
            data_from_file = json.load(f)
            # Ensure the loaded data is a dictionary before updating
            if isinstance(data_from_file, dict):
                default_analytics.update(data_from_file)
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is corrupt, the default structure will be used.
        pass

    return default_analytics

def save_performance_analytics(analytics):
    """Save performance analytics to JSON file"""
    with open('performance_analytics.json', 'w') as f:
        json.dump(analytics, f, indent=2)

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

def track_question_attempt(subtopic, chapter, subject, class_level, is_correct, difficulty="Medium"):
    """Track a question attempt for performance analytics"""
    analytics = load_performance_analytics()

    # Add to question history
    attempt = {
        "timestamp": datetime.now().isoformat(),
        "subtopic": subtopic,
        "chapter": chapter,
        "subject": subject,
        "class": class_level,
        "correct": is_correct,
        "difficulty": difficulty
    }
    analytics['question_history'].append(attempt)

    # Update subtopic stats
    if subtopic not in analytics['subtopic_stats']:
        analytics['subtopic_stats'][subtopic] = {"correct": 0, "total": 0}

    analytics['subtopic_stats'][subtopic]['total'] += 1
    if is_correct:
        analytics['subtopic_stats'][subtopic]['correct'] += 1

    # Update chapter stats
    if chapter not in analytics['chapter_stats']:
        analytics['chapter_stats'][chapter] = {"correct": 0, "total": 0}

    analytics['chapter_stats'][chapter]['total'] += 1
    if is_correct:
        analytics['chapter_stats'][chapter]['correct'] += 1

    # Update subject stats
    subject_key = f"{class_level}_{subject}"
    if subject_key not in analytics['subject_stats']:
        analytics['subject_stats'][subject_key] = {"correct": 0, "total": 0}

    analytics['subject_stats'][subject_key]['total'] += 1
    if is_correct:
        analytics['subject_stats'][subject_key]['correct'] += 1

    save_performance_analytics(analytics)

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
    """Generate a question using Google Gemini API (gemini-2.0-flash model)"""

    print(f"\n\n==== STARTING QUESTION GENERATION FOR: {subtopic_name} ====\n\n")

    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    # Import the Google Generative AI library
    try:
        import google.generativeai as genai
        print("Successfully imported google.generativeai")
    except ImportError:
        print("ERROR: Google Generative AI library not installed")
        st.warning("Google Generative AI library not installed. Using fallback question.")
        return create_fallback_question(subtopic_name)

    # Configure the Gemini API
    genai.configure(api_key=api_key)
    print("Configured Gemini API with key")

    # Construct the prompt for question generation only (without explanation)
    prompt = f"""Generate a JEE-Mains or easy JEE-Advanced  level multiple-choice question on '{subtopic_name}'.
Format the response exactly as follows:

Question: [question text]
A. [option A]
B. [option B]
C. [option C]
D. [option D]
Correct Answer: [letter of correct answer]

Do not include any explanation in this response."""

    print(f"Prompt for question generation:\n{prompt}\n")

    try:
        # Use the Gemini 2.0 Flash model
        print("Creating Gemini model instance (gemini-2.0-flash)")
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Generate content
        print("Sending request to Gemini API...")
        response = model.generate_content(prompt,
                                         generation_config={
                                             "temperature": 0.7,
                                             "top_p": 0.95,
                                             "max_output_tokens": 800,
                                         })

        if response:
            # Extract generated text
            generated_text = response.text
            print(f"\nGemini API Response:\n{generated_text}\n")

            # Parse the structured response
            print("Parsing generated question...")
            question_data = parse_generated_question(generated_text, subtopic_name)

            if question_data:
                print(f"Successfully parsed question data: {question_data}")

                # Store the question data without explanation
                question_without_explanation = question_data.copy()

                # Generate explanation separately
                print("Generating explanation...")
                explanation = generate_explanation(subtopic_name, question_data['question_text'],
                                                 question_data['options'], question_data['correct_answer'])

                # Add explanation to question data
                question_data['explanation'] = explanation
                print(f"Added explanation to question data")

                return question_data
            else:
                print("Failed to parse question data, using fallback question")
                return create_fallback_question(subtopic_name)

        else:
            print("ERROR: No response from Gemini API")
            st.warning("Failed to generate content from Gemini. Using fallback question.")
            return create_fallback_question(subtopic_name)

    except Exception as e:
        print(f"ERROR: Gemini API error: {str(e)}")
        st.warning(f"Gemini API error: {str(e)}. Using fallback question.")
        return create_fallback_question(subtopic_name)

def generate_explanation(subtopic_name, question, options, correct_answer):
    """Generate explanation for a question using Gemini API"""

    print(f"\n==== GENERATING EXPLANATION FOR QUESTION ====\n")

    # Hardcoded API key
    api_key = "AIzaSyBneCrd4X5c1aaiaoQ3_BbN5vOE5Lptcus"
    print(f"Using API key for explanation: {api_key}")

    try:
        import google.generativeai as genai
        print("Successfully imported google.generativeai for explanation")

        # Configure the Gemini API if not already configured
        genai.configure(api_key=api_key)
        print("Configured Gemini API for explanation")

        # Construct options text
        options_text = ""
        for i, option in enumerate(options):
            options_text += f"{chr(65+i)}. {option}\n"

        # Construct the prompt for explanation generation
        prompt = f"""For the following JEE-Mains level multiple-choice question on '{subtopic_name}', provide a detailed explanation of why the correct answer is {correct_answer}.

Question: {question}
{options_text}
Correct Answer: {correct_answer}

Provide a clear, step-by-step explanation of why this is the correct answer. Include relevant formulas, concepts, and calculations where appropriate. Also include what are the common pitfalls to avoid while solving this type of question. """

        print(f"Prompt for explanation generation:\n{prompt}\n")

        # Use the Gemini 2.0 Flash model
        print("Creating Gemini model instance for explanation (gemini-2.0-flash)")
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Generate content
        print("Sending explanation request to Gemini API...")
        response = model.generate_content(prompt,
                                         generation_config={
                                             "temperature": 0.3,  # Lower temperature for more factual response
                                             "top_p": 0.95,
                                             "max_output_tokens": 1000,
                                         })

        if response:
            explanation = response.text
            print(f"\nExplanation response received, length: {len(explanation)} characters")
            print(f"Explanation snippet: {explanation[:100]}...")
            return explanation
        else:
            print("ERROR: No explanation response from Gemini API")
            return "No explanation available."

    except Exception as e:
        print(f"ERROR: Explanation generation error: {str(e)}")
        return f"Could not generate explanation: {str(e)}"

def parse_generated_question(text, subtopic_name):
    """Parse generated question text into structured format"""
    import re

    print(f"\n==== PARSING GENERATED QUESTION ====\n")
    print(f"Raw text to parse:\n{text}\n")

    try:
        # Try to extract question components using regex
        lines = text.split('\n')
        question_text = ""
        options = []
        correct_answer = ""
        explanation = ""

        current_section = None
        print("Parsing question by sections...")

        for line in lines:
            line = line.strip()

            if line.startswith(('Question:', 'Q:')):
                current_section = 'question'
                print(f"Found question section: {line}")
                question_text = line.split(':', 1)[1].strip() if ':' in line else ""
            elif re.match(r'^[A-D][.\):]', line):
                 current_section = 'options'
                 print(f"Found option: {line}")
                 options.append(line)
            elif line.startswith(('Correct Answer:', 'Answer:', 'Correct:')):
                current_section = 'answer'
                print(f"Found correct answer section: {line}")
                answer_text = line.split(':', 1)[1].strip() if ':' in line else ""
                # Extract the letter
                match = re.search(r'[A-D]', answer_text.upper())
                if match:
                    correct_letter = match.group()
                    correct_answer = correct_letter
                    print(f"Extracted correct letter: {correct_answer}")
            elif line.startswith(('Explanation:', 'Solution:')):
                current_section = 'explanation'
                print(f"Found explanation section: {line}")
                explanation = line.split(':', 1)[1].strip() if ':' in line else ""
            elif current_section == 'question' and line:
                question_text += " " + line
                print(f"Added to question: {line}")
            elif current_section == 'explanation' and line:
                explanation += " " + line
                print(f"Added to explanation: {line}")

        # Validate parsed data
        print(f"\nValidation check:\nQuestion: {bool(question_text)}\nOptions: {len(options)}\nCorrect answer: {bool(correct_answer)}")

        if question_text and len(options) == 4 and correct_answer:
            result = {
                "question_text": question_text.strip(),
                "options": [re.split(r'^[A-D][.\):]\s*', opt)[-1].strip() for opt in options],
                "correct_answer": correct_answer.strip(),
                "subtopic": subtopic_name
            }
            print(f"Successfully parsed question data: {result}")
            return result

        print("Failed validation, returning None")
        return None

    except Exception as e:
        print(f"ERROR: Exception while parsing question: {str(e)}")
        return None


def create_fallback_question(subtopic_name):
    """Create a fallback question when API fails"""
    return {
        "question_text": f"Sample question for {subtopic_name}: What is the fundamental concept underlying this topic?",
        "options": [
            "Option 1 - Basic principle",
            "Option 2 - Advanced concept",
            "Option 3 - Related theory",
            "Option 4 - Alternative approach"
        ],
        "correct_answer": "A",
        "explanation": f"This is a sample question for {subtopic_name}. In a real scenario, this would contain a detailed step-by-step explanation of the concept, common mistakes students make, and how to avoid them. The explanation would also cover the fundamental principles underlying this subtopic and how it relates to other concepts in the syllabus.",
        "subtopic": subtopic_name
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
