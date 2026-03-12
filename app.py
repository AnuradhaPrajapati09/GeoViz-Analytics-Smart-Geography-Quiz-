import streamlit as st
import pandas as pd
import plotly.express as px
import random
import os
from db_manager import init_db, update_user_stat, get_all_stats, log_attempt, get_history_log, get_profile_stats
from data_loader import load_country_data

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title=" GeoViz Analytics", layout="wide", page_icon="🌍")

def local_css(file_name):
    """Loads a local CSS file and injects it into the Streamlit app."""
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize DB and Load CSS
init_db()
local_css("style.css")

st.markdown("""
<div class="main-header">
    <h1>🌍 GeoViz Analytics</h1>
    <p style="color: #E0E7FF !important; margin-top: 5px;">Advanced Geospatial Analytics & Learning</p>
</div>
""", unsafe_allow_html=True)

# --- 2. LOGIC FUNCTIONS ---

def show_atlas(df):
    st.markdown("### 📖 World Explorer")
    mode = st.radio("Mode:", ["Single View", "Comparison Mode"], horizontal=True)
    
    if mode == "Comparison Mode":
        st.info("Select up to 3 countries to compare.")
        countries = st.multiselect("Select Countries", sorted(df["country"].unique()), max_selections=3)
        
        if countries:
            subset = df[df["country"].isin(countries)].set_index("country")
            st.dataframe(subset[["capital", "population", "continent", "area", "currency-code"]], use_container_width=True)
            
            cols = st.columns(len(countries))
            for i, country in enumerate(countries):
                row = subset.loc[country]
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"### {country}")
                        st.metric("Population", f"{row['population']:,}")
                        st.metric("Capital", row['capital'])
                        st.caption(f"Currency: {row.get('currency-code', 'N/A')}")
            
            fig = px.choropleth(df[df["country"].isin(countries)], locations="iso3", color="country", projection="natural earth")
            fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        col1, col2 = st.columns([1, 3])
        with col1:
            with st.container(border=True):
                country = st.selectbox("Search Country", sorted(df["country"].unique()))
                info = df[df["country"] == country].iloc[0]
                
                st.divider()
                st.markdown(f"**🏛 Capital:** {info.get('capital', 'N/A')}")
                st.markdown(f"**👥 Population:** {info.get('population', 0):,}")
                st.markdown(f"**📍 Continent:** {info.get('continent', 'N/A')}")
                st.markdown(f"**💰 Currency:** {info.get('currency-code', 'N/A')}")

        with col2:
            df_map = df.copy()
            df_map['color'] = df_map['country'].apply(lambda x: 'Target' if x == country else 'Rest')
            
            lat, lon = info.get('latitude'), info.get('longitude')
            geo_config = dict(showframe=False, showcoastlines=False, projection_type='natural earth')
            
            if pd.notnull(lat) and pd.notnull(lon):
                geo_config.update(center=dict(lat=lat, lon=lon), projection_scale=6)

            fig = px.choropleth(
                df_map, locations="iso3", color="color",
                color_discrete_map={'Target': '#00695C', 'Rest': '#E9ECEF'},
                hover_name="country", hover_data={"capital": True, "population": True, "continent": True, "iso3": False, "color": False}
            )
            fig.update_layout(showlegend=False, margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', geo=geo_config)
            st.plotly_chart(fig, use_container_width=True)

def show_quiz(df):
    st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>🗺️ Global Mastery Challenge</h3>", unsafe_allow_html=True)
    
    diff = st.select_slider("Select Difficulty", options=["Easy", "Hard"])
    quiz_df = df.copy()
    if diff == "Easy":
        quiz_df = quiz_df[quiz_df['population'] > 10000000]
    
    with st.container(border=True):
        col_quiz, col_map = st.columns([1, 1])
        
        with col_quiz:
            if "quiz_country" not in st.session_state:
                st.session_state.quiz_country = quiz_df.sample(1).iloc[0]
                correct = st.session_state.quiz_country["country"]
                wrong = quiz_df[quiz_df["country"] != correct].sample(3)["country"].tolist()
                options = wrong + [correct]
                random.shuffle(options)
                
                st.session_state.quiz_options = options
                st.session_state.quiz_answered = False
                st.session_state.quiz_result = None

            target = st.session_state.quiz_country
            st.markdown("#### ❓ Question")
            st.info(f"Which country has the capital: **{target['capital']}**?")

            choice = st.radio("Select Answer:", st.session_state.quiz_options, disabled=st.session_state.quiz_answered)
            st.markdown("<br>", unsafe_allow_html=True)
            
            b_col1, b_col2 = st.columns([2, 1])
            
            with b_col1:
                if st.button("Lock In Answer 🔐", use_container_width=True, disabled=st.session_state.quiz_answered):
                    st.session_state.quiz_answered = True
                    is_correct = (choice == target["country"])
                    st.session_state.quiz_result = is_correct
                    update_user_stat(target.get("continent", "Unknown"), is_correct)
                    log_attempt(target["country"], choice, target["country"], is_correct)
                    st.rerun()

            with b_col2:
                if st.button("Skip ⏭️", use_container_width=True, disabled=st.session_state.quiz_answered):
                    del st.session_state.quiz_country
                    st.rerun()

            if st.session_state.quiz_answered:
                if st.session_state.quiz_result:
                    st.success(f"✅ Correct! It is **{target['country']}**.")
                else:
                    st.error(f"❌ Incorrect. The answer is **{target['country']}**.")
                
                if st.button("Next Round ➡️", type="primary", use_container_width=True):
                    del st.session_state.quiz_country
                    st.rerun()

        with col_map:
            st.markdown("#### 🌏 Live Tracker")
            if not st.session_state.quiz_answered:
                fig = px.choropleth(locations=[], projection="natural earth")
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=350, geo=dict(showframe=False, showcoastlines=True, showland=True, landcolor="#f0f2f6"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                df_map = df.copy()
                df_map['color'] = df_map['country'].apply(lambda x: 'Correct' if x == target['country'] else 'Rest')
                lat, lon = target.get('latitude'), target.get('longitude')
                geo_config = dict(showframe=False, showcoastlines=False, projection_type='natural earth')
                
                if pd.notnull(lat) and pd.notnull(lon):
                    geo_config.update(center=dict(lat=lat, lon=lon), projection_scale=5) 
                
                fig = px.choropleth(df_map, locations="iso3", color="color", color_discrete_map={'Correct': '#00C853', 'Rest': '#E0E0E0'}, projection="natural earth")
                fig.update_layout(showlegend=False, margin={"r":0,"t":0,"l":0,"b":0}, height=350, geo=geo_config)
                st.plotly_chart(fig, use_container_width=True)

def show_performance(df):
    st.markdown("### 📊 Analytics Dashboard")
    tab_stats, tab_history = st.tabs(["Global Heatmap", "Attempt History"])
    
    with tab_stats:
        stats = get_all_stats()
        if not stats:
            st.warning("No data yet. Play the quiz!")
        else:
            accuracy_map = {cont: (d['correct'] / d['attempts'] * 100) for cont, d in stats.items() if d['attempts'] > 0}
            df["user_accuracy"] = df["continent"].map(accuracy_map).fillna(0)
            
            total_attempts = sum(d['attempts'] for d in stats.values())
            total_correct = sum(d['correct'] for d in stats.values())
            global_acc = (total_correct / total_attempts * 100) if total_attempts > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Questions", total_attempts)
            c2.metric("Accuracy Score", f"{global_acc:.1f}%")
            if accuracy_map:
                weakest = min(accuracy_map, key=accuracy_map.get)
                c3.metric("Focus Area", weakest, f"{accuracy_map[weakest]:.1f}%", delta_color="inverse")
            
            fig = px.choropleth(df, locations="iso3", color="user_accuracy", color_continuous_scale="RdYlGn", range_color=[0, 100], projection="natural earth", title="Global Knowledge Heatmap")
            fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)

    with tab_history:
        st.markdown("### 📜 Recent Activity Log")
        history_df = get_history_log()
        if history_df.empty:
            st.info("No attempts recorded yet.")
        else:
            st.dataframe(history_df, use_container_width=True, hide_index=True)

# --- 3. MAIN NAVIGATION ---
df = load_country_data()
tab1, tab2, tab3, tab4 = st.tabs(["Atlas", "Quiz", "Performance", "Profile"])

with tab1: show_atlas(df)
with tab2: show_quiz(df)
with tab3: show_performance(df)
def show_profile():
    """Display user profile with stats and achievements."""
    st.markdown("### 👤 Explorer Profile")
    
    # Get profile statistics
    stats = get_profile_stats()
    
    # Determine user level based on total games
    total_games = stats['total_games']
    accuracy = stats['best_accuracy']
    
    if total_games == 0:
        level = "Novice Explorer"
        level_emoji = "🗺️"
    elif total_games < 20:
        level = "Curious Wanderer"
        level_emoji = "🧭"
    elif total_games < 50:
        level = "Skilled Navigator"
        level_emoji = "⛵"
    elif total_games < 100:
        level = "World Traveler"
        level_emoji = "✈️"
    elif accuracy >= 80:
        level = "Global Master"
        level_emoji = "🏆"
    else:
        level = "Geography Expert"
        level_emoji = "🌟"
    
    # Profile Header Section
    st.markdown(f"""
    <div class="profile-header">
        <div class="profile-avatar">
            <div class="avatar-circle">🌍</div>
        </div>
        <div class="profile-info">
            <h2 class="profile-name">GeoQuest Explorer</h2>
            <div class="profile-level">
                <span class="level-badge">{level_emoji} {level}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Stats Grid
    st.markdown("#### 📊 Performance Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.metric("Total Games Played", stats['total_games'])
            st.caption("Questions answered")
    
    with col2:
        with st.container(border=True):
            st.metric("Best Accuracy", f"{stats['best_accuracy']:.1f}%")
            st.caption("Correct answers rate")
    
    with col3:
        with st.container(border=True):
            st.metric("Focus Region", stats['most_visited_continent'])
            st.caption("Most practiced continent")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Additional Stats Row
    st.markdown("#### 🎯 Progress Metrics")
    col4, col5, col6 = st.columns(3)
    
    with col4:
        with st.container(border=True):
            st.metric("Current Streak", f"{stats['current_streak']} 🔥")
            st.caption("Consecutive correct answers")
    
    with col5:
        with st.container(border=True):
            st.metric("Best Streak", stats['best_streak'])
            st.caption("Personal record")
    
    with col6:
        with st.container(border=True):
            st.metric("Countries Explored", stats['unique_countries'])
            st.caption("Unique countries attempted")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Achievements Section
    st.markdown("#### 🏅 Earned Badges")
    
    # Calculate which achievements are earned
    achievements = []
    
    if stats['total_games'] >= 10:
        achievements.append(("🎯", "First Steps", "Completed 10 games"))
    if stats['total_games'] >= 50:
        achievements.append(("🌟", "Dedicated Learner", "Completed 50 games"))
    if stats['total_games'] >= 100:
        achievements.append(("💎", "Century Club", "Completed 100 games"))
    
    if stats['best_accuracy'] >= 90:
        achievements.append(("🏆", "Perfectionist", "Achieved 90%+ accuracy"))
    if stats['best_accuracy'] >= 80:
        achievements.append(("⭐", "High Achiever", "Achieved 80%+ accuracy"))
    
    if stats['best_streak'] >= 5:
        achievements.append(("🔥", "Hot Streak", "5 correct in a row"))
    if stats['best_streak'] >= 10:
        achievements.append(("⚡", "Unstoppable", "10 correct in a row"))
    if stats['best_streak'] >= 15:
        achievements.append(("💫", "Legendary", "15 correct in a row"))
    
    if stats['perfect_scores'] >= 1:
        achievements.append(("🎊", "Perfect Day", "Flawless performance"))
    
    if stats['unique_countries'] >= 25:
        achievements.append(("🗺️", "Explorer", "Attempted 25+ countries"))
    if stats['unique_countries'] >= 50:
        achievements.append(("🌍", "Globetrotter", "Attempted 50+ countries"))
    if stats['unique_countries'] >= 100:
        achievements.append(("🌎", "World Scholar", "Attempted 100+ countries"))
    
    # Display achievements
    if achievements:
        # Create rows of 4 badges each
        achievement_cols = st.columns(4)
        for idx, (emoji, title, desc) in enumerate(achievements):
            with achievement_cols[idx % 4]:
                st.markdown(f"""
                <div class="achievement-badge">
                    <div class="achievement-emoji">{emoji}</div>
                    <div class="achievement-title">{title}</div>
                    <div class="achievement-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🎮 Start playing to unlock achievements!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Progress to Next Level
    st.markdown("#### 📈 Level Progress")
    next_milestone = 20 if total_games < 20 else 50 if total_games < 50 else 100 if total_games < 100 else 200
    progress = min(total_games / next_milestone, 1.0)
    
    st.progress(progress)
    remaining = max(0, next_milestone - total_games)
    st.caption(f"Play {remaining} more games to reach the next level!")

with tab4: show_profile()