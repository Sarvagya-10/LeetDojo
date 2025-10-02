import streamlit as st
import json
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from utils import (
    initialize_json_files, load_syllabus, load_user_stats, load_user_progress, 
    load_saved_questions, save_user_stats, save_user_progress, save_saved_questions,
    update_stats, update_progress, check_for_rank_up, generate_question_from_api,
    create_activity_heatmap, track_question_attempt, load_performance_analytics
)

# Page configuration
st.set_page_config(
    page_title="LeetDojo - The Engineer's RPG",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'
if 'selected_class' not in st.session_state:
    st.session_state.selected_class = None
if 'selected_subject' not in st.session_state:
    st.session_state.selected_subject = None
if 'selected_chapter' not in st.session_state:
    st.session_state.selected_chapter = None
if 'selected_subtopic' not in st.session_state:
    st.session_state.selected_subtopic = None
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = None
if 'question_submitted' not in st.session_state:
    st.session_state.question_submitted = False
if 'subtopic_completed' not in st.session_state:
    st.session_state.subtopic_completed = False
if 'question_tracked' not in st.session_state:
    st.session_state.question_tracked = {}

# Initialize JSON files
initialize_json_files()

# Load data
syllabus = load_syllabus()
user_stats = load_user_stats()
user_progress = load_user_progress()
saved_questions = load_saved_questions()

def show_dashboard():
    """Display the main dashboard view"""
    st.title("⚔️ LeetDojo - The Engineer's RPG")
    
    # Header with username and rank
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"## Welcome, {user_stats['username']}!")
    with col2:
        st.markdown(f"### Rank: {user_stats['rank']}")
    
    st.divider()
    
    # Stats display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total XP", user_stats['xp'])
    
    with col2:
        st.metric("Current Streak", f"{user_stats['daily_streak']} days")
    
    with col3:
        # Calculate total subtopics from syllabus
        total_subtopics = sum(
            len(chapter['subtopics']) 
            for class_data in syllabus['syllabus'].values() 
            for subject_data in class_data.values() 
            for chapter in subject_data['chapters']
        )
        progress_percentage = (user_progress['total_subtopics_practiced'] / total_subtopics) * 100
        st.metric("Overall Progress", f"{progress_percentage:.1f}%")
    
    with col4:
        st.metric("Subtopics Completed", user_progress['total_subtopics_practiced'])
    
    # Progress bar
    st.progress(progress_percentage / 100)
    
    st.divider()
    
    # Activity Heatmap
    st.subheader("📊 Activity Heatmap")
    heatmap_fig = create_activity_heatmap(user_stats['heatmap_data'])
    st.plotly_chart(heatmap_fig, use_container_width=True)
    
    st.divider()
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🥋 Enter the Dojo", type="primary", use_container_width=True):
            st.session_state.current_view = 'dojo'
            st.rerun()
    
    with col2:
        if st.button("📚 View Saved Questions", use_container_width=True):
            st.session_state.current_view = 'saved_questions'
            st.rerun()
    
    # Analytics button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Performance Analytics", use_container_width=True):
            st.session_state.current_view = 'analytics'
            st.rerun()

def show_dojo():
    """Display the topic selection view"""
    st.title("🥋 The Dojo - Topic Selection")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_view = 'dashboard'
        st.rerun()
    
    st.divider()
    
    # Hierarchical dropdowns
    col1, col2 = st.columns(2)
    
    with col1:
        # Class selection
        classes = ["11th", "12th"]
        selected_class = st.selectbox("Select Class", classes, key="class_select")
        st.session_state.selected_class = selected_class
        
        # Subject selection
        if selected_class:
            subjects = ["Physics", "Chemistry", "Maths"]
            selected_subject = st.selectbox("Select Subject", subjects, key="subject_select")
            st.session_state.selected_subject = selected_subject
    
    with col2:
        # Chapter selection
        if st.session_state.selected_subject:
            class_key = f"class_{st.session_state.selected_class.replace('th', '')}"
            subject_key = st.session_state.selected_subject.lower()
            
            if class_key in syllabus['syllabus'] and subject_key in syllabus['syllabus'][class_key]:
                chapters = [chapter['chapter_name'] for chapter in syllabus['syllabus'][class_key][subject_key]['chapters']]
                selected_chapter = st.selectbox("Select Chapter", chapters, key="chapter_select")
                st.session_state.selected_chapter = selected_chapter
                
                # Subtopic selection
                if selected_chapter:
                    # Find the selected chapter
                    chapter_data = None
                    for chapter in syllabus['syllabus'][class_key][subject_key]['chapters']:
                        if chapter['chapter_name'] == selected_chapter:
                            chapter_data = chapter
                            break
                    
                    if chapter_data:
                        # Add completion indicators
                        subtopic_options = []
                        for subtopic in chapter_data['subtopics']:
                            if subtopic in user_progress['completed_subtopics']:
                                subtopic_options.append(f"✅ {subtopic}")
                            else:
                                subtopic_options.append(subtopic)
                        
                        selected_subtopic_display = st.selectbox("Select Subtopic", subtopic_options, key="subtopic_select")
                        
                        # Extract actual subtopic name (remove emoji if present)
                        if selected_subtopic_display:
                            selected_subtopic = selected_subtopic_display.replace("✅ ", "")
                            st.session_state.selected_subtopic = selected_subtopic
    
    st.divider()
    
    # Start button
    if st.session_state.selected_subtopic:
        st.info(f"Ready to practice: **{st.session_state.selected_subtopic}**")
        
        if st.button("⚔️ Begin Forging", type="primary", use_container_width=True):
            st.session_state.current_view = 'forge'
            st.session_state.current_question_index = 0
            st.session_state.questions = []
            st.session_state.question_submitted = False
            st.session_state.subtopic_completed = False
            st.session_state.question_tracked = {}  # Reset tracking for new session
            st.rerun()

