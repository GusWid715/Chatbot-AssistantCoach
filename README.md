## Deskripsi

### ⚽️ Head of Recruitment: Chatbot Analisis Data Sepak Bola

Proyek ini bertujuan untuk membangun sebuah chatbot AI dengan nama "Head of Recruitment". Aplikasi ini berfungsi sebagai asisten perekrutan yang dirancang untuk membantu proses scouting dan analisis pemain sepak bola. Pengguna dapat mengajukan pertanyaan dalam bahasa alami dan chatbot akan memproses permintaan tersebut untuk memberikan jawaban yang diekstrak langsung dari database.

## Komponen Teknis:

- **streamlit as st**: Kerangka kerja Python utama yang digunakan untuk membangun antarmuka pengguna (UI) aplikasi web. Perintah streamlit run streamlit_react_tools_app.py digunakan untuk menjalankan aplikasi.

  - `st.title("⚽️ Head of Recruitment")`: Menampilkan judul utama pada halaman web aplikasi.
  - `st.sidebar`: Komponen UI yang digunakan untuk menampung input google_api_key melalui st.text_input (dengan type="password") dan tombol init_db_button (st.button) untuk menginisialisasi database.

- **langchain_google_genai.ChatGoogleGenerativeAI**: Ini adalah model LLM (Gemini gemini-2.5-flash) yang berfungsi sebagai "otak" chatbot, memproses bahasa alami dan instruksi prompt.

- **langgraph.prebuilt.create_react_agent**: Komponen LangGraph yang krusial. Fungsi ini digunakan untuk membangun agen AI (ReAct Agent) yang mampu "berpikir" (Reason) dan "bertindak" (Act). Agen inilah yang memutuskan kapan harus memanggil tools (seperti execute_sql) berdasarkan prompt pengguna.

- **database_tools.py**: Sebuah modul Python kustom yang berisi fungsi-fungsi untuk berinteraksi dengan database.

  - `init_database()`: Fungsi yang dipanggil oleh tombol di sidebar. Fungsi ini menggunakan Pandas untuk membaca file .csv (players.csv, clubs.csv, player_valuations.csv) dan memuatnya ke dalam database SQLite (football_data.db).
  - `text_to_sql()` & `get_database_info()`: Fungsi yang diekspos sebagai tools yang bisa digunakan oleh agen AI untuk mengeksekusi kueri SQL dan mendapatkan skema database.

- **st.session_state**: Komponen ini krusial. Streamlit menjalankan ulang skrip setiap kali ada interaksi. Untuk mencegah hilangnya data penting, st.session_state digunakan untuk menyimpan instance agen AI (st.session_state.agent) dan riwayat obrolan (st.session_state.messages) agar tetap persisten antar-interaksi.

- **st.chat_message(role)**: Komponen ini digunakan untuk membuat gelembung (bubble) obrolan di UI, membedakan antara pesan "user" dan "assistant".

- **st.chat_input("Tanyakan soal data...")**: Komponen ini menyediakan kotak input teks di bagian bawah layar, yang khusus dirancang untuk aplikasi chat.

## Logika Interaksi:

1. Aplikasi pertama-tama meminta google_api_key di sidebar.
2. Setelah API Key dimasukkan, aplikasi menginisialisasi Agen ReAct (LLM + Tools + Prompt kustom) dan menyimpannya di st.session_state.agent.
3. Pengguna diharapkan menekan tombol "Initialize Database" untuk memuat data dari .csv ke database SQLite. Pesan sukses akan ditampilkan.
4. Semua pesan yang ada di st.session_state.messages ditampilkan ke UI menggunakan st.chat_message.
5. Aplikasi menunggu input pengguna melalui st.chat_input.
6. Ketika pengguna mengirim prompt, prompt tersebut (bersama seluruh riwayat obrolan) dikirim ke st.session_state.agent.invoke().
7. Agen AI kemudian memulai siklus ReAct: ia mungkin akan memanggil get_schema_info, lalu "berpikir" untuk membuat kueri SQL, lalu memanggil execute_sql untuk mendapatkan data, dan terakhir merumuskan jawaban dalam bahasa alami.
8. Jawaban akhir dari agen ditambahkan ke st.session_state.messages dan langsung ditampilkan di UI sebagai gelembung obrolan "assistant".

## Menjalankan Aplikasi

### 1. Instalasi

Pastikan Anda memiliki Python 3.9+ dan buatlah virtual environment. Instal semua dependency yang diperlukan:

```bash
pip install -r requirements.txt
```

### 2. Siapkan Data

Pastikan file `players.csv`, `clubs.csv`, dan `player_valuations.csv` berada di direktori root proyek.

### 3. Jalankan Streamlit

Aplikasi utama yang digunakan adalah `streamlit_react_tools_app.py`.

```bash
streamlit run streamlit_react_tools_app.py
```

### 4. Inisialisasi Database

Saat aplikasi terbuka di browser:

- Masukkan kunci API Google AI Anda di sidebar.
- Klik tombol "Initialize Database" di sidebar. Proses ini akan membaca file CSV dan membuat file database `football_data.db`.
- Mulai ajukan pertanyaan rekrutmen Anda.
