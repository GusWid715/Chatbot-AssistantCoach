# Import the necessary libraries
import streamlit as st  # For creating the web app interface
import os
from langchain_google_genai import ChatGoogleGenerativeAI  # For interacting with Google Gemini via LangChain
from langgraph.prebuilt import create_react_agent  # For creating a ReAct agent
from langchain_core.messages import HumanMessage, AIMessage  # For message formatting
from langchain_core.tools import tool  # For creating tools

# Import our database tools
# Pastikan file database_tools.py ada di folder yang sama
from database_tools import text_to_sql, init_database, get_database_info

# --- 1. Page Configuration and Title ---

# Set the title and a caption for the web page
st.title("⚽️ Head of Recruitment")
st.caption("Asisten AI untuk scouting, analisis pemain, dan rekrutmen data-driven.")

# --- 2. Sidebar for Settings ---

# Create a sidebar section for app settings using 'with st.sidebar:'
with st.sidebar:
    # Add a subheader to organize the settings
    st.subheader("Settings")
    
    # Create a text input field for the Google AI API Key.
    google_api_key = st.text_input("Google AI API Key", type="password")
    
    # Create a button to reset the conversation.
    reset_button = st.button("Reset Conversation", help="Clear all messages and start fresh")
    
    # Add a button to initialize the database
    init_db_button = st.button("Initialize Database", help="Muat data 'players', 'clubs', dan 'player_valuations' dari CSV ke database SQLite.")
    
    # Initialize database if button is clicked
    if init_db_button:
        with st.spinner("Memuat data dari CSV ke database... Ini mungkin perlu waktu sejenak."):
            result = init_database()
            st.success(result) # Akan menampilkan pesan sukses/error dari database_tools.py

# --- 3. API Key and Agent Initialization ---

if not google_api_key:
    st.info("Please add your Google AI API key in the sidebar to start chatting.", icon="🗝️")
    st.stop()

# Define the tools using the LangChain tool decorator
@tool
def execute_sql(sql_query: str):
    """
    Execute a SQL query against the football database.
    
    Args:
        sql_query: The SQL query to execute. Must be a valid SQL query string.
              For example: "SELECT * FROM players LIMIT 5", "SELECT name, market_value FROM players ORDER BY market_value DESC LIMIT 10", etc.
    """
    result = text_to_sql(sql_query)
    # Format the result to clearly show the executed SQL query
    formatted_result = f"```sql\n{sql_query}\n```\n\nQuery Results:\n{result}"
    return formatted_result

@tool
def get_schema_info():
    """
    Get information about the database schema and sample data to help with query construction.
    This tool returns the schema of all tables (players, clubs, player_valuations) 
    and sample data (first 3 rows) from each table.
    Use this tool BEFORE writing SQL queries to understand the database structure.
    """
    return get_database_info()

# This block of code handles the creation of the LangGraph agent.
if ("agent" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        # Initialize the LLM with the API key
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.1  # Lower temperature for more accurate SQL
        )
        
        # --- PROMPT AGEN ---
        st.session_state.agent = create_react_agent(
            model=llm,
            tools=[get_schema_info, execute_sql],
            prompt="""You are the "Head of Recruitment," a helpful AI assistant. Your role is to identify talent and support recruitment decisions using data.
            You answer questions about players, clubs, and market values using SQL to find potential targets.
            
            The database contains 3 main tables:
            1. 'players': Contains player information (name, position, nationality, date_of_birth, height, foot, current_club_id, etc.).
            2. 'clubs': Contains club information (club_id, name, league_name, etc.).
            3. 'player_valuations': Contains player market value history (player_id, date, market_value).
            
            IMPORTANT: When a user asks a question about football data, follow these steps:
            1. FIRST, use the `get_schema_info` tool to see the exact column names and data types for all tables.
            2. THEN, construct a SQL query based on the user's question and the database schema.
            3. Execute the SQL query using the `execute_sql` tool.
            4. Explain the results in a clear and concise way.
            
            When writing SQL queries:
            - You will often need to JOIN tables.
            - `players.player_id` links to `player_valuations.player_id`.
            - `players.current_club_id` links to `clubs.club_id`.
            - Pay close attention to column names from the schema (e.g., 'date_of_birth', 'market_value', 'name').
            - Use proper SQL syntax for SQLite.
            - When asked for the "current" market value, you should look for the most recent date in the 'player_valuations' table for that player.
            
            If you encounter any errors:
            - Explain what went wrong.
            - Fix the SQL query and try again.
            
            Remember: You must generate the SQL query yourself based on the user's question and the database schema.
            Do not ask the user to provide SQL queries.
            """
        )
        
        # Store the new key in session state
        st.session_state._last_key = google_api_key
        st.session_state.pop("messages", None)
    except Exception as e:
        st.error(f"Invalid API Key or configuration error: {e}")
        st.stop()

# --- 4. Chat History Management ---

if "messages" not in st.session_state:
    st.session_state.messages = []

if reset_button:
    st.session_state.pop("agent", None)
    st.session_state.pop("messages", None)
    st.rerun()

# --- 5. Display Past Messages ---

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. Handle User Input and Agent Communication ---

# Ubah placeholder teks input
prompt = st.chat_input("Tanyakan soal data pemain, klub, atau nilai pasar...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        with st.spinner("Asisten sedang berpikir..."):
            response = st.session_state.agent.invoke({"messages": messages})
            
            if "messages" in response and len(response["messages"]) > 0:
                answer = response["messages"][-1].content
                
                # ekstrak SQL query dari log
                sql_query = None
                for msg in reversed(response["messages"]): # Cari dari belakang
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            if tool_call.get("name") == "execute_sql" and "sql_query" in tool_call.get("args", {}):
                                sql_query = tool_call["args"]["sql_query"]
                                st.session_state.last_sql_query = sql_query
                                break
                    if sql_query:
                        break
            else:
                answer = "I'm sorry, I couldn't generate a response."

    except Exception as e:
        answer = f"An error occurred: {e}"

    with st.chat_message("assistant"):
        # Tampilkan SQL query jika ditemukan
        sql_query_to_show = st.session_state.pop("last_sql_query", None)
        if sql_query_to_show:
            st.code(sql_query_to_show, language="sql")
        
        st.markdown(answer)
    
    st.session_state.messages.append({"role": "assistant", "content": answer})