def show_forge():
    """Display the problem-solving view"""
    st.title("⚔️ The Forge - Battle Arena")
    
    if st.button("← Back to Dojo"):
        st.session_state.current_view = 'dojo'
        st.rerun()
    
    st.divider()
    
    # Display progress
    progress_text = f"Question {st.session_state.current_question_index + 1} of 3"
    st.subheader(f"📖 {progress_text}")
    st.markdown(f"**Subtopic:** {st.session_state.selected_subtopic}")
    
    # Progress bar for questions
    st.progress((st.session_state.current_question_index + 1) / 3)
    
    st.divider()
    
    # Generate or load current question
    if len(st.session_state.questions) <= st.session_state.current_question_index:
        with st.spinner("🔮 Generating question from the mystical APIs..."):
            try:
                question_data = generate_question_from_api(st.session_state.selected_subtopic)
                st.session_state.questions.append(question_data)
            except Exception as e:
                st.error(f"Failed to generate question: {str(e)}")
                if st.button("Try Again"):
                    st.rerun()
                return
    
    # Display current question
    if st.session_state.questions:
        current_question = st.session_state.questions[st.session_state.current_question_index]
        
        # Question text
        st.markdown("### 🎯 Question")
        st.markdown(current_question['question_text'])
        
        # Options
        if not st.session_state.question_submitted:
            st.session_state.user_answer = st.radio(
                "Select your answer:",
                current_question['options'],
                key=f"answer_{st.session_state.current_question_index}"
            )
            
            if st.button("Submit Answer", type="primary"):
                st.session_state.question_submitted = True
                st.rerun()
        
        else:
            # Show submitted answer and result
            st.radio(
                "Your answer:",
                current_question['options'],
                index=current_question['options'].index(st.session_state.user_answer),
                disabled=True,
                key=f"disabled_answer_{st.session_state.current_question_index}"
            )
            
            # Check if answer is correct
            is_correct = st.session_state.user_answer == current_question['correct_answer']
            
            if is_correct:
                st.success("🎉 Correct! Well done, warrior!")
            else:
                st.error("❌ Incorrect! But every mistake is a lesson learned.")
                st.info(f"The correct answer was: **{current_question['correct_answer']}**")
            
            # Show explanation
            st.markdown("### 📚 Detailed Explanation")
            st.markdown(current_question['detailed_explanation'])
            
            # Update stats and track only once per question
            question_key = f"{st.session_state.selected_subtopic}_{st.session_state.current_question_index}"
            if question_key not in st.session_state.question_tracked:
                update_stats(is_correct)
                
                # Track question attempt for analytics
                track_question_attempt(
                    subtopic=st.session_state.selected_subtopic,
                    chapter=st.session_state.selected_chapter,
                    subject=st.session_state.selected_subject,
                    class_level=st.session_state.selected_class,
                    is_correct=is_correct
                )
                
                st.session_state.question_tracked[question_key] = True
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save Question"):
                    saved_questions = load_saved_questions()
                    saved_questions.append(current_question)
                    save_saved_questions(saved_questions)
                    st.success("Question saved!")
            
            with col2:
                if st.session_state.current_question_index < 2:
                    if st.button("➡️ Next Question", type="primary"):
                        st.session_state.current_question_index += 1
                        st.session_state.question_submitted = False
                        st.session_state.user_answer = None
                        st.rerun()
                else:
                    if st.button("🏆 Finish Forging", type="primary"):
                        # Complete the subtopic
                        update_progress(st.session_state.selected_subtopic)
                        rank_up = check_for_rank_up()
                        
                        if rank_up:
                            st.balloons()
                            st.success(f"🎊 Congratulations! You've been promoted to {rank_up}!")
                        
                        st.session_state.subtopic_completed = True
                        st.success("🎯 Subtopic completed! Returning to the Dojo...")
                        
                        # Reset for next session
                        st.session_state.current_view = 'dojo'
                        st.session_state.current_question_index = 0
                        st.session_state.questions = []
                        st.session_state.question_submitted = False
                        st.rerun()

