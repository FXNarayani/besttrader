
import openai
import streamlit as st

# Your OpenAI API Key (from Streamlit secrets)
openai.api_key = st.secrets["openai"]["api_key"]

# Example function to generate a response
def get_chatgpt_response(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",  # Use appropriate engine
        prompt=prompt,
        max_tokens=100
    )
    return response.choices[0].text.strip()

st.title("Beast Trader - AI + Telegram Breakout Screener")

# Example usage of the function
prompt = st.text_input("Enter your trade query:")
if prompt:
    response = get_chatgpt_response(prompt)
    st.write(response)
