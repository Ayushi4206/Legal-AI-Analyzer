import re
import logging
from typing import Dict, List, Any
from datetime import datetime, date
import spacy
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityExtractor:
    """
    Extract key entities from legal documents including parties, dates, obligations, etc.
    """
    
    def __init__(self):
        """Initialize the entity extractor"""
        # Try to load spaCy model, fallback to rule-based extraction if not available
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.use_spacy = True
        except OSError:
            logger.warning("spaCy model not found, using rule-based extraction")
            self.nlp = None
            self.use_spacy = False
        
        # Entity extraction patterns
        self.patterns = {
            'dates': [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
            ],
            'money': [
                r'\$[\d,]+(?:\.\d{2})?',  # Dollar amounts
                r'USD\s*[\d,]+(?:\.\d{2})?',  # USD amounts
                r'INR\s*[\d,]+(?:\.\d{2})?',  # Indian Rupee amounts
                r'EUR\s*[\d,]+(?:\.\d{2})?',  # Euro amounts
                r'\b(?:dollars?|rupees?|euros?)\s*[\d,]+(?:\.\d{2})?\b'
            ],
            'percentages': [
                r'\b\d+(?:\.\d+)?%\b',  # Percentage values
                r'\b\d+(?:\.\d+)?\s*percent\b'
            ],
            'obligations': [
                r'(?:shall|must|will|required to|obligated to|agrees to)\s+[^.]{10,100}',
                r'(?:responsible for|liable for|duty to)\s+[^.]{10,100}'
            ],
            'penalties': [
                r'(?:penalty|fine|liquidated damages|late fee)\s+[^.]{10,100}',
                r'(?:breach|default|violation)\s+[^.]{10,100}'
            ],
            'termination_conditions': [
                r'(?:terminate|end|cancel|expire)\s+[^.]{10,100}',
                r'(?:upon|after|within)\s+\d+\s+days?\s+notice'
            ]
        }
        
        # Common legal entity indicators
        self.entity_indicators = {
            'company': ['LLC', 'Inc', 'Corp', 'Ltd', 'Company', 'Corporation', 'Limited', 'Partnership'],
            'person': ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.'],
            'address': ['Street', 'St.', 'Avenue', 'Ave.', 'Road', 'Rd.', 'Boulevard', 'Blvd.']
        }

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all entities from document text
        
        Args:
            text: Document text to analyze
            
        Returns:
            Dictionary containing lists of extracted entities
        """
        try:
            entities = {
                'parties': self.extract_parties(text),
                'dates': self.extract_dates(text),
                'amounts': self.extract_monetary_amounts(text),
                'obligations': self.extract_obligations(text),
                'penalties': self.extract_penalties(text),
                'addresses': self.extract_addresses(text),
                'email_addresses': self.extract_emails(text),
                'phone_numbers': self.extract_phone_numbers(text),
                'percentages': self.extract_percentages(text),
                'termination_conditions': self.extract_termination_conditions(text)
            }
            
            # Clean and deduplicate entities
            for key, value_list in entities.items():
                entities[key] = self._clean_and_deduplicate(value_list)
            
            logger.info(f"Extracted entities: {sum(len(v) for v in entities.values())} total")
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return self._get_empty_entities()

    def extract_parties(self, text: str) -> List[str]:
        """Extract party names from the document"""
        try:
            parties = []
            
            if self.use_spacy and self.nlp:
                # Use spaCy for named entity recognition
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ['PERSON', 'ORG']:
                        parties.append(ent.text.strip())
            
            # Rule-based extraction as backup or primary method
            # Look for patterns like "between [PARTY1] and [PARTY2]"
            between_pattern = r'between\s+([^,\n]+?)\s+(?:and|&)\s+([^,\n]+?)(?:\s|,|\.)'
            matches = re.findall(between_pattern, text, re.IGNORECASE)
            
            for match in matches:
                parties.extend([party.strip() for party in match])
            
            # Look for company suffixes
            for indicator in self.entity_indicators['company']:
                pattern = rf'\b([A-Z][^,\n]*?{re.escape(indicator)}[^,\n]*?)\b'
                matches = re.findall(pattern, text)
                parties.extend([match.strip() for match in matches])
            
            # Look for formal name patterns
            formal_pattern = r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
            formal_matches = re.findall(formal_pattern, text)
            parties.extend(formal_matches)
            
            return list(set([p for p in parties if len(p) > 2 and len(p) < 100]))
            
        except Exception as e:
            logger.error(f"Error extracting parties: {str(e)}")
            return []

    def extract_dates(self, text: str) -> List[str]:
        """Extract dates from the document"""
        try:
            dates = []
            
            for pattern in self.patterns['dates']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                dates.extend(matches)
            
            # Also look for relative date expressions
            relative_patterns = [
                r'\b(?:within|after|before)\s+\d+\s+(?:days?|weeks?|months?|years?)\b',
                r'\b\d+\s+(?:days?|weeks?|months?|years?)\s+(?:from|after|before)\b'
            ]
            
            for pattern in relative_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                dates.extend(matches)
            
            return list(set(dates))
            
        except Exception as e:
            logger.error(f"Error extracting dates: {str(e)}")
            return []

    def extract_monetary_amounts(self, text: str) -> List[str]:
        """Extract monetary amounts from the document"""
        try:
            amounts = []
            
            for pattern in self.patterns['money']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                amounts.extend(matches)
            
            # Also look for written amounts
            written_pattern = r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion)\s+(?:dollars?|rupees?|euros?)\b'
            written_matches = re.findall(written_pattern, text, re.IGNORECASE)
            amounts.extend(written_matches)
            
            return list(set(amounts))
            
        except Exception as e:
            logger.error(f"Error extracting monetary amounts: {str(e)}")
            return []

    def extract_obligations(self, text: str) -> List[str]:
        """Extract obligations and duties from the document"""
        try:
            obligations = []
            
            for pattern in self.patterns['obligations']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                obligations.extend([match.strip() for match in matches])
            
            # Look for specific obligation keywords
            obligation_keywords = [
                'shall provide', 'must deliver', 'required to submit',
                'responsible for maintaining', 'agrees to perform',
                'undertakes to', 'commits to', 'promises to'
            ]
            
            for keyword in obligation_keywords:
                pattern = rf'{re.escape(keyword)}\s+[^.{{50,150}}]'
                matches = re.findall(pattern, text, re.IGNORECASE)
                obligations.extend([match.strip() for match in matches])
            
            return list(set([o for o in obligations if len(o) > 10]))
            
        except Exception as e:
            logger.error(f"Error extracting obligations: {str(e)}")
            return []

    def extract_penalties(self, text: str) -> List[str]:
        """Extract penalties and consequences from the document"""
        try:
            penalties = []
            
            for pattern in self.patterns['penalties']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                penalties.extend([match.strip() for match in matches])
            
            # Look for specific penalty terms
            penalty_terms = [
                'late fee', 'interest charge', 'liquidated damages',
                'penalty clause', 'forfeiture', 'termination for cause'
            ]
            
            for term in penalty_terms:
                if term.lower() in text.lower():
                    # Extract surrounding context
                    pattern = rf'[^.]*{re.escape(term)}[^.]*'
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    penalties.extend([match.strip() for match in matches])
            
            return list(set([p for p in penalties if len(p) > 10]))
            
        except Exception as e:
            logger.error(f"Error extracting penalties: {str(e)}")
            return []

    def extract_addresses(self, text: str) -> List[str]:
        """Extract addresses from the document"""
        try:
            addresses = []
            
            # Pattern for street addresses
            address_pattern = r'\d+\s+[A-Z][^,\n]*?(?:' + '|'.join(self.entity_indicators['address']) + r')[^,\n]*'
            matches = re.findall(address_pattern, text)
            addresses.extend([match.strip() for match in matches])
            
            # Pattern for city, state, zip
            city_state_pattern = r'[A-Z][a-z]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?'
            matches = re.findall(city_state_pattern, text)
            addresses.extend(matches)
            
            return list(set(addresses))
            
        except Exception as e:
            logger.error(f"Error extracting addresses: {str(e)}")
            return []

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from the document"""
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            return list(set(emails))
            
        except Exception as e:
            logger.error(f"Error extracting emails: {str(e)}")
            return []

    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from the document"""
        try:
            phone_patterns = [
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
                r'\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',  # International
                r'\b\d{10}\b'  # Simple 10-digit
            ]
            
            phones = []
            for pattern in phone_patterns:
                matches = re.findall(pattern, text)
                phones.extend(matches)
            
            return list(set(phones))
            
        except Exception as e:
            logger.error(f"Error extracting phone numbers: {str(e)}")
            return []

    def extract_percentages(self, text: str) -> List[str]:
        """Extract percentage values from the document"""
        try:
            percentages = []
            
            for pattern in self.patterns['percentages']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                percentages.extend(matches)
            
            return list(set(percentages))
            
        except Exception as e:
            logger.error(f"Error extracting percentages: {str(e)}")
            return []

    def extract_termination_conditions(self, text: str) -> List[str]:
        """Extract termination conditions from the document"""
        try:
            conditions = []
            
            for pattern in self.patterns['termination_conditions']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                conditions.extend([match.strip() for match in matches])
            
            # Look for specific termination triggers
            termination_triggers = [
                'material breach', 'failure to pay', 'insolvency',
                'bankruptcy', 'change of control', 'mutual agreement'
            ]
            
            for trigger in termination_triggers:
                if trigger.lower() in text.lower():
                    pattern = rf'[^.]*{re.escape(trigger)}[^.]*'
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    conditions.extend([match.strip() for match in matches])
            
            return list(set([c for c in conditions if len(c) > 10]))
            
        except Exception as e:
            logger.error(f"Error extracting termination conditions: {str(e)}")
            return []

    def _clean_and_deduplicate(self, items: List[str]) -> List[str]:
        """Clean and deduplicate a list of extracted items"""
        if not items:
            return []
        
        # Clean items
        cleaned = []
        for item in items:
            if isinstance(item, str):
                # Remove extra whitespace
                cleaned_item = re.sub(r'\s+', ' ', item.strip())
                # Remove items that are too short or too long
                if 3 <= len(cleaned_item) <= 200:
                    cleaned.append(cleaned_item)
        
        # Deduplicate (case-insensitive)
        seen = set()
        deduplicated = []
        for item in cleaned:
            if item.lower() not in seen:
                seen.add(item.lower())
                deduplicated.append(item)
        
        # Sort and limit results
        deduplicated.sort()
        return deduplicated[:10]  # Limit to top 10 items per category

    def _get_empty_entities(self) -> Dict[str, List[str]]:
        """Return empty entities structure"""
        return {
            'parties': [],
            'dates': [],
            'amounts': [],
            'obligations': [],
            'penalties': [],
            'addresses': [],
            'email_addresses': [],
            'phone_numbers': [],
            'percentages': [],
            'termination_conditions': []
        }

    def get_entity_summary(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Generate a summary of extracted entities
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Summary statistics and insights
        """
        try:
            total_entities = sum(len(v) for v in entities.values())
            
            summary = {
                'total_entities_found': total_entities,
                'entity_breakdown': {k: len(v) for k, v in entities.items()},
                'has_parties': len(entities.get('parties', [])) > 0,
                'has_financial_terms': len(entities.get('amounts', [])) > 0,
                'has_deadlines': len(entities.get('dates', [])) > 0,
                'has_penalties': len(entities.get('penalties', [])) > 0,
                'complexity_score': min(10, total_entities // 2)  # Simple complexity scoring
            }
            
            # Generate insights
            insights = []
            if summary['has_parties']:
                insights.append(f"Document involves {len(entities['parties'])} parties")
            if summary['has_financial_terms']:
                insights.append(f"Contains {len(entities['amounts'])} financial terms")
            if summary['has_penalties']:
                insights.append("Document includes penalty clauses")
            if len(entities.get('obligations', [])) > 3:
                insights.append("Complex obligation structure detected")
            
            summary['insights'] = insights
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating entity summary: {str(e)}")
            return {
                'total_entities_found': 0,
                'entity_breakdown': {},
                'insights': ['Error generating summary'],
                'complexity_score': 0
            }