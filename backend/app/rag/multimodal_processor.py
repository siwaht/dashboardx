"""
Multi-Modal Document Processor

Handles extraction and processing of various document formats including:
- Images (OCR, visual understanding)
- Tables (from PDFs and images)
- Audio (transcription)
- Video (frame extraction and analysis)
- Charts and graphs
"""

import logging
import io
import tempfile
from typing import List, Dict, Any, Optional, Union, BinaryIO
from pathlib import Path
from enum import Enum
import base64

# Core libraries
import numpy as np
from PIL import Image
import cv2

# OCR and text extraction
try:
    import pytesseract
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not available. Install with: pip install easyocr")

# Table extraction
try:
    import camelot
    import tabula
    TABLE_EXTRACTION_AVAILABLE = True
except ImportError:
    TABLE_EXTRACTION_AVAILABLE = False
    logging.warning("Table extraction libraries not available")

# PDF processing
try:
    from pdf2image import convert_from_path, convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logging.warning("pdf2image not available")

# Transformers for visual understanding
try:
    from transformers import (
        CLIPProcessor, CLIPModel,
        BlipProcessor, BlipForConditionalGeneration,
        AutoProcessor, AutoModelForCausalLM
    )
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available for visual understanding")

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Supported document types"""
    IMAGE = "image"
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"
    TABLE = "table"
    CHART = "chart"
    TEXT = "text"
    UNKNOWN = "unknown"


class ExtractionMethod(str, Enum):
    """Extraction methods"""
    OCR_TESSERACT = "ocr_tesseract"
    OCR_EASYOCR = "ocr_easyocr"
    TABLE_CAMELOT = "table_camelot"
    TABLE_TABULA = "table_tabula"
    VISUAL_CLIP = "visual_clip"
    VISUAL_BLIP = "visual_blip"
    AUDIO_WHISPER = "audio_whisper"


class MultiModalProcessor:
    """
    Multi-Modal Document Processor
    
    Handles extraction and processing of various document formats
    with intelligent format detection and fallback mechanisms.
    """
    
    def __init__(
        self,
        use_gpu: bool = False,
        ocr_languages: List[str] = None
    ):
        """
        Initialize multi-modal processor
        
        Args:
            use_gpu: Use GPU for processing if available
            ocr_languages: Languages for OCR (default: ['en'])
        """
        self.use_gpu = use_gpu and torch.cuda.is_available() if TRANSFORMERS_AVAILABLE else False
        self.device = "cuda" if self.use_gpu else "cpu"
        self.ocr_languages = ocr_languages or ['en']
        
        # Initialize models lazily
        self._clip_model = None
        self._clip_processor = None
        self._blip_model = None
        self._blip_processor = None
        self._easyocr_reader = None
        
        logger.info(f"MultiModalProcessor initialized (device: {self.device})")
    
    def detect_document_type(
        self,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None
    ) -> DocumentType:
        """
        Detect document type from file
        
        Args:
            file_path: Path to file
            file_bytes: File bytes
            mime_type: MIME type hint
            
        Returns:
            Detected document type
        """
        # Check MIME type first
        if mime_type:
            if mime_type.startswith('image/'):
                return DocumentType.IMAGE
            elif mime_type == 'application/pdf':
                return DocumentType.PDF
            elif mime_type.startswith('audio/'):
                return DocumentType.AUDIO
            elif mime_type.startswith('video/'):
                return DocumentType.VIDEO
        
        # Check file extension
        if file_path:
            ext = Path(file_path).suffix.lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                return DocumentType.IMAGE
            elif ext == '.pdf':
                return DocumentType.PDF
            elif ext in ['.mp3', '.wav', '.m4a', '.flac']:
                return DocumentType.AUDIO
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                return DocumentType.VIDEO
        
        return DocumentType.UNKNOWN
    
    async def process_document(
        self,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        extract_tables: bool = True,
        extract_images: bool = True,
        generate_captions: bool = True
    ) -> Dict[str, Any]:
        """
        Process document and extract all content
        
        Args:
            file_path: Path to document
            file_bytes: Document bytes
            mime_type: MIME type
            extract_tables: Extract tables from document
            extract_images: Extract images from document
            generate_captions: Generate captions for images
            
        Returns:
            Extracted content with metadata
        """
        try:
            doc_type = self.detect_document_type(file_path, file_bytes, mime_type)
            
            logger.info(f"Processing document of type: {doc_type}")
            
            if doc_type == DocumentType.IMAGE:
                return await self.process_image(file_path, file_bytes, generate_captions)
            
            elif doc_type == DocumentType.PDF:
                return await self.process_pdf(
                    file_path, file_bytes,
                    extract_tables, extract_images, generate_captions
                )
            
            elif doc_type == DocumentType.AUDIO:
                return await self.process_audio(file_path, file_bytes)
            
            elif doc_type == DocumentType.VIDEO:
                return await self.process_video(file_path, file_bytes, generate_captions)
            
            else:
                return {
                    "type": doc_type,
                    "text": "",
                    "error": "Unsupported document type"
                }
                
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            return {
                "type": DocumentType.UNKNOWN,
                "text": "",
                "error": str(e)
            }
    
    async def process_image(
        self,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        generate_caption: bool = True
    ) -> Dict[str, Any]:
        """
        Process image: OCR + visual understanding
        
        Args:
            file_path: Path to image
            file_bytes: Image bytes
            generate_caption: Generate image caption
            
        Returns:
            Extracted text and metadata
        """
        try:
            # Load image
            if file_bytes:
                image = Image.open(io.BytesIO(file_bytes))
            elif file_path:
                image = Image.open(file_path)
            else:
                raise ValueError("Either file_path or file_bytes must be provided")
            
            result = {
                "type": DocumentType.IMAGE,
                "text": "",
                "metadata": {
                    "width": image.width,
                    "height": image.height,
                    "format": image.format
                }
            }
            
            # Extract text using OCR
            ocr_text = await self.extract_text_from_image(image)
            result["text"] = ocr_text
            result["metadata"]["ocr_method"] = "tesseract"
            
            # Generate caption if requested
            if generate_caption and TRANSFORMERS_AVAILABLE:
                caption = await self.generate_image_caption(image)
                result["metadata"]["caption"] = caption
            
            # Detect if image contains tables or charts
            contains_table = await self.detect_table_in_image(image)
            result["metadata"]["contains_table"] = contains_table
            
            if contains_table:
                # Try to extract table structure
                table_data = await self.extract_table_from_image(image)
                if table_data:
                    result["tables"] = [table_data]
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            return {
                "type": DocumentType.IMAGE,
                "text": "",
                "error": str(e)
            }
    
    async def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from image using OCR
        
        Args:
            image: PIL Image
            
        Returns:
            Extracted text
        """
        try:
            # Try Tesseract first (faster)
            text = pytesseract.image_to_string(image)
            
            # If Tesseract returns little text, try EasyOCR (more accurate)
            if len(text.strip()) < 10 and EASYOCR_AVAILABLE:
                if self._easyocr_reader is None:
                    self._easyocr_reader = easyocr.Reader(self.ocr_languages)
                
                # Convert PIL to numpy array
                img_array = np.array(image)
                results = self._easyocr_reader.readtext(img_array)
                text = ' '.join([result[1] for result in results])
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error in OCR: {e}")
            return ""
    
    async def generate_image_caption(self, image: Image.Image) -> str:
        """
        Generate caption for image using BLIP
        
        Args:
            image: PIL Image
            
        Returns:
            Generated caption
        """
        try:
            if not TRANSFORMERS_AVAILABLE:
                return ""
            
            # Initialize BLIP model lazily
            if self._blip_model is None:
                self._blip_processor = BlipProcessor.from_pretrained(
                    "Salesforce/blip-image-captioning-base"
                )
                self._blip_model = BlipForConditionalGeneration.from_pretrained(
                    "Salesforce/blip-image-captioning-base"
                ).to(self.device)
            
            # Generate caption
            inputs = self._blip_processor(image, return_tensors="pt").to(self.device)
            outputs = self._blip_model.generate(**inputs, max_length=50)
            caption = self._blip_processor.decode(outputs[0], skip_special_tokens=True)
            
            return caption
            
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return ""
    
    async def detect_table_in_image(self, image: Image.Image) -> bool:
        """
        Detect if image contains a table
        
        Args:
            image: PIL Image
            
        Returns:
            True if table detected
        """
        try:
            # Convert to grayscale
            img_array = np.array(image.convert('L'))
            
            # Detect horizontal and vertical lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            horizontal_lines = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, vertical_kernel)
            
            # If we detect both horizontal and vertical lines, likely a table
            h_count = np.sum(horizontal_lines > 0)
            v_count = np.sum(vertical_lines > 0)
            
            return h_count > 1000 and v_count > 1000
            
        except Exception as e:
            logger.error(f"Error detecting table: {e}")
            return False
    
    async def extract_table_from_image(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """
        Extract table structure from image
        
        Args:
            image: PIL Image
            
        Returns:
            Table data or None
        """
        try:
            # This is a simplified version
            # In production, use specialized table extraction models
            text = await self.extract_text_from_image(image)
            
            # Try to parse as table (basic heuristic)
            lines = text.split('\n')
            if len(lines) > 2:
                return {
                    "rows": len(lines),
                    "text": text,
                    "method": "ocr_based"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting table from image: {e}")
            return None
    
    async def process_pdf(
        self,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        extract_tables: bool = True,
        extract_images: bool = True,
        generate_captions: bool = True
    ) -> Dict[str, Any]:
        """
        Process PDF: extract text, tables, and images
        
        Args:
            file_path: Path to PDF
            file_bytes: PDF bytes
            extract_tables: Extract tables
            extract_images: Extract images
            generate_captions: Generate captions for images
            
        Returns:
            Extracted content
        """
        try:
            result = {
                "type": DocumentType.PDF,
                "text": "",
                "tables": [],
                "images": [],
                "metadata": {}
            }
            
            # Extract tables using Camelot (for PDFs with clear table structure)
            if extract_tables and TABLE_EXTRACTION_AVAILABLE and file_path:
                try:
                    tables = camelot.read_pdf(file_path, pages='all')
                    for i, table in enumerate(tables):
                        result["tables"].append({
                            "index": i,
                            "data": table.df.to_dict('records'),
                            "method": ExtractionMethod.TABLE_CAMELOT
                        })
                except Exception as e:
                    logger.warning(f"Camelot extraction failed: {e}")
                    
                    # Fallback to Tabula
                    try:
                        if file_path:
                            tables = tabula.read_pdf(file_path, pages='all')
                            for i, table in enumerate(tables):
                                result["tables"].append({
                                    "index": i,
                                    "data": table.to_dict('records'),
                                    "method": ExtractionMethod.TABLE_TABULA
                                })
                    except Exception as e2:
                        logger.warning(f"Tabula extraction failed: {e2}")
            
            # Convert PDF pages to images for OCR
            if PDF2IMAGE_AVAILABLE:
                if file_bytes:
                    images = convert_from_bytes(file_bytes)
                elif file_path:
                    images = convert_from_path(file_path)
                else:
                    images = []
                
                all_text = []
                for i, img in enumerate(images):
                    # Extract text from each page
                    page_text = await self.extract_text_from_image(img)
                    all_text.append(f"[Page {i+1}]\n{page_text}")
                    
                    # Optionally extract images
                    if extract_images:
                        result["images"].append({
                            "page": i + 1,
                            "image": img,
                            "caption": await self.generate_image_caption(img) if generate_captions else None
                        })
                
                result["text"] = "\n\n".join(all_text)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            return {
                "type": DocumentType.PDF,
                "text": "",
                "error": str(e)
            }
    
    async def process_audio(
        self,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Process audio: transcription
        
        Note: Requires Whisper or similar ASR model
        This is a placeholder - implement with actual ASR
        
        Args:
            file_path: Path to audio
            file_bytes: Audio bytes
            
        Returns:
            Transcription
        """
        try:
            # Placeholder for Whisper integration
            # In production, use: openai.Audio.transcribe()
            
            return {
                "type": DocumentType.AUDIO,
                "text": "[Audio transcription not yet implemented]",
                "metadata": {
                    "note": "Install openai-whisper for audio transcription"
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return {
                "type": DocumentType.AUDIO,
                "text": "",
                "error": str(e)
            }
    
    async def process_video(
        self,
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        generate_captions: bool = True,
        frame_interval: int = 30
    ) -> Dict[str, Any]:
        """
        Process video: extract frames and analyze
        
        Args:
            file_path: Path to video
            file_bytes: Video bytes
            generate_captions: Generate captions for frames
            frame_interval: Extract every Nth frame
            
        Returns:
            Extracted content
        """
        try:
            if not file_path:
                # Save bytes to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                    tmp.write(file_bytes)
                    file_path = tmp.name
            
            # Open video
            cap = cv2.VideoCapture(file_path)
            
            frames = []
            frame_count = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    frame_data = {
                        "frame_number": frame_count,
                        "timestamp": frame_count / cap.get(cv2.CAP_PROP_FPS)
                    }
                    
                    if generate_captions:
                        caption = await self.generate_image_caption(pil_image)
                        frame_data["caption"] = caption
                    
                    frames.append(frame_data)
                
                frame_count += 1
            
            cap.release()
            
            return {
                "type": DocumentType.VIDEO,
                "text": "\n".join([f"[{f['timestamp']:.2f}s] {f.get('caption', '')}" for f in frames]),
                "frames": frames,
                "metadata": {
                    "total_frames": frame_count,
                    "extracted_frames": len(frames)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return {
                "type": DocumentType.VIDEO,
                "text": "",
                "error": str(e)
            }


# Export
__all__ = ["MultiModalProcessor", "DocumentType", "ExtractionMethod"]
