from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.tools import tool
import config
from dotenv import load_dotenv
from typing import List

load_dotenv()

embeddings = OpenAIEmbeddings(model='text-embedding-3-small', dimensions=512)
vectorstore = Chroma(collection_name=config.VDB_COLLECTION_NAME, embedding_function=embeddings, persist_directory=config.VDB_PERSIST_DIR)

@tool
def get_canonical_line_items(queries:List[str]):
    """Gives the relevant line items semantic to the given queries.
    Example line items in the output will be 'Net Gain on Sale of Current Investments', 'Profit before Tax', 'Loans to Joint Venture Entities' etc"""

    retriever = vectorstore.as_retriever()
    result_docs = []
    for query in queries:
        result_docs.extend(retriever.invoke(query, k=config.VDB_TOP_K_VALUE))

    output = ''
    for doc in result_docs:
        output += '\n' + str(doc.metadata)

    return f'''Related canonical line items relevant to the query are:
        {output}
        '''


if __name__ == '__main__':
    print(get_canonical_line_items('What is the sum of total loans given to joint ventures in FY 2023-24?'))