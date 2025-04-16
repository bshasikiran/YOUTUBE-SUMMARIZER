#DEVELOPER: SHASIKIRAN @Shasikiran_2004
import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pyperclip


# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompt
prompt = """You are a helpful YouTube video summarizer. Please summarize the video transcript below into concise, bullet-point notes that highlight the most important takeaways. 
Keep the summary under 250 words, and use clear language. Here's the transcript: 
"""

# Get Video ID
def get_video_id(youtube_url):
    parsed_url = urlparse(youtube_url)
    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]
    elif parsed_url.hostname in ("www.youtube.com", "youtube.com"):
        return parse_qs(parsed_url.query).get("v", [None])[0]
    return None

# Extract Transcript
def extract_transcript_details(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([segment["text"] for segment in transcript])
    except Exception as e:
        raise e

# Generate Gemini Summary
def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt + transcript_text)
    return response.text

# Create PDF
def create_pdf(summary_text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)
    text = c.beginText(40, 750)
    text.setLeading(15)
    text.textLine("YouTube Video Summary:")
    text.textLine("")

    for line in summary_text.split("\n"):
        if text.getY() < 40:
            c.drawText(text)
            c.showPage()
            text = c.beginText(40, 750)
            text.setFont("Helvetica", 12)
            text.setLeading(15)
        text.textLine(line)

    c.drawText(text)
    c.save()
    buffer.seek(0)
    return buffer

# Streamlit App UI
st.set_page_config(page_title="YouTube Summarizer", layout="wide")
st.title("📄 YouTube Transcript to Detailed Notes Converter")

youtube_link = st.text_input("🔗 Enter YouTube Video Link:")

if youtube_link:
    video_id = get_video_id(youtube_link)
    if video_id:
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)
    else:
        st.error("Invalid YouTube link. Please enter a valid URL.")

# Toggle transcript display
show_transcript = st.checkbox("Show Raw Transcript")

# Summarize
if st.button("✨ Get Detailed Notes"):
    if not video_id:
        st.error("Could not extract video ID.")
    else:
        with st.spinner("⏳ Fetching transcript and generating summary..."):
            try:
                transcript_text = extract_transcript_details(video_id)

                if len(transcript_text) > 10000:
                    transcript_text = transcript_text[:10000]

                if transcript_text:
                    if show_transcript:
                        st.markdown("### 📄 Raw Transcript:")
                        st.info(transcript_text)

                    summary = generate_gemini_content(transcript_text, prompt)

                    st.markdown("## 📝 Detailed Notes:")
                    st.success(summary)

                    # Word count
                    st.caption(f"🧾 Word Count: {len(summary.split())}")

                    # PDF download
                    pdf_buffer = create_pdf(summary)
                    st.download_button("📥 Download Summary as PDF", data=pdf_buffer,
                                       file_name="YouTube_Summary.pdf", mime="application/pdf")

                    # Copy to clipboard (note: works only locally if `pyperclip` is installed)
                    if st.button("📋 Copy Summary to Clipboard"):
                        try:
                            pyperclip.copy(summary)
                            st.toast("Copied to clipboard!", icon="✅")
                        except:
                            st.warning("Clipboard copy works only in local apps.")

                else:
                    st.warning("No transcript found for this video.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
