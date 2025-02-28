import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, time
import time as tm

# URL dari Google Apps Script Web App (Ganti dengan URL Web App Anda)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx5l661KhMjkrC00-ZiGVqMXnBOMXgmvDoenKAK0Zh3DkUzt7JGVi82aGLWFmUyo9ie/exec"

# Fungsi untuk mendapatkan semua data dari Google Sheets
def get_all_data():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_data"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil data: {e}")
        return []

# Ambil data dari Google Sheets
all_data = get_all_data()

# Tampilkan di Streamlit
st.title("Daftar Riwayat Mesin")

if isinstance(all_data, list) and len(all_data) > 0:
    # Konversi data ke DataFrame
    df = pd.DataFrame(all_data, columns=[
        "ID", "BU", "Line", "Produk", "Mesin", "Tanggal", 
        "Mulai", "Selesai", "Masalah", "Tindakan", 
        "Deskripsi", "Quantity", "PIC", "Approval", "Mengetahui"
    ])

    # Menampilkan data sebagai tabel
    st.subheader("Data Keseluruhan")
    st.dataframe(df)

    # Tambahkan visualisasi sederhana (misalnya, jumlah entri per masalah)
    st.subheader("Visualisasi Masalah")
    masalah_counts = df["Masalah"].value_counts().reset_index()
    masalah_counts.columns = ["Masalah", "Jumlah"]
    st.bar_chart(masalah_counts.set_index("Masalah"))
else:
    st.warning("Tidak ada data yang tersedia.")

# Fungsi untuk mendapatkan opsi dari Google Sheets
def get_options():
    try:
        response = requests.get(APPS_SCRIPT_URL, params={"action": "get_options"}, timeout=10)
        response.raise_for_status()
        options = response.json()
        # Tambahkan opsi kosong "" sebagai default di setiap kategori
        for key in options:
            options[key].insert(0, "")
        return options
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat mengambil data: {e}")
        return {}
    


# Fungsi untuk mengirim data ke Google Sheets
def add_data(form_data):
    try:
        response = requests.post(APPS_SCRIPT_URL, json=form_data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

# Ambil data untuk select box
options = get_options()

# Cek dan set default di session_state jika belum ada
defaults = {
    "form_bu": "",
    "form_line": "",
    "form_produk": "",
    "form_mesin": "",
    "form_masalah": "",
    "form_tindakan": "",
    "form_deskripsi": "",
    "form_pic": "",
}

if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = False

if st.session_state.reset_trigger:
    for key, value in defaults.items():
        st.session_state[key] = value
    st.session_state.reset_trigger = False


# Streamlit UI
st.title("Tambah Data ke Google Sheets")
st.subheader("Isi Data Berikut:")

bu_options = [item[0] if isinstance(item, list) and item else item for item in options.get("BU", [""])]
bu = st.selectbox("BU", bu_options, key="form_bu")

# Reset Produk jika BU berubah
if bu != st.session_state.form_bu:
    st.session_state.form_bu = bu
    st.session_state.form_produk = ""  # Reset Produk
    st.session_state.form_pic = ""


line_options = [item[0] if isinstance(item, list) and item else item for item in options.get("Line", [""])]
line = st.selectbox("Line", line_options , key="form_line")

# Filter produk berdasarkan BU yang dipilih
# Filter daftar Produk berdasarkan BU yang dipilih
# Pastikan options["Produk"] memiliki struktur yang benar sebelum memprosesnya
produk_options = [item[1] for item in options.get("Produk", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu] if bu else [""]
produk = st.selectbox("Produk", produk_options, key="form_produk")

mesin_options = [item[1] for item in options.get("Mesin", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu] if bu else [""]
mesin = st.selectbox("Mesin", mesin_options, key="form_mesin")

if mesin != st.session_state.form_mesin:
    st.session_state.form_mesin = mesin
    st.session_state.form_masalah = "" 

tanggal = st.date_input("Tanggal Pengerjaan")
mulai = st.time_input("Waktu Mulai")
selesai = st.time_input("Waktu Selesai")

masalah_options = [item[1] for item in options.get("Masalah", []) if isinstance(item, list) and len(item) > 1 and item[0] == mesin] if bu else [""]
masalah = st.selectbox("Masalah", masalah_options, key="form_masalah")

tindakan_options = [item[0] if isinstance(item, list) and item else item for item in options.get("Tindakan Perbaikan", [""])]
tindakan = st.selectbox("Tindakan Perbaikan", tindakan_options, key="form_tindakan")

deskripsi_options = [item[0] if isinstance(item, list) and item else item for item in options.get("Deskripsi", [""])]
deskripsi = st.selectbox("Deskripsi Sparepart", deskripsi_options, key="form_deskripsi")

quantity = st.number_input("Quantity", min_value=0, value=0)

pic_options = [item[1] for item in options.get("PIC", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu] if bu else [""]
pic = st.selectbox("PIC", pic_options, key="form_pic")

submitted = st.button("Tambah Data")

if submitted:
    if selesai <= mulai:
        st.error("Waktu selesai harus lebih besar dari waktu mulai.")
    else:
        data_to_send = {
            "action": "add_data",
            "BU": bu,
            "Line": line,
            "Produk": produk,
            "Mesin": mesin,
            "Tanggal": tanggal.strftime("%Y-%m-%d"),
            "Mulai": mulai.strftime("%H:%M"),
            "Selesai": selesai.strftime("%H:%M"),
            "Masalah": masalah,
            "Tindakan": tindakan,
            "Deskripsi": deskripsi,
            "Quantity": int(quantity),
            "PIC": pic
        }

        response = add_data(data_to_send)

        if response.get("status") == "success":
            st.toast("Data berhasil ditambahkan!", icon="✅")
            tm.sleep(2)
            st.session_state.form_add_reset = True
            st.rerun()
        else:
            st.error(f"Gagal menambahkan data: {response.get('error', 'Tidak diketahui')}")