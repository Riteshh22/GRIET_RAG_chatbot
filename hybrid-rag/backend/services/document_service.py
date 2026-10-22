import os
import json
from pathlib import Path
from backend.config.settings import get_settings
from backend.models.schemas import DocumentMetadata, DocumentStatus
from backend.utils.helpers import generate_id, timestamp_now


METADATA_FILE = "uploads/metadata.json"


class DocumentService:
    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_metadata_file()

    def _ensure_metadata_file(self):
        if not os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, "w") as f:
                json.dump([], f)

    def _load_metadata(self) -> list[dict]:
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_metadata(self, metadata: list[dict]):
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)

    def save_document(self, filename: str, file_content: bytes, file_type: str) -> DocumentMetadata:
        doc_id = generate_id()
        file_path = self.upload_dir / f"{doc_id}_{filename}"
        with open(file_path, "wb") as f:
            f.write(file_content)

        meta = DocumentMetadata(
            id=doc_id,
            filename=filename,
            file_type=file_type,
            file_size=len(file_content),
            status=DocumentStatus.UPLOADING,
            upload_time=timestamp_now(),
        )

        all_meta = self._load_metadata()
        all_meta.append(meta.model_dump())
        self._save_metadata(all_meta)
        return meta

    def update_document(self, doc_id: str, updates: dict) -> DocumentMetadata | None:
        all_meta = self._load_metadata()
        for i, doc in enumerate(all_meta):
            if doc["id"] == doc_id:
                all_meta[i].update(updates)
                self._save_metadata(all_meta)
                return DocumentMetadata(**all_meta[i])
        return None

    def get_document(self, doc_id: str) -> DocumentMetadata | None:
        all_meta = self._load_metadata()
        for doc in all_meta:
            if doc["id"] == doc_id:
                return DocumentMetadata(**doc)
        return None

    def list_documents(self) -> list[DocumentMetadata]:
        all_meta = self._load_metadata()
        return [DocumentMetadata(**doc) for doc in all_meta]

    def delete_document(self, doc_id: str) -> bool:
        all_meta = self._load_metadata()
        original_len = len(all_meta)
        all_meta = [doc for doc in all_meta if doc["id"] != doc_id]
        if len(all_meta) < original_len:
            self._save_metadata(all_meta)
            for f in self.upload_dir.glob(f"{doc_id}_*"):
                f.unlink(missing_ok=True)
            return True
        return False

    def get_file_path(self, doc_id: str) -> Path | None:
        for f in self.upload_dir.glob(f"{doc_id}_*"):
            return f
        return None

    def get_document_count(self) -> int:
        return len(self._load_metadata())

    def get_total_chunks(self) -> int:
        all_meta = self._load_metadata()
        return sum(doc.get("chunks", 0) for doc in all_meta)
