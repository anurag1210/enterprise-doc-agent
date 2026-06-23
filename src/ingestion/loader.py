#Enterprise Loader function to Load the various 
#Importing the necessary packages
import os
import re
import pdfplumber
import pandas as pd
from langchain_core.documents import Document



def load_file(file_path: str, metadata: dict = None) -> list[Document]:
    """
    Load any supported file format (PDF, TXT/MD, CSV, Excel) and return a list[Document].
    - PDF: one Document per page
    - TXT/MD: one Document for whole file
    - CSV: one Document per row
    - Excel: one Document per sheet row (all sheets read)
    """
    documents = []
    _,file_ext = os.path.splitext(file_path)
    ext = file_ext.lower()

    base_meta={"source":file_path}
    if metadata:
        base_meta.update(metadata)

    #Handling the .pdf files
    if ext==".pdf":
        try:
            with pdfplumber.open(file_path)as pdf:
                total_pages=len(pdf.pages)
                for i,page in enumerate(pdf.pages):
                    text=page.extract_text() or ""
                    if not text:
                        continue
                    #Remove common browser PDF Header(date/time +filename)
                    text = re.sub(r'\d{2}/\d{2}/\d{4},\s*\d{2}:\d{2}\s*\S+', '', text).strip()
                    page_meta = dict(base_meta)
                    page_meta.update({"page": i, "total_pages": total_pages})
                    documents.append(Document(page_content=text, metadata=page_meta))
        except Exception as e:
            print(f"Failed to read PDF{file_path}:{e}")
            return[]
        
    #Handling the .txt, .md and .text format files
    elif ext in (".txt", ".md", ".text"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            try:
                with open(file_path, "rb") as f:
                    text = f.read().decode("utf-8", errors="ignore")
            except Exception as e:
                print(f"Failed to read text file {file_path}: {e}")
                return []
        documents.append(Document(page_content=text, metadata=base_meta))
    
    elif ext==".csv":
        try:
            #Handling CSV as strong to avoid unwanted type conversion
            df = pd.read_csv(file_path,dtype=str,keep_default_na=False)
            total_rows=len(df)
            for idx, row in df.iterrows():
               # convert row to a simple text representation
                row_text = " | ".join(f"{col}: {row[col]}" for col in row.index)
                row_meta = dict(base_meta)
                row_meta.update({"row_index": int(idx), "total_rows": int(total_rows)})
                documents.append(Document(page_content=row_text, metadata=row_meta))
        except Exception as e:
            print(f"Failed to read CSV {file_path}: {e}")
            return []
    
    elif ext in (".xls", ".xlsx", ".xlsm"):
        try:
            #Handling the xls and xlsx format files
            sheets = pd.read_excel(file_path, sheet_name=None, dtype=str)
            for sheet_name, df in sheets.items():
                df = df.fillna("")
                total_rows = len(df)
                for idx, row in df.iterrows():
                    row_text = " | ".join(f"{col}: {row[col]}" for col in row.index)
                    row_meta = dict(base_meta)
                    row_meta.update({"sheet": sheet_name, "row_index": int(idx), "total_rows": int(total_rows)})
                    documents.append(Document(page_content=row_text, metadata=row_meta))
        except Exception as e:
            print(f"Failed to read Excel {file_path}: {e}")
            return []

    else:
        print(f"Unsupported file type for {file_path}, skipping.")
        return []


    return documents

def load_all_documents(data_dir: str = "data/raw") -> list[Document]:
    """Load all supported files (PDF, TXT, CSV, Excel) from the data directory."""
    all_documents=[]
    supported_formats = ('.pdf', '.txt', '.csv', '.xlsx', '.xls','.md')
    for filename in os.listdir(data_dir):
        if filename.lower().endswith(supported_formats):
            file_path = os.path.join(data_dir, filename)

        # Adding the metadata to the document for citation purposes
            metadata = {
                "source_file": filename,
                "document_name": os.path.splitext(filename)[0].replace("_", " ").title(),
                "file_type": os.path.splitext(filename)[1].lower(),
            }
            documents=load_file(file_path, metadata)

            all_documents.extend(documents)
            print(f"Loaded {len(documents)} pages from {filename}")

    print(f"\nTotal documents loaded: {len(all_documents)}")
    return all_documents

if __name__=="__main__":
    print('Loading the PDF file to the Loader, the file format can be any of the following : PDF, TXT, CSV, Excel')
    docs = load_all_documents()
     # Print first page as a test
    if docs:
        print(f"\npage 10 preview:")
        print(f"Metadata: {docs[0].metadata}")
        print(f"Content: {docs[1].page_content[:500]}...")



