from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pikepdf
import io
import os
import hashlib
from PIL import Image

# Step 1: Create a basic PDF with ReportLab
def create_base_pdf(filename):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(100, 750, "Sample Text Page 1")
    can.drawString(100, 500, "Sample Text Page 2")
    can.showPage()
    can.drawString(100, 750, "Sample Text Page 3")
    can.showPage()
    can.save()
    
    # Move to the beginning of the StringIO buffer
    packet.seek(0)
    with open(filename, 'wb') as f:
        f.write(packet.read())

# Helper function to create a small valid PNG image to simulate an anomaly
def create_valid_small_image():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))  # Red square image
    img.save("small_image.png")

# Step 2: Add anomalies to the PDF
def add_anomalies(filename):
    # 1. Encrypt the PDF with both owner and user passwords using pikepdf
    encrypted_filename = "encrypted_temp.pdf"
    with pikepdf.open(filename) as pdf:
        pdf.save(encrypted_filename, encryption=pikepdf.Encryption(owner="ownerpass", user="userpass", R=4))

    # 2. Open the encrypted file and decrypt it in PyPDF2
    reader = PdfReader(encrypted_filename)
    reader.decrypt("userpass")  # Decrypt with the user password

    writer = PdfWriter()

    # Add all pages from the decrypted reader
    for page in reader.pages:
        writer.add_page(page)

    # 3. Add malformed metadata, ensuring each value is a string or handled as empty
    metadata = {
        '/Title': 'Anomalous PDF', 
        '/Producer': 'Unknown/0',
        '/Author': '',
        '/Keywords': 'test anomaly corruption\x00\x01'
    }
    writer.add_metadata({k: str(v) if v is not None else '' for k, v in metadata.items()})

    # 4. Create a missing EOF by saving without closing properly
    with open("final_anomalous_sample.pdf", 'wb') as output:
        writer.write(output)
    # Simulate missing EOF by reopening and truncating the last few bytes
    with open("final_anomalous_sample.pdf", "ab") as f:
        f.truncate(f.tell() - 10)  # Remove last 10 bytes to simulate missing EOF

    # 5. Add inconsistent object IDs by duplicating last page
    with pikepdf.open("final_anomalous_sample.pdf", allow_overwriting_input=True) as pdf:
        pdf.pages.append(pdf.pages[-1])  # Duplicate last page to create inconsistency
        pdf.save("final_anomalous_sample.pdf")

    # 6. Duplicate a page with altered content to create redundancy
    with pikepdf.open("final_anomalous_sample.pdf", allow_overwriting_input=True) as pdf:
        duplicate_page = pdf.pages[0]
        pdf.pages.append(duplicate_page)  # Duplicate first page at the end
        pdf.save("final_anomalous_sample.pdf")

    # 7. Add an empty object reference (invalid indirect object reference)
    writer.add_blank_page(width=0, height=0)  # Add a blank page with invalid size
    with open("final_anomalous_sample.pdf", 'wb') as output:
        writer.write(output)

    # 8. Insert a page with a small, valid PNG image (simulated anomaly)
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawImage("small_image.png", 100, 500, width=50, height=50)  # Insert small, valid PNG
    can.showPage()
    can.save()
    packet.seek(0)
    small_image_reader = PdfReader(packet)
    writer.add_page(small_image_reader.pages[0])
    with open("final_anomalous_sample.pdf", 'wb') as output:
        writer.write(output)

    # 9. Add inconsistent fonts between pages (simulate changing fonts between pages)
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", 12)
    can.drawString(100, 750, "Inconsistent Font Page")
    can.showPage()
    can.save()
    packet.seek(0)
    inconsistent_font_reader = PdfReader(packet)
    writer.add_page(inconsistent_font_reader.pages[0])
    with open("final_anomalous_sample.pdf", 'wb') as output:
        writer.write(output)

    # 10. Replace Font with an empty dictionary to simulate a missing font dictionary
    with pikepdf.open("final_anomalous_sample.pdf", allow_overwriting_input=True) as pdf:
        pdf.pages[0].Font = {}  # Alter font dictionary to create an invalid reference
        pdf.save("final_anomalous_sample.pdf")

    print("Anomalous PDF created: 'final_anomalous_sample.pdf'")

# Generate the base PDF
base_pdf = "base_sample.pdf"
create_base_pdf(base_pdf)

# Create a small, valid PNG image to simulate an anomaly
create_valid_small_image()

# Add anomalies
add_anomalies(base_pdf)