def show_analytics():
    """Display performance analytics and weak areas"""
    st.title("📊 Performance Analytics")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_view = 'dashboard'
        st.rerun()
    
    st.divider()
    
    analytics = load_performance_analytics()
    
    if not analytics['question_history']:
        st.info("No data yet. Start practicing to see your performance analytics!")
        return
    
    # Overall Statistics
    st.subheader("📈 Overall Statistics")
    total_questions = len(analytics['question_history'])
    correct_questions = sum(1 for q in analytics['question_history'] if q['correct'])
    accuracy = (correct_questions / total_questions * 100) if total_questions > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions Attempted", total_questions)
    with col2:
        st.metric("Correct Answers", correct_questions)
    with col3:
        st.metric("Overall Accuracy", f"{accuracy:.1f}%")
    
    st.divider()
    
    # Weak Areas Identification
    st.subheader("🎯 Weak Areas (Topics to Focus On)")
    
    # Calculate accuracy for each area
    weak_chapters = []
    for chapter, stats in analytics['chapter_stats'].items():
        if stats['total'] >= 3:  # Only consider chapters with at least 3 questions
            chapter_accuracy = (stats['correct'] / stats['total'] * 100)
            if chapter_accuracy < 70:  # Weak if < 70% accuracy
                weak_chapters.append({
                    'chapter': chapter,
                    'accuracy': chapter_accuracy,
                    'correct': stats['correct'],
                    'total': stats['total']
                })
    
    weak_chapters.sort(key=lambda x: x['accuracy'])
    
    if weak_chapters:
        st.markdown("**Chapters with accuracy below 70%:**")
        for i, chapter in enumerate(weak_chapters[:10], 1):  # Show top 10
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"{i}. **{chapter['chapter']}**")
            with col2:
                st.markdown(f"{chapter['correct']}/{chapter['total']}")
            with col3:
                color = "red" if chapter['accuracy'] < 50 else "orange"
                st.markdown(f":{color}[{chapter['accuracy']:.1f}%]")
    else:
        st.success("Great job! No weak areas identified. Keep up the good work!")
    
    st.divider()
    
    # Subject-wise Performance
    st.subheader("📚 Subject-wise Performance")
    
    subject_data = []
    for subject_key, stats in analytics['subject_stats'].items():
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total'] * 100)
            subject_data.append({
                'subject': subject_key.replace('_', ' - '),
                'accuracy': accuracy,
                'correct': stats['correct'],
                'total': stats['total']
            })
    
    if subject_data:
        subject_data.sort(key=lambda x: x['accuracy'], reverse=True)
        
        for subject in subject_data:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.progress(subject['accuracy'] / 100)
                st.markdown(f"**{subject['subject']}**: {subject['correct']}/{subject['total']} correct")
            with col2:
                st.metric("Accuracy", f"{subject['accuracy']:.1f}%")
    
    st.divider()
    
    # Recent Activity
    st.subheader("🕒 Recent Activity")
    recent_questions = analytics['question_history'][-10:][::-1]  # Last 10, reversed
    
    for i, q in enumerate(recent_questions, 1):
        status_icon = "✅" if q['correct'] else "❌"
        timestamp = datetime.fromisoformat(q['timestamp']).strftime("%Y-%m-%d %H:%M")
        
        with st.expander(f"{status_icon} {q['subtopic']} - {timestamp}"):
            st.markdown(f"**Subject:** {q['subject']}")
            st.markdown(f"**Chapter:** {q['chapter']}")
            st.markdown(f"**Result:** {'Correct' if q['correct'] else 'Incorrect'}")

def show_saved_questions():
    """Display saved questions view"""
    st.title("📚 Saved Questions")
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_view = 'dashboard'
        st.rerun()
    
    st.divider()
    
    if not saved_questions:
        st.info("No saved questions yet. Start practicing to save interesting questions!")
        return
    
    st.markdown(f"**Total Saved Questions:** {len(saved_questions)}")
    
    for i, question in enumerate(saved_questions):
        with st.expander(f"Question {i + 1}: {question['question_text'][:100]}..."):
            st.markdown("**Question:**")
            st.markdown(question['question_text'])
            
            st.markdown("**Options:**")
            for option in question['options']:
                if option == question['correct_answer']:
                    st.markdown(f"✅ **{option}** (Correct Answer)")
                else:
                    st.markdown(f"• {option}")
            
            st.markdown("**Explanation:**")
            st.markdown(question['detailed_explanation'])

# Main app logic
def main():
    # Custom CSS for dark theme (minimal styling)
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Route to appropriate view
    if st.session_state.current_view == 'dashboard':
        show_dashboard()
    elif st.session_state.current_view == 'dojo':
        show_dojo()
    elif st.session_state.current_view == 'forge':
        show_forge()
    elif st.session_state.current_view == 'analytics':
        show_analytics()
    elif st.session_state.current_view == 'saved_questions':
        show_saved_questions()

if __name__ == "__main__":
    main()
