"""Text splitter for large documents with multiple STIX objects."""
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class STIXDocumentSplitter:
    """Split large documents into manageable chunks for STIX processing."""
    
    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """Initialize the splitter.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between chunks
            separators: Custom separators for splitting
        """
        if separators is None:
            # Use separators that make sense for penetration test reports
            separators = [
                "\n\n## ",  # Markdown headers
                "\n\n# ",   # Markdown headers
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentences
                " ",       # Words
                ""         # Characters
            ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
        )
    
    def split_document(self, text: str, metadata: dict = None) -> List[Document]:
        """Split a document into chunks.
        
        Args:
            text: The full document text
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of Document chunks
        """
        chunks = self.splitter.create_documents([text])
        
        # Add metadata and chunk index
        for i, chunk in enumerate(chunks):
            if metadata:
                chunk.metadata.update(metadata)
            chunk.metadata['chunk_index'] = i
            chunk.metadata['total_chunks'] = len(chunks)
        
        return chunks
    
    def split_by_sections(self, text: str, metadata: dict = None) -> List[Document]:
        """Split document by logical sections (vulnerabilities, attacks, etc.).
        
        Args:
            text: The full document text
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of Document chunks organized by sections
        """
        # Try to identify sections
        sections = []
        current_section = []
        current_title = "Introduction"
        
        lines = text.split('\n')
        
        for line in lines:
            # Detect section headers
            if line.strip().startswith('#') or line.strip().endswith(':'):
                if current_section:
                    sections.append({
                        'title': current_title,
                        'content': '\n'.join(current_section)
                    })
                current_title = line.strip().lstrip('#').strip()
                current_section = [line]
            else:
                current_section.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                'title': current_title,
                'content': '\n'.join(current_section)
            })
        
        # Convert to Documents
        documents = []
        for i, section in enumerate(sections):
            doc = Document(
                page_content=section['content'],
                metadata={
                    'section_title': section['title'],
                    'section_index': i,
                    'total_sections': len(sections)
                }
            )
            if metadata:
                doc.metadata.update(metadata)
            documents.append(doc)
        
        return documents if documents else self.split_document(text, metadata)

