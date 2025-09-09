import hashlib
import os
from typing import List, Dict, Any
import pandas as pd
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from transformers import pipeline

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PERSIST_DIR = "./data/chroma_db"
COLLECTION_NAME = "terminology"


if OPENAI_API_KEY is None:
    raise ValueError("Set OPENAI_API_KEY environment variable before running.")

embeddings = OpenAIEmbeddings(model='text-embedding-3-small', dimensions=512)
vectorstore = Chroma(collection_name=COLLECTION_NAME, embedding_function=embeddings, persist_directory=PERSIST_DIR)


'''try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")
'''

nlp = pipeline(task='ner', model='dslim/distilbert-NER', aggregation_strategy = 'simple')

def merge_consecutive_ner_subtokens(tokens):
    if not tokens:
        return []

    merged_words = []

    # initialize with first token
    first = tokens[0]
    curr_group = first.get("entity_group") or first.get("entity")
    curr_word = first["word"].replace("##", "")
    curr_end = first["end"]

    for tok in tokens[1:]:
        tok_group = tok.get("entity_group") or tok.get("entity")
        tok_start = tok["start"]
        tok_end = tok["end"]
        tok_word = tok["word"].replace("##", "")

        # merge only when same group AND indices are consecutive
        if tok_group == curr_group and tok_start == curr_end:
            curr_word += tok_word
            curr_end = tok_end
        else:
            merged_words.append(curr_word)
            curr_group = tok_group
            curr_word = tok_word
            curr_end = tok_end

    # append last
    merged_words.append(curr_word)
    return merged_words

def extract_named_entities(text: str) -> List[str]:
    """Return list of unique named entities from text using hugging face transformers."""
    ner = nlp(text)
    return merge_consecutive_ner_subtokens(ner)


def build_document_text(line_item:str, others:dict) -> str:
    """Concatenate the item, categories into a text blob."""
    text = f"{line_item} || " + " || ".join([f'{key} is {value}' for key, value in others.items()])
    return text


def ingest_csv_file(csv_file_path,line_item_col, other_req_col):
    for chunk_df in pd.read_csv(csv_file_path,chunksize=1000):
        unique_rows_df = chunk_df.drop_duplicates(subset=[line_item_col]+other_req_col)
        documents = []
        for _, row in unique_rows_df.iterrows():
            text = build_document_text(row[line_item_col], {col:row[col] for col in other_req_col})
            id_ = hashlib.sha1(text.encode("utf-8")).hexdigest()

            exists = vectorstore._collection.get(ids=[id_])
            if exists and exists.get('ids'):
                # print(f'exists:{exists}')

                doc_metadata = exists.get('metadatas')[0]
                existing_context = [con.strip() for con in doc_metadata['context'].split(',')]
                current_context = os.path.basename(csv_file_path).rsplit('.', 1)[0]
                if current_context not in existing_context:
                    doc_metadata['context'] += ', '+ current_context

                    updated_doc = Document(
                        page_content=text,
                        metadata= doc_metadata,
                        id= id_
                    )
                    vectorstore.update_document(document_id = id_, document=updated_doc)

            else:
                ner = extract_named_entities(row[line_item_col])
                metadata = {
                    "line_item": row[line_item_col],
                    "context":os.path.basename(csv_file_path).rsplit('.', 1)[0],
                    "ner": '|'.join(ner),
                    }
                metadata.update({col:row[col] for col in other_req_col})

                documents.append(Document(
                    page_content= text,
                    metadata=metadata,
                    id=id_,
                ))
        if documents:
            vectorstore.add_documents(documents)

    print(f"all rows of {csv_file_path} are added to the vectorstore")


def create_initial_index():
    ingest_csv_file('./data/CSVs/BalanceSheet.csv', 'Line Item', ['SubCategory','SubSubCategory'])
    ingest_csv_file('./data/CSVs/CashFlowStatement.csv', 'Item',	['Category'])
    ingest_csv_file('./data/CSVs/Consolidated PnL.csv', 'Line Item', [])
    ingest_csv_file('./data/CSVs/Quarterly PnL.csv', 'Item', ['Category'])
    ingest_csv_file('./data/CSVs/ROCE External.csv', 'Particular', [])
    ingest_csv_file('./data/CSVs/ROCE Internal.csv', 'Line Item',['Category'])



if __name__ == "__main__":
    create_initial_index()
