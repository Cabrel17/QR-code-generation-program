import streamlit as st
import pandas as pd
import qrcode
import os
import zipfile
from io import BytesIO
import math

# =========================
# CONFIGURATION GLOBALE
# =========================
MAX_ROWS = 10_000

st.set_page_config(
    page_title="Générateur de QR Codes",
    layout="centered"
)

# =========================
# HEADER
# =========================
col1, col2 = st.columns([1, 4])
with col1:
    st.image("logo_moov_africa.jfif", width=80)
with col2:
    st.markdown("### Application de génération de QR Codes")
    st.markdown("Chargez une base de short codes et obtenez vos QR codes.")

st.divider()

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("### Paramètres d'entrée")

    uploaded_file = st.file_uploader(
        "Charger le fichier Excel",
        type=["xlsx", "xls"]
    )

    shortcode_col_index = st.number_input(
        "Numéro de la colonne des short codes",
        min_value=1,
        step=1
    )

    company_col_index = st.number_input(
        "Numéro de la colonne des noms d'entreprises",
        min_value=1,
        step=1
    )

# =========================
# FONCTIONS
# =========================
def sanitize_text(text):
    return "".join(
        c if c.isalnum() or c in ("_", "-") else "_"
        for c in str(text).strip()
    )

def make_qr(code, company_name, output_dir):
    if pd.isna(code) or str(code).strip() == "":
        return None

    code = str(code).strip()
    filename = f"qr_{sanitize_text(company_name)}_{sanitize_text(code)}.png"
    path = os.path.join(output_dir, filename)

    img = qrcode.make(code)
    img.save(path)

    return path

def split_dataframe(df, chunk_size):
    total_rows = len(df)
    n_chunks = math.ceil(total_rows / chunk_size)
    chunks = []

    for i in range(n_chunks):
        start = i * chunk_size
        end = start + chunk_size
        chunks.append((i + 1, df.iloc[start:end].copy()))

    return chunks

# =========================
# TRAITEMENT PRINCIPAL
# =========================
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("Fichier chargé avec succès")

        st.write("Aperçu des données :")
        st.dataframe(df.head())

        total_rows = len(df)

        # =========================
        # CAS 1 : GROS DATASET
        # =========================
        if total_rows > MAX_ROWS:
            st.warning(
                f"""
                ⚠️ **Votre base contient {total_rows:,} lignes.**

                Pour des raisons de performance, la génération des QR codes
                se fera **par lots de 10 000 lignes**

                - Veuillez d’abord découper votre base en plusieurs lots.\n
                - Vous chargerez ensuite chacune des bases pour générer les QR Codes.
                """
            )

            if st.button("Découper la base en lots"):
                chunks = split_dataframe(df, MAX_ROWS)
                total_chunks = len(chunks)

                progress = st.progress(0)
                status = st.empty()

                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for i, (idx, chunk_df) in enumerate(chunks, start=1):
                        status.info(
                            f"Découpage en cours : base {i} / {total_chunks}"
                        )

                        buffer = BytesIO()
                        file_name = f"Base_{idx:02d}.xlsx"
                        chunk_df.to_excel(buffer, index=False)
                        buffer.seek(0)
                        zipf.writestr(file_name, buffer.read())

                        progress.progress(i / total_chunks)

                zip_buffer.seek(0)

                st.success(f"{total_chunks} bases obtenues")

                st.download_button(
                    label="Télécharger les bases découpées (ZIP)",
                    data=zip_buffer,
                    file_name="bases_decoupées.zip",
                    mime="application/zip"
                )

            st.stop()  # STOP

        # =========================
        # CAS 2 : DATASET NORMAL
        # =========================
        else:
            if st.button("Générer les QR Codes"):
                base_output_dir = "output"
                qr_dir = os.path.join(base_output_dir, "qr_codes")
                os.makedirs(qr_dir, exist_ok=True)

                shortcode_col = df.columns[shortcode_col_index - 1]
                company_col = df.columns[company_col_index - 1]

                df[shortcode_col] = df[shortcode_col].astype(str).str.strip()

                progress = st.progress(0)
                status = st.empty()
                paths = []

                total = len(df)

                for i, (code, company) in enumerate(
                    zip(df[shortcode_col], df[company_col]), start=1
                ):
                    p = make_qr(code, company, qr_dir)
                    if p:
                        paths.append(p)

                    if i % 100 == 0 or i == total:
                        progress.progress(i / total)
                        status.info(f"Génération QR : {i} / {total}")

                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in paths:
                        arcname = os.path.relpath(file_path, base_output_dir)
                        zipf.write(file_path, arcname)

                zip_buffer.seek(0)

                st.success(f"{len(paths)} QR codes générés avec succès")

                st.download_button(
                    label="Télécharger les QR Codes (ZIP)",
                    data=zip_buffer,
                    file_name="qr_codes.zip",
                    mime="application/zip"
                )

    except Exception as e:
        st.error(f"Erreur lors du traitement : {e}")

# =========================
# FOOTER
# =========================
st.divider()
st.markdown(
    "<center><small>Moov Africa (GVC) – Moov Money</small></center>",
    unsafe_allow_html=True
)
