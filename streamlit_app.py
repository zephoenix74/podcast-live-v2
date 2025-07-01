from openai import OpenAI
client = OpenAI()

import streamlit as st
from elevenlabs import set_api_key, generate, save
import os
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import queue
import av
import tempfile

# Configuration des clés API
set_api_key(os.getenv("ELEVENLABS_API_KEY"))

st.set_page_config("🎧 Podcast Live IA", layout="centered")
st.title("🎧 Podcast interactif en direct : Israël - Iran")

# Écoute du podcast
st.subheader("🎙 Écoutez le podcast")
st.audio("podcast.mp3", format="audio/mp3")

st.subheader("🎤 Posez une question à voix haute (micro en direct)")

# Gestion audio live
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.buffer = queue.Queue()

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray().flatten().astype("int16").tobytes()
        self.buffer.put(pcm)
        return frame

ctx = webrtc_streamer(
    key="speech-to-text",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if ctx.state.playing:
    st.info("🎙️ Parlez maintenant...")
    if ctx.audio_processor:
        audio_data = b""
        while not ctx.audio_processor.buffer.empty():
            audio_data += ctx.audio_processor.buffer.get()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_data)
            wav_path = f.name

        if wav_path:
            with st.spinner("🔍 Transcription en cours..."):
                with open(wav_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                st.markdown(f"📝 **Vous avez dit** : {transcript.text}")

                with st.spinner("💬 Réponse de l’IA..."):
                    chat = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Tu es un expert en géopolitique, parle simplement."},
                            {"role": "user", "content": transcript.text}
                        ]
                    )
                    reply = chat.choices[0].message.content
                    st.markdown(f"🧠 **Réponse IA** : {reply}")

                with st.spinner("🔊 Synthèse vocale..."):
                    audio = generate(text=reply, voice="Bella", model="eleven_multilingual_v1")
                    save(audio, "ia-response.mp3")
                    st.audio("ia-response.mp3", format="audio/mp3")

st.audio("", format="audio/mp3")  # coupe l'audio actif

