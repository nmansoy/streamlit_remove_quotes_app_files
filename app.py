import io
import os
import csv
import zipfile
from datetime import datetime
import streamlit as st

st.set_page_config(page_title='CSV Icindeki Tirnaklari Kaldir', layout="centered")
st.title('🧹 CSV icindeki " karakterlerini kaldir')

st.markdown("""
Bu uygulama yukledigin CSV dosyalarinin (veya CSV iceren bir ZIP'in) icindeki **cift tirnak** (`"`) karakterlerini
hucrelerden siler.

- Degisiklik olan dosyalar: `modified_<orijinal_ad>.csv`
- Degisiklik olmayanlar raporda listelenir
- Sonuclar tek bir ZIP olarak indirilebilir (icinde rapor + tum ciktular)
""")

source_mode = st.radio(
    "Girdi turu",
    ["CSV dosyalari yukle (coklu)", "CSV iceren ZIP yukle (alt klasorler dahil)"],
    horizontal=True
)

auto_sniff = st.checkbox("Ayiriciyi otomatik algila (csv.Sniffer)", value=True)
encoding = st.selectbox("Dosya encoding", ["utf-8", "utf-8-sig", "cp1254", "latin-1"], index=1)

def process_csv_bytes(data: bytes, filename: str, *, auto_sniff: bool, encoding: str):
    """
    Returns:
      out_bytes (bytes): modified CSV content (written as utf-8)
      modified (bool)
      lines_modified (int)
      error (str|None)
    """
    try:
        text = data.decode(encoding, errors="replace")
        sample = text[:4096]

        if auto_sniff:
            try:
                dialect = csv.Sniffer().sniff(sample)
            except Exception:
                dialect = csv.excel
        else:
            dialect = csv.excel

        infile = io.StringIO(text, newline="")
        reader = csv.reader(infile, dialect)

        new_rows = []
        modified = False
        lines_modified = 0

        for row in reader:
            new_row = [cell.replace('"', "") for cell in row]
            new_rows.append(new_row)
            if new_row != row:
                modified = True
                lines_modified += 1

        out_buf = io.StringIO(newline="")
        writer = csv.writer(out_buf, dialect)
        writer.writerows(new_rows)
        out_text = out_buf.getvalue()

        return out_text.encode("utf-8"), modified, lines_modified, None
    except Exception as e:
        return b"", False, 0, f"{filename}: {e}"

def iter_csv_from_uploaded_zip(zip_bytes: bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        for name in zf.namelist():
            if name.lower().endswith(".csv") and not name.endswith("/"):
                yield name, zf.read(name)

def build_output_zip(results, report_text: str):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("rapor.txt", report_text)
        for out_name, out_bytes in results:
            z.writestr(out_name, out_bytes)
    out.seek(0)
    return out.getvalue()

timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

modified_lines = []
unchanged_lines = []
errors = []
output_files = []  # (name, bytes)

if source_mode == "CSV dosyalari yukle (coklu)":
    uploaded = st.file_uploader("CSV dosyalarini yukle", type=["csv"], accept_multiple_files=True)
    if uploaded:
        for up in uploaded:
            data = up.read()
            out_bytes, modified, lines_modified, err = process_csv_bytes(
                data, up.name, auto_sniff=auto_sniff, encoding=encoding
            )
            if err:
                errors.append(err)
                continue

            out_name = f"modified_{os.path.basename(up.name)}"
            output_files.append((out_name, out_bytes))

            if modified:
                modified_lines.append(f"{up.name} dosyasinda {lines_modified} satirda '"' karakteri silindi.")
            else:
                unchanged_lines.append(f"{up.name} dosyasinda degisiklik yapilmadi.")
else:
    upzip = st.file_uploader("CSV iceren ZIP dosyasini yukle", type=["zip"], accept_multiple_files=False)
    if upzip is not None:
        zip_bytes = upzip.read()
        try:
            found_any = False
            for member_name, member_bytes in iter_csv_from_uploaded_zip(zip_bytes):
                found_any = True
                base_name = os.path.basename(member_name)

                out_bytes, modified, lines_modified, err = process_csv_bytes(
                    member_bytes, member_name, auto_sniff=auto_sniff, encoding=encoding
                )
                if err:
                    errors.append(err)
                    continue

                folder = os.path.dirname(member_name)
                out_file_name = f"modified_{base_name}"
                out_name = os.path.join(folder, out_file_name) if folder else out_file_name

                output_files.append((out_name, out_bytes))

                if modified:
                    modified_lines.append(f"{member_name} dosyasinda {lines_modified} satirda '"' karakteri silindi.")
                else:
                    unchanged_lines.append(f"{member_name} dosyasinda degisiklik yapilmadi.")

            if not found_any:
                st.warning("ZIP icinde CSV bulunamadi.")
        except zipfile.BadZipFile:
            st.error("Gecersiz veya bozuk ZIP dosyasi.")
        except Exception as e:
            st.error(f"Hata: {e}")

if output_files or errors or modified_lines or unchanged_lines:
    report = []
    report.append("CSV Dosyalarinda Yapilan Degisiklikler:\n\n")
    report.append(f"Zaman: {timestamp}\n")

    if modified_lines:
        report.append("\nDegisiklik Yapilan Dosyalar:\n")
        report.extend([line + "\n" for line in modified_lines])

    if unchanged_lines:
        report.append("\nDegisiklik Yapilmayan Dosyalar:\n")
        report.extend([line + "\n" for line in unchanged_lines])

    if errors:
        report.append("\nHatalar:\n")
        report.extend([line + "\n" for line in errors])

    report_text = "".join(report)

    st.subheader("📄 Rapor")
    st.text(report_text)

    if output_files:
        out_zip_bytes = build_output_zip(output_files, report_text)
        st.download_button(
            "📥 Ciktilari indir (ZIP)",
            data=out_zip_bytes,
            file_name=f"modified_csvler_{timestamp}.zip",
            mime="application/zip"
        )

        with st.expander("Tek tek dosya indirme"):
            for name, b in output_files:
                st.download_button(
                    f"⬇️ {name}",
                    data=b,
                    file_name=os.path.basename(name),
                    mime="text/csv",
                    key=f"dl_{name}"
                )
