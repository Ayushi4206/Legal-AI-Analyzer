import logging
import re
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime

# Note: In production, you would use actual AI APIs like:
# - Google Gemini API
# - OpenAI API
# - Anthropic Claude API
# For this demo, we'll use mock responses with realistic legal analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAnalyzer:
    """
    AI-powered legal document analyzer using Gemini API or similar
    """
    
    def __init__(self):
        """Initialize the AI analyzer"""
        self.api_key = None  # Set your API key here
        self.model_name = "gemini-pro"  # or your preferred model
        
        # Legal clause patterns for identification
        self.clause_patterns = {
            'termination': [
                r'terminat\w*', r'end\s+(?:of\s+)?(?:this\s+)?(?:agreement|contract)',
                r'expire\w*', r'dissolution', r'cancell\w*'
            ],
            'liability': [
                r'liabilit\w*', r'responsible\w*', r'damages?', r'loss\w*',
                r'indemnif\w*', r'hold\s+harmless'
            ],
            'payment': [
                r'payment\w*', r'pay\w*', r'fee\w*', r'cost\w*', r'price\w*',
                r'invoice\w*', r'billing', r'charge\w*'
            ],
            'confidentiality': [
                r'confidential\w*', r'non.?disclosure', r'proprietary',
                r'trade\s+secret\w*', r'private\w*'
            ],
            'intellectual_property': [
                r'intellectual\s+property', r'copyright\w*', r'trademark\w*',
                r'patent\w*', r'ownership'
            ],
            'dispute_resolution': [
                r'dispute\w*', r'arbitration', r'mediation', r'court\w*',
                r'jurisdiction', r'governing\s+law'
            ]
        }
        
        # Risk keywords that indicate higher risk
        self.high_risk_keywords = [
            'unlimited liability', 'personal guarantee', 'no refund',
            'immediate termination', 'sole discretion', 'without cause',
            'liquidated damages', 'penalty', 'forfeiture'
        ]
        
        self.medium_risk_keywords = [
            'limited liability', 'reasonable notice', 'material breach',
            'cure period', 'mutual agreement', 'standard terms'
        ]

    async def analyze_document(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Analyze legal document using AI
        
        Args:
            text: Extracted document text
            filename: Original filename
            
        Returns:
            Analysis results including clauses, summaries, and risk assessment
        """
        try:
            logger.info(f"Starting AI analysis for {filename}")
            
            # Split text into sections/clauses
            sections = self._split_into_clauses(text)
            
            # Analyze each clause
            analyzed_clauses = []
            for i, section in enumerate(sections):
                if len(section.strip()) > 50:  # Only analyze substantial sections
                    clause_analysis = await self._analyze_clause(section, i)
                    analyzed_clauses.append(clause_analysis)
            
            # Generate document summary
            summary = await self._generate_summary(text, filename)
            
            result = {
                'summary': summary,
                'clauses': analyzed_clauses,
                'analysis_timestamp': datetime.now().isoformat(),
                'document_type': self._detect_document_type(text)
            }
            
            logger.info(f"Completed analysis for {filename} - found {len(analyzed_clauses)} clauses")
            return result
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {
                'summary': f'Error analyzing document: {str(e)}',
                'clauses': [],
                'analysis_timestamp': datetime.now().isoformat(),
                'document_type': 'unknown'
            }
    
    def _split_into_clauses(self, text: str) -> List[str]:
        """
        Split document text into individual clauses
        """
        try:
            # Split by common clause separators
            clause_separators = [
                r'\n\s*\d+\.\s+',  # Numbered clauses like "1. "
                r'\n\s*\([a-z]\)\s+',  # Lettered clauses like "(a) "
                r'\n\s*[A-Z\s]{3,}:\s*\n',  # All caps headers
                r'\n\s*SECTION\s+\d+',  # Section headers
                r'\n\s*ARTICLE\s+\d+',  # Article headers
            ]
            
            import re
            sections = [text]  # Start with full text
            
            for pattern in clause_separators:
                new_sections = []
                for section in sections:
                    parts = re.split(pattern, section)
                    new_sections.extend([p.strip() for p in parts if p.strip()])
                sections = new_sections
            
            # Filter out very short sections and limit number
            meaningful_sections = [s for s in sections if len(s) > 100]
            return meaningful_sections[:20]  # Limit to 20 clauses max
            
        except Exception as e:
            logger.error(f"Error splitting clauses: {str(e)}")
            # Fallback: split by double newlines
            return [p.strip() for p in text.split('\n\n') if len(p.strip()) > 100][:10]
    
    async def _analyze_clause(self, clause_text: str, clause_index: int) -> Dict[str, Any]:
        """
        Analyze individual clause using AI
        """
        try:
            # Identify clause type
            clause_type = self._identify_clause_type(clause_text)
            
            # Generate simplified explanation
            simplified = await self._simplify_clause(clause_text, clause_type)
            
            # Assess risk level
            risk_assessment = self._assess_clause_risk(clause_text, clause_type)
            
            return {
                'id': f'clause_{clause_index}',
                'title': clause_type.replace('_', ' ').title(),
                'content': clause_text[:500] + '...' if len(clause_text) > 500 else clause_text,
                'simplified': simplified,
                'risk_level': risk_assessment['level'],
                'risk_score': risk_assessment['score'],
                'risk_factors': risk_assessment['factors'],
                'clause_type': clause_type
            }
            
        except Exception as e:
            logger.error(f"Error analyzing clause {clause_index}: {str(e)}")
            return {
                'id': f'clause_{clause_index}',
                'title': f'Clause {clause_index + 1}',
                'content': clause_text[:200] + '...' if len(clause_text) > 200 else clause_text,
                'simplified': 'Unable to analyze this clause automatically.',
                'risk_level': 'medium',
                'risk_score': 5,
                'risk_factors': ['Analysis failed'],
                'clause_type': 'unknown'
            }
    
    def _identify_clause_type(self, text: str) -> str:
        """
        Identify the type of legal clause
        """
        text_lower = text.lower()
        
        for clause_type, patterns in self.clause_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return clause_type
        
        # Fallback classification based on common legal terms
        if any(word in text_lower for word in ['shall', 'will', 'must', 'required']):
            return 'obligation'
        elif any(word in text_lower for word in ['may', 'can', 'permitted', 'allowed']):
            return 'right'
        else:
            return 'general'
    
    async def _simplify_clause(self, clause_text: str, clause_type: str) -> str:
        """
        Generate plain English explanation of legal clause
        """
        # In production, this would use Gemini API or similar
        # For demo, we'll use rule-based simplification
        
        simplification_templates = {
            'termination': "This explains how either party can end the contract.",
            'liability': "This describes who is responsible if something goes wrong.",
            'payment': "This covers how much you pay and when payments are due.",
            'confidentiality': "This requires keeping shared information private.",
            'intellectual_property': "This defines who owns ideas and creative work.",
            'dispute_resolution': "This explains how to resolve disagreements.",
            'obligation': "This describes what you must do under the contract.",
            'right': "This explains what you're allowed to do."
        }
        
        base_explanation = simplification_templates.get(clause_type, "This is a standard contract provision.")
        
        # Add specific details based on text analysis
        text_lower = clause_text.lower()
        
        if 'termination' in text_lower:
            if 'notice' in text_lower:
                notice_match = re.search(r'(\d+)\s+days?\s+notice', text_lower)
                if notice_match:
                    days = notice_match.group(1)
                    base_explanation += f" You need to give {days} days notice."
            
            if 'cause' in text_lower and 'without' in text_lower:
                base_explanation += " Either party can terminate without giving a specific reason."
        
        elif 'payment' in text_lower:
            amount_match = re.search(r'\$[\d,]+', clause_text)
            if amount_match:
                base_explanation += f" The amount involved is {amount_match.group()}."
            
            if 'late' in text_lower and 'fee' in text_lower:
                base_explanation += " There are penalties for late payment."
        
        return base_explanation
    
    def _assess_clause_risk(self, clause_text: str, clause_type: str) -> Dict[str, Any]:
        """
        Assess risk level of a clause
        """
        text_lower = clause_text.lower()
        risk_score = 5  # Default medium risk
        risk_factors = []
        
        # Check for high-risk terms
        for term in self.high_risk_keywords:
            if term.lower() in text_lower:
                risk_score += 2
                risk_factors.append(f"Contains high-risk term: '{term}'")
        
        # Check for medium-risk terms
        for term in self.medium_risk_keywords:
            if term.lower() in text_lower:
                risk_score += 1
                risk_factors.append(f"Contains medium-risk term: '{term}'")
        
        # Clause-specific risk assessment
        if clause_type == 'termination':
            if 'immediate' in text_lower or 'without notice' in text_lower:
                risk_score += 2
                risk_factors.append("Allows immediate termination")
        
        elif clause_type == 'liability':
            if 'unlimited' in text_lower:
                risk_score += 3
                risk_factors.append("Unlimited liability exposure")
            elif 'limited' in text_lower:
                risk_score -= 1
                risk_factors.append("Liability is limited")
        
        elif clause_type == 'payment':
            if 'penalty' in text_lower or 'liquidated damages' in text_lower:
                risk_score += 2
                risk_factors.append("Contains payment penalties")
        
        # Normalize score to 1-10 range
        risk_score = max(1, min(10, risk_score))
        
        # Determine risk level
        if risk_score <= 3:
            risk_level = 'low'
        elif risk_score <= 7:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        if not risk_factors:
            risk_factors = ['Standard clause with typical terms']
        
        return {
            'score': risk_score,
            'level': risk_level,
            'factors': risk_factors
        }
    
    async def _generate_summary(self, text: str, filename: str) -> str:
        """
        Generate AI summary of the document
        """
        try:
            # In production, use Gemini API for this
            doc_type = self._detect_document_type(text)
            word_count = len(text.split())
            
            summary = f"This {doc_type} document ({filename}) contains approximately {word_count} words. "
            
            # Add clause count
            clause_count = len(self._split_into_clauses(text))
            summary += f"The document has been analyzed and contains {clause_count} major clauses or sections. "
            
            # Identify key themes
            themes = []
            text_lower = text.lower()
            
            if any(pattern in text_lower for patterns in self.clause_patterns['termination'] for pattern in patterns):
                themes.append("contract termination")
            if any(pattern in text_lower for patterns in self.clause_patterns['payment'] for pattern in patterns):
                themes.append("payment terms")
            if any(pattern in text_lower for patterns in self.clause_patterns['liability'] for pattern in patterns):
                themes.append("liability provisions")
            if any(pattern in text_lower for patterns in self.clause_patterns['confidentiality'] for pattern in patterns):
                themes.append("confidentiality requirements")
            
            if themes:
                summary += f"Key areas covered include: {', '.join(themes)}."
            
            return summary
            
        except Exception as e:
            return f"Document analysis summary for {filename}. Analysis encountered some issues: {str(e)}"
    
    def _detect_document_type(self, text: str) -> str:
        """
        Detect the type of legal document
        """
        text_lower = text.lower()
        
        if 'service agreement' in text_lower or 'services agreement' in text_lower:
            return 'Service Agreement'
        elif 'employment' in text_lower and 'agreement' in text_lower:
            return 'Employment Agreement'
        elif 'lease' in text_lower or 'rental' in text_lower:
            return 'Lease Agreement'
        elif 'non-disclosure' in text_lower or 'nda' in text_lower:
            return 'Non-Disclosure Agreement'
        elif 'license' in text_lower and 'agreement' in text_lower:
            return 'License Agreement'
        elif 'purchase' in text_lower or 'sale' in text_lower:
            return 'Purchase Agreement'
        elif 'partnership' in text_lower:
            return 'Partnership Agreement'
        elif 'contract' in text_lower:
            return 'Contract'
        else:
            return 'Legal Document'
    
    async def compare_documents(self, doc1: Dict, doc2: Dict) -> Dict[str, Any]:
        """
        Compare two documents and highlight differences
        """
        try:
            comparison = {
                'document_comparison': {
                    'doc1_clauses': len(doc1.get('clauses', [])),
                    'doc2_clauses': len(doc2.get('clauses', [])),
                    'doc1_risk': doc1.get('overall_risk', 'unknown'),
                    'doc2_risk': doc2.get('overall_risk', 'unknown')
                },
                'key_differences': [],
                'similar_clauses': [],
                'unique_to_doc1': [],
                'unique_to_doc2': [],
                'risk_comparison': self._compare_risks(doc1, doc2)
            }
            
            # Compare clause types
            doc1_types = set()
            doc2_types = set()
            
            for clause in doc1.get('clauses', []):
                doc1_types.add(clause.get('clause_type', 'unknown'))
            
            for clause in doc2.get('clauses', []):
                doc2_types.add(clause.get('clause_type', 'unknown'))
            
            comparison['unique_to_doc1'] = list(doc1_types - doc2_types)
            comparison['unique_to_doc2'] = list(doc2_types - doc1_types)
            comparison['similar_clauses'] = list(doc1_types.intersection(doc2_types))
            
            # Generate key differences
            if doc1.get('overall_risk') != doc2.get('overall_risk'):
                comparison['key_differences'].append(
                    f"Risk levels differ: Document 1 is {doc1.get('overall_risk', 'unknown')} risk, "
                    f"Document 2 is {doc2.get('overall_risk', 'unknown')} risk"
                )
            
            clause_diff = abs(len(doc1.get('clauses', [])) - len(doc2.get('clauses', [])))
            if clause_diff > 2:
                comparison['key_differences'].append(
                    f"Significant difference in complexity: {clause_diff} more clauses in one document"
                )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing documents: {str(e)}")
            return {'error': f'Comparison failed: {str(e)}'}
    
    def _compare_risks(self, doc1: Dict, doc2: Dict) -> Dict[str, Any]:
        """
        Compare risk levels between two documents
        """
        try:
            doc1_scores = [clause.get('risk_score', 5) for clause in doc1.get('clauses', [])]
            doc2_scores = [clause.get('risk_score', 5) for clause in doc2.get('clauses', [])]
            
            doc1_avg = sum(doc1_scores) / len(doc1_scores) if doc1_scores else 5
            doc2_avg = sum(doc2_scores) / len(doc2_scores) if doc2_scores else 5
            
            return {
                'doc1_average_risk': round(doc1_avg, 1),
                'doc2_average_risk': round(doc2_avg, 1),
                'risk_difference': round(abs(doc1_avg - doc2_avg), 1),
                'recommendation': (
                    "Document 1 is riskier" if doc1_avg > doc2_avg else
                    "Document 2 is riskier" if doc2_avg > doc1_avg else
                    "Both documents have similar risk levels"
                )
            }
        except Exception as e:
            return {'error': f'Risk comparison failed: {str(e)}'}
    
    async def answer_question(self, document_text: str, clauses: List[Dict], question: str) -> str:
        """
        Answer questions about document using RAG (Retrieval-Augmented Generation)
        """
        try:
            question_lower = question.lower()
            relevant_clauses = []
            
            # Find relevant clauses based on question keywords
            question_keywords = {
                'terminate': ['termination', 'end', 'cancel'],
                'pay': ['payment', 'cost', 'fee', 'price'],
                'liability': ['liable', 'responsible', 'damages'],
                'confidential': ['confidential', 'secret', 'private'],
                'breach': ['breach', 'violation', 'default'],
                'obligation': ['obligation', 'duty', 'requirement', 'must']
            }
            
            # Match question to relevant clause types
            relevant_types = []
            for keyword, synonyms in question_keywords.items():
                if any(synonym in question_lower for synonym in synonyms):
                    relevant_types.extend(synonyms)
            
            # Find matching clauses
            for clause in clauses:
                clause_text = clause.get('content', '').lower()
                clause_type = clause.get('clause_type', '')
                
                if any(rtype in clause_text or rtype in clause_type for rtype in relevant_types):
                    relevant_clauses.append(clause)
            
            # Generate answer based on relevant clauses
            if not relevant_clauses:
                return "I couldn't find specific information about your question in this document. You might want to consult with a legal professional for clarification."
            
            answer_parts = []
            for clause in relevant_clauses[:3]:  # Limit to top 3 relevant clauses
                simplified = clause.get('simplified', '')
                if simplified:
                    answer_parts.append(simplified)
            
            if answer_parts:
                answer = "Based on the document analysis: " + " ".join(answer_parts)
                
                # Add risk warning if relevant
                high_risk_clauses = [c for c in relevant_clauses if c.get('risk_level') == 'high']
                if high_risk_clauses:
                    answer += " ⚠️ Please note that some related clauses have been flagged as high-risk."
                
                return answer
            else:
                return "The document contains relevant clauses, but I need more context to provide a specific answer. Please consider consulting with a legal professional."
                
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return f"I encountered an error while analyzing your question: {str(e)}. Please try rephrasing your question."
    
    async def check_jurisdiction_compliance(self, clauses: List[Dict], jurisdiction: str) -> Dict[str, Any]:
        """
        Check document compliance with specific jurisdiction laws
        """
        try:
            compliance_issues = []
            recommendations = []
            
            jurisdiction_rules = {
                'indian': {
                    'required_clauses': ['termination', 'dispute_resolution'],
                    'restricted_terms': ['unlimited liability', 'waiver of statutory rights'],
                    'mandatory_provisions': ['governing law clause', 'jurisdiction clause']
                },
                'us': {
                    'required_clauses': ['termination', 'liability'],
                    'restricted_terms': ['penalty clauses', 'unconscionable terms'],
                    'mandatory_provisions': ['choice of law', 'dispute resolution']
                },
                'eu': {
                    'required_clauses': ['data protection', 'consumer rights'],
                    'restricted_terms': ['unfair contract terms', 'consumer right waivers'],
                    'mandatory_provisions': ['GDPR compliance', 'cooling-off period']
                }
            }
            
            rules = jurisdiction_rules.get(jurisdiction.lower(), jurisdiction_rules['indian'])
            
            # Check for required clauses
            clause_types = [clause.get('clause_type', '') for clause in clauses]
            for required in rules['required_clauses']:
                if required not in clause_types:
                    compliance_issues.append(f"Missing required {required.replace('_', ' ')} clause")
                    recommendations.append(f"Add a {required.replace('_', ' ')} clause")
            
            # Check for restricted terms
            document_text = ' '.join([clause.get('content', '') for clause in clauses]).lower()
            for restricted in rules['restricted_terms']:
                if restricted.lower() in document_text:
                    compliance_issues.append(f"Contains potentially problematic term: '{restricted}'")
                    recommendations.append(f"Review and possibly remove '{restricted}' clause")
            
            # Overall compliance score
            total_checks = len(rules['required_clauses']) + len(rules['restricted_terms'])
            issues_found = len(compliance_issues)
            compliance_score = max(0, (total_checks - issues_found) / total_checks * 100)
            
            compliance_level = (
                'High' if compliance_score >= 80 else
                'Medium' if compliance_score >= 60 else
                'Low'
            )
            
            return {
                'jurisdiction': jurisdiction,
                'compliance_level': compliance_level,
                'compliance_score': round(compliance_score, 1),
                'issues': compliance_issues,
                'recommendations': recommendations,
                'checked_provisions': list(rules.keys())
            }
            
        except Exception as e:
            logger.error(f"Error checking jurisdiction compliance: {str(e)}")
            return {
                'jurisdiction': jurisdiction,
                'compliance_level': 'Unknown',
                'compliance_score': 0,
                'issues': [f'Compliance check failed: {str(e)}'],
                'recommendations': ['Manual legal review recommended'],
                'checked_provisions': []
            }