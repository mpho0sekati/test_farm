import streamlit as st
import datetime
import pandas as pd
import plotly.figure_factory as ff
import requests
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from gtts import gTTS
import os

# Weather Icons
weather_icons = {
    "Clear": "🌞",
    "Clouds": "☁️",
    "Drizzle": "🌦️",
    "Rain": "🌧️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Smoke": "🌫️",
    "Haze": "🌫️",
    "Dust": "🌫️",
    "Fog": "🌫️",
    "Sand": "🌫️",
    "Ash": "🌫️",
    "Squall": "🌫️",
    "Tornado": "🌪️"
}


# Define Google LLM for interacting with Google Calendar
llm = ChatGoogleGenerativeAI(model="gemini-pro", verbose=True, temperature=0.6, google_api_key="AIzaSyDjITo6JpwACzQKlMCJKuBhHHK8jTQIhBg")

# Define agents
farmer_agent = Agent(role='Farmer Agent', goal='Gather planting information from the farmer',
                     backstory='An agent specialized in interacting with farmers to gather planting information.',
                     verbose=True, allow_delegation=False, llm=llm)

agronomist_agent = Agent(role='Agronomist Local Expert', goal='Provide personalized farming advice based on location and crop',
                         backstory='An expert specialized in providing personalized farming advice based on location and crop.',
                         verbose=True, allow_delegation=False, llm=llm)

planner_agent = Agent(role='Amazing Planner Agent', goal='Create an optimized planting calendar with budget and best farming practices',
                      backstory='Specialist in farm management and agronomy with decades of experience, providing a calendar based on the provided information.',
                      verbose=True, allow_delegation=False, llm=llm)

crop_suggestion_agent = Agent(role='Crop Suggestion Agent', goal='Suggest alternative crops if the entered crop is out of season',
                              backstory='An agent specialized in suggesting alternative crops based on seasonality and profitability in that local area.',
                              verbose=True, allow_delegation=False, llm=llm)

# Define tasks
planting_info_task = Task(description='Gather planting information from the farmer: {plant}', agent=farmer_agent,
                          expected_output='Planting information collected from the farmer.')

farming_advice_task = Task(description='Provide personalized farming advice for {crop} in {location} starting from {start_date}.',
                           agent=agronomist_agent, expected_output='Personalized farming advice provided.')

farming_calendar_task = Task(description='Generate farming calendar for {crop} in {location} starting from {start_date}.',
                             agent=planner_agent, expected_output='Farming calendar generated.')

season_check_task = Task(description='Check if the planting season has ended for {crop} in {location} by {current_date}.',
                         agent=agronomist_agent, expected_output='Planting season status checked.')

crop_suggestion_task = Task(description='Suggest alternative crops if {crop} is out of season for {location} by {current_date}.',
                            agent=crop_suggestion_agent, expected_output='Alternative crops suggested.')

farming_itinerary_task = Task(description='Display farming itinerary for {crop} in {location} starting from {start_date}.',
                              agent=agronomist_agent, expected_output='Farming itinerary displayed.')

# Define crews
farming_crew_planting = Crew(agents=[farmer_agent, agronomist_agent, planner_agent, crop_suggestion_agent],
                              tasks=[planting_info_task, farming_advice_task, farming_calendar_task, season_check_task,
                                     crop_suggestion_task, farming_itinerary_task], verbose=True, process=Process.sequential)

# Streamlit App
st.title("AbutiSpinach: Your Farming Assistant")
st.markdown("---")


# Task Selection
task_selection = st.radio("Select Task:", options=["Planting Calendar"])

