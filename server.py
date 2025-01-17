# server.py
import os
import shutil
import random
from magic_pdf.data.data_reader_writer import FileBasedDataWriter
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
import docxpy
import io
import rpyc
import time
from concurrent.futures import ProcessPoolExecutor
import tempfile

def process_pdf_ai(pdf_bytes: bytes, pdf_file_name: str = "abc.pdf") -> str:
    """
    Process the given PDF (as bytes), produce an .md file from it, 
    read its contents, remove the output folder, and return the text.
    """

    # 1. Prepare environment: create 'output' and 'output/images'
    output_dir = f"output_{random.randint(0, 1000000)}"
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # 2. Derive the markdown filename from the PDF filename
    name_without_suffix = os.path.splitext(pdf_file_name)[0]
    md_filename = f"{name_without_suffix}.md"

    # 3. Prepare FileBasedDataWriter objects
    image_writer = FileBasedDataWriter(images_dir)
    md_writer = FileBasedDataWriter(output_dir)

    # 4. Create dataset instance from PDF bytes
    ds = PymuDocDataset(pdf_bytes)

    # 5. Apply model analyze -> pipe_ocr_mode -> dump_md
    #    This step will create the .md file in 'output/'
    ds.apply(doc_analyze, ocr=True) \
      .pipe_ocr_mode(image_writer) \
      .dump_md(md_writer, md_filename, os.path.basename(images_dir))

    # 6. Read the generated .md file
    md_path = os.path.join(output_dir, md_filename)
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 7. Remove the entire output directory
    shutil.rmtree(output_dir)

    # 8. Return the .md text
    return md_content


def extract_docx_from_bytes(docx_bytes):
    # Create a temp file with a .docx suffix
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(docx_bytes)
        tmp.flush()
        temp_path = tmp.name

    # Now pass the path to docxpy
    try:
        text = docxpy.process(temp_path)
    finally:
        # Clean up the temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return text



executor = ProcessPoolExecutor(max_workers=4)

class MyService(rpyc.Service):
    def exposed_md_conversion(self, file_bytes, filename):
        future = executor.submit(md_conversion_worker, file_bytes, filename)
        return future.result()

def md_conversion_worker(file_bytes, filename):
    # This function runs in a separate process, so no GIL contention with others
    return process_file(file_bytes, filename)


def process_file(file_bytes, filename):
    # Make the check case-insensitive by using .lower()
    if filename.lower().endswith('.pdf'):
        return process_pdf_ai(file_bytes, filename)
    elif filename.lower().endswith('.docx'):
        return extract_docx_from_bytes(file_bytes)
    else:
        raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")


if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(MyService, port=18812)
    print("Server started on port 18812")
    server.start()
