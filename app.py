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
if 'challenge_mode' not in st.session_state:
    st.session_state.challenge_mode = False
if 'challenge_start_time' not in st.session_state:
    st.session_state.challenge_start_time = None
if 'challenge_time_limit' not in st.session_state:
    st.session_state.challenge_time_limit = 300  # 5 minutes default

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
        progress_percentage = (user_progress['total_subtopics_practiced'] / total_subtopics) * 100 if total_subtopics > 0 else 0
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

    # Analytics and Challenge buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Performance Analytics", use_container_width=True):
            st.session_state.current_view = 'analytics'
            st.rerun()

    with col2:
        if st.button("⏱️ Timed Challenge", type="primary", use_container_width=True):
            st.session_state.current_view = 'challenge_setup'
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
    # Check if challenge mode
    if st.session_state.challenge_mode:
        st.title("⏱️ Timed Challenge")

        # Calculate remaining time
        elapsed = (datetime.now() - st.session_state.challenge_start_time).total_seconds()
        remaining = max(0, st.session_state.challenge_time_limit - elapsed)

        # Check if time's up
        if remaining == 0:
            st.error("⏰ Time's up! Challenge complete!")
            st.session_state.challenge_mode = False
            st.session_state.current_view = 'dashboard'
            st.rerun()

        # Display timer
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        timer_color = "red" if remaining < 60 else "orange" if remaining < 180 else "green"

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"### Time Remaining: :{timer_color}[{minutes:02d}:{seconds:02d}]")
        with col2:
            st.metric("Progress", f"{st.session_state.current_question_index + 1}/{st.session_state.challenge_num_questions}")
        with col3:
            if st.button("End Challenge"):
                st.session_state.challenge_mode = False
                st.session_state.current_view = 'dashboard'
                st.rerun()

        # Auto-refresh for timer
        import time
        time.sleep(1)
        st.rerun()
    else:
        st.title("⚔️ The Forge - Battle Arena")

        if st.button("← Back to Dojo"):
            st.session_state.current_view = 'dojo'
            st.rerun()

    st.divider()

    # Get current subtopic (from challenge or regular mode)
    if st.session_state.challenge_mode:
        total_questions = st.session_state.challenge_num_questions
        current_subtopic_data = st.session_state.challenge_subtopics[st.session_state.current_question_index]
        current_subtopic = current_subtopic_data['subtopic']
        current_chapter = current_subtopic_data['chapter']
        current_subject = current_subtopic_data['subject']
        current_class = current_subtopic_data['class']
    else:
        total_questions = 3
        current_subtopic = st.session_state.selected_subtopic
        current_chapter = st.session_state.selected_chapter
        current_subject = st.session_state.selected_subject
        current_class = st.session_state.selected_class

    # Display progress
    progress_text = f"Question {st.session_state.current_question_index + 1} of {total_questions}"
    st.subheader(f"📖 {progress_text}")
    st.markdown(f"**Subtopic:** {current_subtopic}")

    # Progress bar for questions
    st.progress((st.session_state.current_question_index + 1) / total_questions)

    st.divider()

    # Generate or load current question
    if len(st.session_state.questions) <= st.session_state.current_question_index:
        with st.spinner("Get ready, next problem incoming..."):
            try:
                question_data = generate_question_from_api(current_subtopic)
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
            # --- START: RECTIFIED LOGIC ---
            options = current_question['options']
            user_answer = st.session_state.user_answer
            api_correct_answer = current_question['correct_answer']

            # Find the full text of the correct answer from the options list.
            # This handles cases where the API gives a letter ('C') or the full text.
            correct_answer_full_text = None
            if api_correct_answer in options:
                correct_answer_full_text = api_correct_answer
            else:
                # Assuming the API gives a letter like 'A', 'B', 'C'.
                try:
                    correct_letter = api_correct_answer.strip().upper()[0]
                    # Case 1: Option is prefixed like "C. Answer"
                    found_by_prefix = False
                    for opt in options:
                        if opt.strip().upper().startswith(correct_letter):
                            correct_answer_full_text = opt
                            found_by_prefix = True
                            break
                    # Case 2: Options are not prefixed. Assume A=0, B=1, ...
                    if not found_by_prefix:
                        correct_idx = ord(correct_letter) - ord('A')
                        if 0 <= correct_idx < len(options):
                            correct_answer_full_text = options[correct_idx]
                except Exception:
                    # If conversion fails, we cannot determine the correct answer.
                    pass

            # Now, perform a direct string comparison for correctness
            is_correct = (user_answer == correct_answer_full_text)

            # Get indices for display formatting
            user_index = options.index(user_answer) if user_answer in options else None
            correct_index = options.index(correct_answer_full_text) if correct_answer_full_text in options else None

            def format_option(option, idx):
                if idx == user_index and idx == correct_index:
                    return f"✅ {option} (Your Answer - Correct)"
                elif idx == user_index and idx != correct_index:
                    return f"❌ {option} (Your Answer)"
                elif idx == correct_index:
                    return f"✅ {option} (Correct Answer)"
                else:
                    return option

            formatted_options = [format_option(opt, i) for i, opt in enumerate(options)]

            st.radio(
                "Your answer:",
                formatted_options,
                index=user_index if user_index is not None else 0,
                disabled=True,
                key=f"disabled_answer_{st.session_state.current_question_index}"
            )

            if is_correct:
                st.success("🎉 Correct! Well done, warrior!")
            else:
                st.error("❌ Incorrect! But every mistake is a lesson learned.")
                # Show the full correct answer text if available
                if correct_answer_full_text:
                    st.info(f"The correct answer was: **{correct_answer_full_text}**")
                else:
                    # Fallback if we couldn't determine it
                    st.info(f"The provided correct answer was: **{api_correct_answer}**")

            # Show explanation
            st.markdown("### 📚 Detailed Explanation")
            st.markdown(current_question['explanation'])
            # --- END: RECTIFIED LOGIC ---

            # Update stats and track only once per question
            question_key = f"{current_subtopic}_{st.session_state.current_question_index}"
            if question_key not in st.session_state.question_tracked:
                update_stats(is_correct)

                # Track question attempt for analytics
                track_question_attempt(
                    subtopic=current_subtopic,
                    chapter=current_chapter,
                    subject=current_subject,
                    class_level=current_class,
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
                last_question = st.session_state.current_question_index >= (total_questions - 1)

                if not last_question:
                    if st.button("➡️ Next Question", type="primary"):
                        st.session_state.current_question_index += 1
                        st.session_state.question_submitted = False
                        st.session_state.user_answer = None
                        st.rerun()
                else:
                    button_text = "🏆 Finish Challenge" if st.session_state.challenge_mode else "🏆 Finish Forging"
                    if st.button(button_text, type="primary"):
                        # In regular mode, complete the subtopic
                        if not st.session_state.challenge_mode:
                            update_progress(current_subtopic)
                            rank_up = check_for_rank_up()

                            if rank_up:
                                st.balloons()
                                st.success(f"🎊 Congratulations! You've been promoted to {rank_up}!")

                            st.session_state.subtopic_completed = True
                            st.success("🎯 Subtopic completed! Returning to the Dojo...")
                            st.session_state.current_view = 'dojo'
                        else:
                            # Challenge mode complete
                            st.balloons()
                            st.success("🎊 Challenge Complete!")
                            st.session_state.challenge_mode = False
                            st.session_state.current_view = 'dashboard'

                        # Reset for next session
                        st.session_state.current_question_index = 0
                        st.session_state.questions = []
                        st.session_state.question_submitted = False
                        st.rerun()

def show_challenge_setup():
    """Display challenge mode setup"""
    st.title("⏱️ Timed Challenge - Exam Simulation")

    if st.button("← Back to Dashboard"):
        st.session_state.current_view = 'dashboard'
        st.rerun()

    st.divider()

    st.markdown("""
    **Challenge Mode** simulates exam conditions with:
    - ⏱️ Countdown timer
    - 🎯 Random questions from selected topics
    - 📊 Final score and performance report
    - 🚫 No hints or explanations until completion
    """)

    st.divider()

    # Challenge configuration
    st.subheader("⚙️ Configure Challenge")

    col1, col2 = st.columns(2)

    with col1:
        num_questions = st.selectbox(
            "Number of Questions",
            [5, 10, 15, 20, 25],
            index=1
        )

        time_limit = st.selectbox(
            "Time Limit",
            [("3 minutes", 180), ("5 minutes", 300), ("10 minutes", 600), ("15 minutes", 900), ("20 minutes", 1200)],
            format_func=lambda x: x[0],
            index=1
        )

    with col2:
        subject_filter = st.selectbox(
            "Subject",
            ["All Subjects", "Physics", "Chemistry", "Maths"]
        )

        class_filter = st.selectbox(
            "Class",
            ["Both Classes", "11th", "12th"]
        )

    st.divider()

    if st.button("🚀 Start Challenge", type="primary", use_container_width=True):
        # Initialize challenge
        st.session_state.challenge_mode = True
        st.session_state.challenge_start_time = datetime.now()
        st.session_state.challenge_time_limit = time_limit[1]
        st.session_state.challenge_num_questions = num_questions
        st.session_state.challenge_subject = subject_filter
        st.session_state.challenge_class = class_filter
        st.session_state.current_view = 'forge'
        st.session_state.current_question_index = 0
        st.session_state.questions = []
        st.session_state.question_submitted = False
        st.session_state.question_tracked = {}

        # Select random subtopics based on filters
        import random

        available_subtopics = []
        for class_key, class_data in syllabus['syllabus'].items():
            if class_filter != "Both Classes":
                if class_filter == "11th" and class_key != "class_11":
                    continue
                if class_filter == "12th" and class_key != "class_12":
                    continue

            for subject_key, subject_data in class_data.items():
                if subject_filter != "All Subjects" and subject_key != subject_filter.lower():
                    continue

                for chapter in subject_data['chapters']:
                    for subtopic in chapter['subtopics']:
                        available_subtopics.append({
                            'subtopic': subtopic,
                            'chapter': chapter['chapter_name'],
                            'subject': subject_key.capitalize(),
                            'class': class_key.replace('class_', '') + 'th'
                        })

        # Select random subtopics
        if available_subtopics and len(available_subtopics) >= num_questions:
            selected = random.sample(available_subtopics, num_questions)
        elif available_subtopics:
            selected = available_subtopics * (num_questions // len(available_subtopics) + 1)
            selected = selected[:num_questions]
        else:
            st.error("No subtopics available for the selected filters. Please adjust your challenge settings.")
            return

        st.session_state.challenge_subtopics = selected
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
                'subject': subject_key.replace('_', ' - ').capitalize(),
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

    saved_questions = load_saved_questions()

    if not saved_questions:
        st.info("No saved questions yet. Start practicing to save interesting questions!")
        return

    st.markdown(f"**Total Saved Questions:** {len(saved_questions)}")

    for i, question in enumerate(saved_questions):
        with st.expander(f"Question {i + 1}: {question.get('question_text', 'N/A')[:100]}..."):
            st.markdown("**Question:**")
            st.markdown(question.get('question_text', 'N/A'))

            st.markdown("**Options:**")
            options = question.get('options', [])
            correct_answer_text = question.get('correct_answer', '')
            
            # Find the full correct answer text if the stored answer is just a letter
            correct_answer_full = correct_answer_text
            if len(correct_answer_text.strip()) == 1:
                for opt in options:
                    if opt.strip().upper().startswith(correct_answer_text.strip().upper()):
                        correct_answer_full = opt
                        break
            
            for option in options:
                if option == correct_answer_full:
                    st.markdown(f"✅ **{option}** (Correct Answer)")
                else:
                    st.markdown(f"• {option}")

            st.markdown("**Explanation:**")
            explanation = question.get('explanation') or question.get('detailed_explanation', 'No explanation available.')
            st.markdown(explanation)

            st.divider()
            if st.button("🗑️ Remove", key=f"remove_q_{i}"):
                saved_questions.pop(i)
                save_saved_questions(saved_questions)
                st.rerun()

# Main app logic
def main():
    """Main function to run the Streamlit app."""
    # Custom CSS for dark theme (minimal styling)
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Route to appropriate view
    view_map = {
        'dashboard': show_dashboard,
        'dojo': show_dojo,
        'forge': show_forge,
        'challenge_setup': show_challenge_setup,
        'analytics': show_analytics,
        'saved_questions': show_saved_questions
    }

    view_function = view_map.get(st.session_state.current_view, show_dashboard)
    view_function()

if __name__ == "__main__":
    main()
