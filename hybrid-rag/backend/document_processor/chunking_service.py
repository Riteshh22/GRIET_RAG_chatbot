from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.config.settings import get_settings
from backend.models.schemas import ChunkData
from backend.utils.helpers import generate_id


class ChunkingService:
    def __init__(self):
        self.settings = get_settings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.CHUNK_SIZE,
            chunk_overlap=self.settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_document(
        self,
        text: str,
        document_id: str,
        document_name: str,
        page_number: int = 0,
    ) -> list[ChunkData]:
        text_chunks = self.text_splitter.split_text(text)
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            if not chunk_text.strip():
                continue
            chunk = ChunkData(
                id=generate_id(),
                content=chunk_text.strip(),
                document_id=document_id,
                document_name=document_name,
                page_number=page_number,
                chunk_index=i,
                metadata={
                    "document_id": document_id,
                    "document_name": document_name,
                    "page_number": page_number,
                    "chunk_index": i,
                },
            )
            chunks.append(chunk)
        return chunks

    def chunk_pages(
        self,
        pages: list[dict],
        document_id: str,
        document_name: str,
    ) -> list[ChunkData]:
        all_chunks = []
        for page in pages:
            page_num = page.get("page_number", 0)
            text = page.get("content", "")
            if text.strip():
                chunks = self.chunk_document(
                    text, document_id, document_name, page_num
                )
                all_chunks.extend(chunks)
        return all_chunks

    def update_chunk_size(self, chunk_size: int, chunk_overlap: int):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
