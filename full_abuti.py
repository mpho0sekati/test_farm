import streamlit as st
import datetime
import pandas as pd
import plotly.figure_factory as ff
import requests
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from gtts import gTTS
import os
import random
import csv
from io import StringIO

# Weather Icons
weather_icons = {
    "Clear": "🌞", "Clouds": "☁️", "Drizzle": "🌦️", "Rain": "🌧️",
    "Thunderstorm": "⛈️", "Snow": "❄️", "Mist": "🌫️", "Smoke": "🌫️",
    "Haze": "🌫️", "Dust": "🌫️", "Fog": "🌫️", "Sand": "🌫️",
    "Ash": "🌫️", "Squall": "🌫️", "Tornado": "🌪️"
}

# Define Google LLM for interacting with Google Calendar
llm = ChatGoogleGenerativeAI(model="gemini-pro", verbose=True, temperature=0.6, google_api_key="AIzaSyDjITo6JpwACzQKlMCJKuBhHHK8jTQIhBg")

# Define agents
farmer_agent = Agent(
    role='Farmer Agent',
    goal='Gather detailed planting information from the farmer',
    backstory='An agent specialized in interacting with farmers to gather comprehensive planting information.',
    verbose=True, allow_delegation=False, llm=llm
)

agronomist_agent = Agent(
    role='Agronomist Local Expert',
    goal='Provide personalized, step-by-step farming advice based on location and crop',
    backstory='An expert agronomist specialized in providing tailored farming advice for specific locations and crops.',
    verbose=True, allow_delegation=False, llm=llm
)

planner_agent = Agent(
    role='Amazing Planner Agent', 
    goal='Create a comprehensive, easy-to-follow planting calendar with detailed tasks and helpful tips',
    backstory='Expert farm planner with decades of experience in creating actionable, week-by-week planting schedules tailored to specific crops and locations.',
    verbose=True, allow_delegation=False, llm=llm
)

crop_suggestion_agent = Agent(
    role='Crop Suggestion Agent',
    goal='Suggest alternative crops if the entered crop is out of season or suggest complementary crops',
    backstory='An agent specialized in suggesting alternative or complementary crops based on seasonality, profitability, and sustainable farming practices in the local area.',
    verbose=True, allow_delegation=False, llm=llm
)

# Define tasks
planting_info_task = Task(
    description='Gather comprehensive planting information from the farmer for: {plant}',
    agent=farmer_agent,
    expected_output='Detailed planting information collected from the farmer.'
)

farming_advice_task = Task(
    description='Provide personalized, step-by-step farming advice for {crop} in {location} starting from {start_date}.',
    agent=agronomist_agent,
    expected_output='Detailed, personalized farming advice provided.'
)

farming_calendar_task = Task(
    description='''Generate a detailed, week-by-week farming calendar for {crop} in {location} starting from {start_date}. 
    Include specific dates, tasks, and helpful tips. Format each entry as:
    "YYYY-MM-DD: Task - Details - Tips"
    Cover the entire growing season, including preparation, planting, care, and harvest.''',
    agent=planner_agent, 
    expected_output='Detailed week-by-week farming calendar in CSV format.'
)

season_check_task = Task(
    description='Check if the planting season has ended for {crop} in {location} by {current_date}.',
    agent=agronomist_agent,
    expected_output='Planting season status checked with recommendations.'
)

crop_suggestion_task = Task(
    description='Suggest alternative or complementary crops for {crop} in {location} considering the current date {current_date} and sustainable farming practices.',
    agent=crop_suggestion_agent,
    expected_output='Alternative or complementary crops suggested with rationale.'
)

# Define crews
farming_crew_planting = Crew(
    agents=[farmer_agent, agronomist_agent, planner_agent, crop_suggestion_agent],
    tasks=[planting_info_task, farming_advice_task, farming_calendar_task, season_check_task, crop_suggestion_task],
    verbose=True, process=Process.sequential
)

