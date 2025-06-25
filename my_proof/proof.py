import os
import hashlib
import json
import logging
from typing import Dict, Any

from langdetect import detect, lang_detect_exception

from .models.proof_response import ProofResponse

# Constants for validation
MIN_TEXT_LENGTH = 50
MAX_TEXT_LENGTH = 5000


class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])

    def generate(self) -> ProofResponse:
        """
        Generate a proof for a single text file input, validating it for the Hindi DataDAO.
        """
        logging.info("Starting Hindi text proof generation")
        
        # --- Find the first text file to process ---
        text_content = None
        file_to_process = None

        logging.info("Hi")

        for filename in os.listdir(self.config['input_dir']):
            # This logic assumes the first non-JSON file is the text to be validated
           
            if not filename.endswith('.json'):
                file_to_process = os.path.join(self.config['input_dir'], filename)
                logging.info(file_to_process)
                break # Process only the first valid file found

        if not file_to_process:
            logging.error("No text file found in input directory to process.")
            self.proof_response.valid = False
            self.proof_response.attributes['error'] = 'No text file found for validation.'
            return self.proof_response
            
        with open(file_to_process, "r", encoding="utf-8") as f:
            text_content = f.read()

        # --- 1. Authenticity Check: Is the language Hindi? ---
        is_hindi = False
        language_detected = "unknown"
        try:
            language_detected = detect(text_content)
            if language_detected == "hi":
                is_hindi = True
        except lang_detect_exception.LangDetectException:
            is_hindi = False
            language_detected = "detection_failed"

        # --- 2. Quality Check: Is the text of reasonable length? ---
        content_length = len(text_content)
        is_good_length = MIN_TEXT_LENGTH <= content_length <= MAX_TEXT_LENGTH

        # --- 3. Uniqueness Check: Generate a hash of the content ---
        content_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
        is_unique = True  # Placeholder: In production, check this hash against a database

        # --- Final Validation ---
        self.proof_response.valid = is_hindi and is_good_length and is_unique
        
        # --- Populate Scores and Attributes ---
        self.proof_response.score = 1.0 if self.proof_response.valid else 0.0
        self.proof_response.ownership = 1.0 # Assuming ownership if it passes other checks
        self.proof_response.authenticity = 1.0 if is_hindi else 0.0
        self.proof_response.quality = 1.0 if is_good_length else 0.0
        self.proof_response.uniqueness = 1.0 if is_unique else 0.0

        self.proof_response.attributes = {
            "language_detected": language_detected,
            "is_hindi": is_hindi,
            "content_length": content_length,
            "is_good_length": is_good_length,
            "content_hash": content_hash,
            "min_length_required": MIN_TEXT_LENGTH,
            "max_length_allowed": MAX_TEXT_LENGTH,
        }

        self.proof_response.metadata = {
            'dlp_id': self.config['dlp_id'],
        }

        return self.proof_response