if task_selection == "Planting Calendar":
    # Gather planting information from the farmer
    st.subheader("Planting Information")
    with st.form("planting_form"):
        location = st.text_input("Location (e.g., city, state, or country):", placeholder="Enter your location")
        crop = st.text_input("Crop (e.g., tomatoes, wheat):", placeholder="Enter the crop name")
        start_date = st.date_input("Start Date:", min_value=datetime.date.today(), help="Select the desired start date for planting")

        submitted = st.form_submit_button("Generate Calendar")

        if submitted:
            if not location or not crop or not start_date:
                st.error("Please fill out all fields.")
            else:
                try:
                    # Interpolate farmer's planting information into the tasks descriptions
                    planting_info_task.interpolate_inputs({"plant": crop})
                    farming_advice_task_inputs = {"crop": crop, "location": location, "start_date": start_date}
                    farming_advice_task.interpolate_inputs(farming_advice_task_inputs)
                    farming_calendar_task_inputs = {"crop": crop, "location": location, "start_date": start_date}
                    farming_calendar_task.interpolate_inputs(farming_calendar_task_inputs)
                    current_date = datetime.date.today()
                    season_check_task_inputs = {"crop": crop, "location": location, "current_date": current_date}
                    season_check_task.interpolate_inputs(season_check_task_inputs)
                    crop_suggestion_task_inputs = {"crop": crop, "location": location, "current_date": current_date}
                    crop_suggestion_task.interpolate_inputs(crop_suggestion_task_inputs)
                    farming_itinerary_task_inputs = {"crop": crop, "location": location, "start_date": start_date}
                    farming_itinerary_task.interpolate_inputs(farming_itinerary_task_inputs)

                    # Get weather information for the specified location
                    openweathermap_api_key = "bb7a7d944437ed1b8df2a27b54490cbb"
                    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={openweathermap_api_key}&units=metric"
                    weather_response = requests.get(weather_url)
                    weather_data = weather_response.json()

                    # Display weather information
                    if weather_data["cod"] != "404":
                        st.subheader("Current Weather")
                        cols = st.columns(2)
                        with cols[0]:
                            st.write(f"Temperature: {weather_data['main']['temp']}°C")
                            st.write(f"Humidity: {weather_data['main']['humidity']}%")
                        with cols[1]:
                            weather_condition = weather_data['weather'][0]['main']
                            weather_icon = weather_icons.get(weather_condition, "❓")
                            st.write(f"Weather: {weather_icon} {weather_data['weather'][0]['description']}")
                            st.write(f"Wind Speed: {weather_data['wind']['speed']} m/s")
                            
                            # Text to Speech - Weather Information
                            tts_text_weather = f"Temperature: {weather_data['main']['temp']} degrees Celsius. Humidity: {weather_data['main']['humidity']} percent. Weather: {weather_icon} {weather_data['weather'][0]['description']}. Wind Speed: {weather_data['wind']['speed']} meters per second."
                            tts_filename_weather = "weather_info.mp3"
                            tts_weather = gTTS(tts_text_weather, lang='en')
                            tts_weather.save(tts_filename_weather)
                            st.audio(tts_filename_weather, format='audio/mp3')
                            os.remove(tts_filename_weather)  # Remove the audio file after playing

                    else:
                        st.warning(f"Could not retrieve weather information for {location}.")

                    # Execute the farming crew for planting calendar
                    with st.spinner("Executing farming tasks..."):
                        calendar_data = []
                        for task in farming_crew_planting.tasks:
                            if task.agent == farmer_agent:
                                continue  # Skip displaying output for the farmer's task
                            st.write(f"Executing task: {task.description}")
                            output = task.execute()
                            st.success("Task completed successfully!")

                            # Collect calendar data
                            if task.agent == planner_agent:
                                calendar_data.append(output)
                                
                            # Text to Speech - Agent Response
                            tts_text_agent = output
                            tts_filename_agent = f"agent_response_{task.agent.role.replace(' ', '_')}.mp3"
                            tts_agent = gTTS(tts_text_agent, lang='en')
                            tts_agent.save(tts_filename_agent)
                            st.audio(tts_filename_agent, format='audio/mp3')
                            os.remove(tts_filename_agent)  # Remove the audio file after playing

                            # Display written output
                            st.write(output)

                        # Create Gantt Chart
                        if calendar_data:
                            gantt_df = pd.DataFrame(calendar_data, columns=["Task", "Start", "Finish"])
                            fig = ff.create_gantt(gantt_df, colors=['#7a7a7a', '#adadad'], index_col='Task', show_colorbar=False,
                                                  title='Planting Calendar', showgrid_x=True, showgrid_y=True)
                            st.plotly_chart(fig)

                except ValueError:
                    st.error("Invalid input. Please enter valid values.")

st.markdown("---")
st.info("This application was developed by AbutiSpinach to assist farmers with planting calendars and farming advice. For more information or support, please visit our [website](https://sites.google.com/view/abutispinach).")
