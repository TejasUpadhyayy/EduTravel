import streamlit as st
from fpdf import FPDF
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key="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")

st.set_page_config(page_title="Educational Tour Proposal Generator", layout="wide")
st.title("📚 Educational Tour Proposal AI Agent")

# Input Section
with st.sidebar:
    st.header("📋 Tour Configuration")
    start_location = st.text_input("Starting Location")
    destination = st.text_input("Destination")
    duration = st.slider("Duration (days)", 1, 15, 5)
    experiences = st.multiselect("Select Experience Types", [
        "University Visit", "Industry Visit", "Student Exchange",
        "Skill Workshop", "Cultural Activities", "Sightseeing"
    ])
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    hotel_type = st.selectbox("Hotel Type", ["3-star", "4-star", "5-star"])
    weather = st.text_area("Weather Notes (Optional)")

    status = st.selectbox("Proposal Status", [
        "Draft", "Sent", "In Review", "Feedback Received", "Finalized", "Confirmed"
    ])

# Generate Travel Plan
if st.button("Generate Tour Proposal"):
    prompt = f"""
    Generate a {duration}-day educational tour plan to {destination} for school students.

    Include:
    - Experience types: {', '.join(experiences)}
    - Day-wise itinerary with morning/afternoon/evening slots
    - Suggested hotels ({hotel_type})
    - Meals included (B/L/D)
    - Learning outcomes per day
    - Estimated cost breakdown including:
        - Travel cost (bus/train/flight)
        - Hotel stay (per night per student)
        - Experience/activity fees
        - Meal cost per day
        - Miscellaneous charges
    - Total base cost per student
    - Notes on weather: {weather}
    """

    with st.spinner("Generating proposal and estimating cost..."):
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a school tour planning AI assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        travel_plan = response.choices[0].message.content.strip()

        # Extracting cost (rough logic — assumes Groq model outputs a line like "Total Base Cost: ₹XXXXX")
        import re
        match = re.search(r"Total Base Cost.*?₹?(\d+[\d,]*)", travel_plan)
        base_cost = float(match.group(1).replace(",", "")) if match else 0
        convenience_fee = round(base_cost * 0.10, 2)
        final_cost = round(base_cost + convenience_fee, 2)

        st.session_state["travel_plan"] = travel_plan
        st.session_state["base_cost"] = base_cost
        st.session_state["final_cost"] = final_cost
        st.session_state["convenience_fee"] = convenience_fee

        st.success("✅ Proposal & Budget Generated!")
        st.write(travel_plan)

        if base_cost > 0:
            st.markdown("---")
            st.markdown("### 💰 **Budget Summary**")
            st.markdown(f"- **Base Cost per Student**: ₹{base_cost:,.2f}")
            st.markdown(f"- **Convenience Fee (10%)**: ₹{convenience_fee:,.2f}")
            st.markdown(f"### 🧾 **Total Final Price per Student: ₹{final_cost:,.2f}**")


# Amendment Chat
if "travel_plan" in st.session_state:
    amendment_prompt = st.text_input("✏️ Suggest a change to the itinerary")
    if amendment_prompt:
        chat_response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a school tour planning AI assistant."},
                {"role": "user", "content": f"Original Plan:\n{st.session_state['travel_plan']}"},
                {"role": "user", "content": f"Amendment: {amendment_prompt}"}
            ]
        )
        new_plan = chat_response.choices[0].message.content.strip()
        st.session_state["travel_plan"] = new_plan
        st.write("🔁 Updated Itinerary:")
        st.write(new_plan)

# Download Proposal
if "travel_plan" in st.session_state:
    if st.button("Download Proposal PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in st.session_state["travel_plan"].split("\n"):
            pdf.multi_cell(0, 10, line)
        pdf.output("Tour_Proposal.pdf")
        st.success("📄 Proposal downloaded as PDF!")

# Status
if "travel_plan" in st.session_state:
    st.markdown(f"### 📌 Current Proposal Status: `{status}`")
