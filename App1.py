import streamlit as st
import pandas as pd
import qrcode
import os
import zipfile
from io import BytesIO

# Configuration de la page
st.set_page_config(
    page_title="Générateur de QR Codes",
    layout="centered"
)

# Header with logo
col1, col2 = st.columns([1, 4])
with col1:
    st.image("logo_moov_africa.jfif", width=80) 
with col2:
    st.markdown("### Application de génération de QR Codes")
    st.markdown("Chargez une base de shorts codes et obtenez vos QR codes.")


st.divider()

# Chargement du fichier 

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

#Fonction de génération QR

def make_qr(code, company_name, output_dir):
    if pd.isna(code) or str(code).strip() == "":
        return None


    code = str(code).strip()


    safe_company = "".join(
        c if c.isalnum() or c in ("_", "-") else "_"
        for c in str(company_name).strip()
    )


    safe_code = "".join(
        c if c.isalnum() or c in ("_", "-") else "_"
        for c in code
    )


    filename = f"qr_{safe_company}_{safe_code}.png"
    path = os.path.join(output_dir, filename)


    img = qrcode.make(code)
    img.save(path)


    return path

# Traitement
  
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("Fichier chargé avec succès")


        st.write("Aperçu des données :")
        st.dataframe(df.head())


        if st.button("Générer les QR Codes"):
            base_output_dir = "output"
            qr_dir = os.path.join(base_output_dir, "qr_codes")
            os.makedirs(qr_dir, exist_ok=True)


            shortcode_col = df.columns[shortcode_col_index - 1]
            company_col = df.columns[company_col_index - 1]


            df[shortcode_col] = df[shortcode_col].astype(str).str.strip()


            paths = []

            for _, row in df.iterrows():
                p = make_qr(row[shortcode_col], row[company_col], qr_dir)
                if p:
                    paths.append(p)

            # Création du ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in paths:
                    arcname = os.path.relpath(file_path, base_output_dir)
                    zipf.write(file_path, arcname=arcname)


            zip_buffer.seek(0)


            st.success(f"{len(paths)} QR codes générés avec succès")


            st.download_button(
                label="Télécharger le dossier de QR Codes (ZIP)",
                data=zip_buffer,
                file_name="qr_codes.zip",
                mime="application/zip"
            )


    except Exception as e:
        st.error(f"Erreur lors du traitement : {e}")


# Pied de page

# FOOTER
# -----------------------------
st.divider()
st.markdown(
    "<center><small>Moov Africa (GVC)  – Moov Money</small></center>",
    unsafe_allow_html=True
)

