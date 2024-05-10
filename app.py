import streamlit as st
import streamlit_authenticator as stauth
from lida import Manager, TextGenerationConfig, llm
from dotenv import load_dotenv
import os
import openai
from PIL import Image
from io import BytesIO
import base64
import yaml
from yaml.loader import SafeLoader

def render_main():
    load_dotenv()

    openai.api_key = os.getenv("OPENAI_API_KEY")

    def base64_to_image(base64_string):
        byte_data = base64.b64decode(base64_string)

        return Image.open(BytesIO(byte_data))

    # Initiate lia with openai model
    lida = Manager(text_gen=llm("openai"))
    # Using a local model
    # llm(provider='hf', model="together-computer/llama-32k", device_map="auto")

    menu = st.sidebar.selectbox(
        "Choose an option", ["Summarize", "Question based Graph"]
    )

    if menu == "Summarize":
        st.subheader("Summarization of your Data")

        ai_model = st.selectbox("Open AI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        number_of_ideas = st.number_input("Number of ideas", min_value=1, max_value=5, value=3)

        textgen_config = TextGenerationConfig(
            n=1, temperature=0.2, model=ai_model, use_cache=True
        )
        file_uploader = st.file_uploader("Upload your file", type="csv")
        if file_uploader is not None:
            path_to_save = f"files/{file_uploader.name}"
            with open(path_to_save, "wb") as f:
                f.write(file_uploader.getvalue())
            summary = lida.summarize(
                path_to_save, summary_method="default", textgen_config=textgen_config
            )
            st.text("Summary of the uploaded file")
            st.write(summary)
            goals = lida.goals(summary, n=number_of_ideas, textgen_config=textgen_config)
            for goal in goals:
                st.write(goal)
                library = "seaborn"
                charts = lida.visualize(
                    summary=summary,
                    goal=goal,
                    textgen_config=textgen_config,
                    library=library
                )
                for chart in charts:
                    img_base64_string = chart.raster
                    img = base64_to_image(img_base64_string)
                    st.image(img)

    elif menu == "Question based Graph":
        st.subheader("Query your data to generate Graph")

        ai_model = st.selectbox("Open AI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        textgen_config = TextGenerationConfig(
            n=1, temperature=0.2, model=ai_model, use_cache=True
        )

        file_uploader = st.file_uploader("Upload your CSV", type="csv")
        if file_uploader is not None:
            path_to_save = f"files/{file_uploader.name}"
            with open(path_to_save, "wb") as f:
                f.write(file_uploader.getvalue())

            text_area = st.text_area("Query your data to generate Graph", height=200)
            if st.button("Generate Graph"):
                if len(text_area) > 0:
                    st.info("Your query: " + text_area)
                    lida = Manager(text_gen=llm("openai"))
                    summary = lida.summarize(
                        path_to_save,
                        summary_method="default",
                        textgen_config=textgen_config,
                    )
                    user_query = text_area
                    charts = lida.visualize(
                        summary=summary, goal=user_query, textgen_config=textgen_config
                    )

                    st.write(f"Number of charts generated: {len(charts)}")

                    for chart in charts:
                        image_base64 = chart.raster
                        img = base64_to_image(image_base64)
                        st.image(img)

# Load authentication config
with open("./config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

# Starts with login page
authenticator.login()
if st.session_state["authentication_status"]:
    # Display main content and logout widged if login successfully
    st.write(f'Welcome *{st.session_state["name"]}*')
    authenticator.logout()
    render_main()
elif st.session_state["authentication_status"] is False:
    # Display error incorrect password if authentication fail
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    # Show warning messages if not input all data
    st.warning("Please enter your username and password")
