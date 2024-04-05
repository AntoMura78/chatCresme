
# %%
import streamlit as st
import openai
from datetime import timedelta
from PIL import Image
import io
import base64
import pyttsx3

# Initialize OpenAI API key
openai.api_key = st.secrets["OPkey"]
limit = 5
# %% Streamlit UI
st.image("https://www.harpaceas.it/hs-fs/hubfs/logo_cresme_60_compatto.png?width=1194&height=749&name=logo_cresme_60_compatto.png", width=200)
st.write('http://www.cresme.it')
st.header(':blue[Chat con Cresme]', divider='rainbow')

st.markdown('Prova a chiedere:  <li> Cosa è il Cresme?</li>' +
            '<li> Quali sono le opzioni di associazione? </li>',
            unsafe_allow_html=True)
input_text = st.chat_input(
    "Inserisci la tua domanda (riavvia la pagina per resettare la conversazione)")

# %% Initialize or update session state for conversation
if 'messaggi_preparati' not in st.session_state:
    st.session_state.messaggi_preparati = []
if 'contatore' not in st.session_state:
    st.session_state.contatore = 0
if input_text:
    if 'thread_id' not in st.session_state:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id

# %% defining the assistant
assistant = openai.beta.assistants.retrieve(
    'asst_nYeTpYfq8ClgCPKHqxbubSJP')


def call_assistant(th_id, assistant, question):
    # % Step 2: Create a Thread/conversation

    # % add a message to the thread
    openai.beta.threads.messages.create(
        thread_id=th_id,
        role="user",
        content=question)
    # % make the assistant read the thread
    run = openai.beta.threads.runs.create(
        thread_id=th_id,
        assistant_id=assistant.id)
    while run.status in ["queued", "in_progress"]:
        keep_retrieving_run = openai.beta.threads.runs.retrieve(
            thread_id=th_id, run_id=run.id)
        if keep_retrieving_run.status == "completed":
            messages = openai.beta.threads.messages.list(thread_id=th_id)
            break
    return messages


def srotola(msg):
    paragrafi = []
    messaggi = []
    for i in range(0, len(msg.data)):
        paragrafi.append(msg.data[i].content)
    for j in range(len(paragrafi)-1, -1, -1):
        for k in range(len(paragrafi[j])-1, -1, -1):
            if paragrafi[j][k].type == 'text':
                messaggi.append(paragrafi[j][k].text.value)
            elif paragrafi[j][k].type == 'image_file':
                messaggi.append(Image.open(openai.files.content(
                    paragrafi[j][k].image_file.file_id)))
    return messaggi


def immagine_a_base64(immagine):
    img_byte_arr = io.BytesIO()
    immagine.save(img_byte_arr, format='PNG')
    encoded_img = base64.b64encode(img_byte_arr.getvalue()).decode('ascii')
    return f"data:image/png;base64,{encoded_img}"


def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


# %% Catching the thread
if st.session_state.contatore < limit:
    if input_text:  # Check if there's input text
        with st.status("Attendere"):
            st.write("Rispondo all'ultima domanda: " + input_text)

            msg = call_assistant(st.session_state.thread_id,
                                 assistant, 'Domanda: '+input_text)
            messaggi = srotola(msg)
            messaggi_preparati = [immagine_a_base64(m) if isinstance(
                m, Image.Image) else m for m in messaggi]

            st.session_state.messaggi_preparati = messaggi_preparati
            st.session_state.contatore += 1
# Display conversation
c = 1
if st.session_state.messaggi_preparati:
    with st.chat_message("assistant"):
        st.subheader("Conversazione:")
        for msg in st.session_state.messaggi_preparati:
            # For images, you would use st.image after converting them to base64 or directly if they're URLs
            if msg.startswith('data:image'):
                st.image(msg)
            else:
                if msg.startswith('Domanda'):
                    highlighted_text = f"""
                    <style>
                    .highlight {{
                        background-color: #f0f0f0; /* Grigio */
                    }}
                    </style>
                    <p class="highlight">{msg}</p>
                    """
                    # st.markdown(highlighted_text, unsafe_allow_html=True)
                    st.success(msg)
                else:
                    st.markdown(msg)
                    if st.button('Listen to the answer', key=c):
                        text_to_speech(msg)
            c += 1


restanti = limit-st.session_state.contatore
if restanti > 0:
    progress_bar = st.progress(
        st.session_state.contatore / (limit), 'Domande disponibili: ' + str(restanti))
else:
    progress_bar = st.progress(
        st.session_state.contatore / st.session_state.contatore, ':red[Limite domande raggiunto!]')