# Function to create CSV
def create_csv(calendar_data):
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(['Date', 'Task', 'Details', 'Tips'])
    
    for entry in calendar_data:
        try:
            date, rest = entry.split(': ', 1)
            task, details, tips = rest.split(' - ', 2)
        except ValueError:
            # If the split doesn't work as expected, use a default format
            date = entry[:10]  # Assume YYYY-MM-DD format
            task = "Check your plan"
            details = "Review your farming plan"
            tips = "Contact support if you need help understanding this entry"
        
        writer.writerow([date.strip(), task.strip(), details.strip(), tips.strip()])
    
    return csv_buffer.getvalue()

# Streamlit App
st.set_page_config(page_title="AbutiSpinach: Your Farming Assistant", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for dark theme
st.markdown("""
    <style>
    .stApp {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stProgress .st-bo {
        background-color: #4CAF50;
    }
    .streamlit-expanderHeader {
        background-color: #2E2E2E;
        color: #FFFFFF;
    }
    .stTextInput>div>div>input {
        background-color: #3E3E3E;
        color: #FFFFFF;
    }
    .stSelectbox>div>div>select {
        background-color: #3E3E3E;
        color: #FFFFFF;
    }
    .stDateInput>div>div>input {
        background-color: #3E3E3E;
        color: #FFFFFF;
    }
    .reportview-container {
        background-color: #1E1E1E;
    }
    .sidebar .sidebar-content {
        background-color: #2E2E2E;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 AbutiSpinach: Your Smart Farming Assistant")
st.markdown("---")

# Motivational farming quotes
farming_quotes = [
    "The farmer is the only man in our economy who buys everything at retail, sells everything at wholesale, and pays the freight both ways. - John F. Kennedy",
    "Agriculture is our wisest pursuit, because it will in the end contribute most to real wealth, good morals, and happiness. - Thomas Jefferson",
    "Farming looks mighty easy when your plow is a pencil and you're a thousand miles from the corn field. - Dwight D. Eisenhower",
    "The ultimate goal of farming is not the growing of crops, but the cultivation and perfection of human beings. - Masanobu Fukuoka"
]

# Display a random motivational quote
st.info(random.choice(farming_quotes))

# Quick Tips Section
with st.expander("📚 Quick Farming Tips"):
    st.write("1. Rotate your crops to maintain soil health.")
    st.write("2. Implement integrated pest management for sustainable pest control.")
    st.write("3. Use mulch to conserve water and suppress weeds.")
    st.write("4. Monitor soil pH and adjust as needed for optimal nutrient uptake.")
    st.write("5. Consider companion planting to improve crop yield and pest resistance.")

# Gather planting information from the farmer
st.subheader("🌾 Let's Plan Your Farm!")

# Use columns for a more compact layout
col1, col2 = st.columns(2)

with col1:
    location = st.text_input("📍 Your Location:", placeholder="e.g., city, state, or country")
    crop = st.text_input("🌿 Crop to Plant:", placeholder="e.g., tomatoes, wheat")

with col2:
    start_date = st.date_input("🗓️ Planting Start Date:", min_value=datetime.date.today(), help="Select when you want to start planting")

# Add a progress bar for visual feedback
progress_bar = st.progress(0)

if st.button("🚀 Generate My Farming Plan"):
    if not location or not crop or not start_date:
        st.error("🚫 Oops! Please fill out all fields to get your personalized plan.")
    else:
        try:
            # Interpolate farmer's planting information into the tasks descriptions
            planting_info_task.interpolate_inputs({"plant": crop})
            farming_advice_task.interpolate_inputs({"crop": crop, "location": location, "start_date": start_date})
            farming_calendar_task.interpolate_inputs({"crop": crop, "location": location, "start_date": start_date})
            current_date = datetime.date.today()
            season_check_task.interpolate_inputs({"crop": crop, "location": location, "current_date": current_date})
            crop_suggestion_task.interpolate_inputs({"crop": crop, "location": location, "current_date": current_date})

            # Get weather information
            openweathermap_api_key = "bb7a7d944437ed1b8df2a27b54490cbb"
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={openweathermap_api_key}&units=metric"
            weather_response = requests.get(weather_url)
            weather_data = weather_response.json()

            # Display weather information
            if weather_data["cod"] != "404":
                st.subheader("☀️ Current Weather")
                weather_container = st.container()
                with weather_container:
                    cols = st.columns(4)
                    with cols[0]:
                        st.metric("Temperature", f"{weather_data['main']['temp']}°C", delta=None, delta_color="off")
                    with cols[1]:
                        st.metric("Humidity", f"{weather_data['main']['humidity']}%", delta=None, delta_color="off")
                    with cols[2]:
                        weather_condition = weather_data['weather'][0]['main']
                        weather_icon = weather_icons.get(weather_condition, "❓")
                        st.metric("Weather", f"{weather_icon} {weather_data['weather'][0]['description']}", delta=None, delta_color="off")
                    with cols[3]:
                        st.metric("Wind Speed", f"{weather_data['wind']['speed']} m/s", delta=None, delta_color="off")
                
                st.markdown("""
                    <style>
                    [data-testid="stMetricValue"] {
                        font-size: 20px;
                    }
                    [data-testid="stMetricLabel"] {
                        font-size: 16px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # Text to Speech - Weather Information
                tts_text_weather = f"Here's the current weather for {location}: Temperature is {weather_data['main']['temp']} degrees Celsius. Humidity is {weather_data['main']['humidity']} percent. Weather condition is {weather_data['weather'][0]['description']}. Wind Speed is {weather_data['wind']['speed']} meters per second."
                tts_filename_weather = "weather_info.mp3"
                tts_weather = gTTS(tts_text_weather, lang='en')
                tts_weather.save(tts_filename_weather)
                st.audio(tts_filename_weather, format='audio/mp3')
                os.remove(tts_filename_weather)  # Remove the audio file after playing
            else:
                st.warning(f"😕 Oops! We couldn't find weather information for {location}. Let's continue with your farming plan anyway!")

            # Execute the farming crew for planting calendar
            st.subheader("🌱 Your Personalized Farming Plan")
            calendar_data = []
            agent_outputs = {}

            for i, task in enumerate(farming_crew_planting.tasks):
                progress_bar.progress((i + 1) / len(farming_crew_planting.tasks))
                with st.spinner(f"🤖 Our {task.agent.role} is working on your plan..."):
                    output = task.execute()
                
                # Store outputs from all agents
                agent_outputs[task.agent.role] = output
                
                # Text to Speech - Agent Response
                tts_text_agent = f"Here's what our {task.agent.role} says: {output}"
                tts_filename_agent = f"agent_response_{task.agent.role.replace(' ', '_')}.mp3"
                tts_agent = gTTS(tts_text_agent, lang='en')
                tts_agent.save(tts_filename_agent)
                
                # Display output in an expander for cleaner UI
                with st.expander(f"💡 Advice from {task.agent.role}"):
                    st.write(output)
                    st.audio(tts_filename_agent, format='audio/mp3')
                
                os.remove(tts_filename_agent)  # Remove the audio file after playing

            # Generate the CSV planner
            planner_output = agent_outputs.get('Amazing Planner Agent', '')
            if planner_output:
                calendar_entries = planner_output.split('\n')
                csv_data = create_csv(calendar_entries)
                
                st.success("🎉 Your personalized farming plan is ready! Download and open the CSV file to see your detailed, week-by-week planting calendar.")
                
                # Add download button for CSV
                st.download_button(
                    label="📥 Download Your Detailed Planting Calendar (CSV)",
                    data=csv_data,
                    file_name="my_farming_calendar.csv",
                    mime="text/csv"
                )
                
                # Preview the calendar
                st.subheader("📆 Preview of Your Planting Calendar")
                df = pd.read_csv(StringIO(csv_data))
                st.dataframe(df.head(10))  # Show first 10 rows as a preview
                st.info("👆 This is just a preview. Download the full CSV for your complete planting calendar!")
            else:
                st.warning("We couldn't generate a CSV planner at this time. Please try again.")

            # Add a call-to-action button
            if st.button("📅 Save This Plan to My Calendar"):
                st.info("This feature is coming soon! We're working on integrating with popular calendar apps.")

        except Exception as e:
            st.error(f"😓 Oops! Something went wrong: {str(e)}. Please try again or contact support.")

st.markdown("---")
st.info("This is just a preview. Download the full CSV for your complete planting calendar!")
