import logging
from typing import Dict, List, Any, Tuple
import re
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskAnalyzer:
    """
    Analyze and assess risk levels of legal document clauses
    """
    
    def __init__(self):
        """Initialize the risk analyzer"""
        
        # High-risk terms and patterns
        self.high_risk_terms = {
            'liability': [
                'unlimited liability', 'personal liability', 'joint and several liability',
                'full liability', 'complete liability', 'absolute liability'
            ],
            'termination': [
                'immediate termination', 'terminate without cause', 'terminate at will',
                'no notice termination', 'summary termination', 'terminate for convenience'
            ],
            'payment': [
                'no refund', 'non-refundable', 'liquidated damages', 'penalty clause',
                'forfeiture', 'compound interest', 'usurious interest'
            ],
            'obligations': [
                'personal guarantee', 'unlimited guarantee', 'unconditional guarantee',
                'irrevocable commitment', 'binding obligation'
            ],
            'dispute': [
                'waive jury trial', 'binding arbitration', 'no appeal',
                'attorney fees to prevailing party', 'forum selection'
            ],
            'modification': [
                'unilateral modification', 'sole discretion', 'without consent',
                'may change at any time', 'reserves the right'
            ]
        }
        
        # Medium-risk terms
        self.medium_risk_terms = {
            'liability': [
                'limited liability', 'liability cap', 'consequential damages excluded'
            ],
            'termination': [
                'terminate with cause', '30 days notice', 'material breach'
            ],
            'payment': [
                'late fees', 'interest charges', 'partial refund'
            ],
            'obligations': [
                'best efforts', 'commercially reasonable efforts', 'due diligence'
            ]
        }
        
        # Low-risk (protective) terms
        self.low_risk_terms = {
            'liability': [
                'mutual liability limitation', 'liability excluded', 'no liability'
            ],
            'termination': [
                'terminate for convenience with notice', 'mutual termination', 'cure period'
            ],
            'payment': [
                'pro-rated refund', 'reasonable fees', 'market rate'
            ]
        }
        
        # Risk scoring weights
        self.risk_weights = {
            'high_risk_term': 3,
            'medium_risk_term': 2,
            'low_risk_term': -1,
            'unclear_language': 2,
            'one_sided_clause': 2,
            'broad_scope': 1,
            'time_pressure': 1
        }
        
        # Clause type base risk scores
        self.base_risk_scores = {
            'termination': 6,
            'liability': 7,
            'payment': 5,
            'confidentiality': 3,
            'intellectual_property': 4,
            'dispute_resolution': 5,
            'obligations': 5,
            'warranties': 4,
            'indemnification': 7,
            'force_majeure': 2,
            'general': 4
        }

    def assess_risk(self, clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess overall risk level of the document
        
        Args:
            clauses: List of analyzed clauses
            
        Returns:
            Comprehensive risk assessment
        """
        try:
            if not clauses:
                return self._get_empty_risk_assessment()
            
            individual_risks = []
            risk_factors = []
            clause_risk_breakdown = {}
            
            # Analyze each clause
            for clause in clauses:
                clause_risk = self._analyze_clause_risk(clause)
                individual_risks.append(clause_risk['score'])
                risk_factors.extend(clause_risk['factors'])
                
                clause_type = clause.get('clause_type', 'general')
                if clause_type not in clause_risk_breakdown:
                    clause_risk_breakdown[clause_type] = []
                clause_risk_breakdown[clause_type].append(clause_risk['score'])
            
            # Calculate overall metrics
            avg_risk_score = sum(individual_risks) / len(individual_risks)
            max_risk_score = max(individual_risks)
            high_risk_count = sum(1 for score in individual_risks if score >= 7)
            
            # Determine overall risk level
            overall_risk = self._determine_overall_risk(avg_risk_score, max_risk_score, high_risk_count)
            
            # Generate risk summary
            risk_summary = self._generate_risk_summary(
                avg_risk_score, high_risk_count, len(clauses), clause_risk_breakdown
            )
            
            # Identify top risk areas
            top_risks = self._identify_top_risks(clause_risk_breakdown, clauses)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                overall_risk, risk_factors, clause_risk_breakdown
            )
            
            return {
                'overall_risk': overall_risk,
                'risk_score': round(avg_risk_score, 1),
                'max_risk_score': max_risk_score,
                'high_risk_clauses': high_risk_count,
                'total_clauses': len(clauses),
                'risk_summary': risk_summary,
                'top_risk_areas': top_risks,
                'risk_factors': list(set(risk_factors)),
                'clause_breakdown': clause_risk_breakdown,
                'recommendations': recommendations,
                'risk_distribution': self._calculate_risk_distribution(individual_risks)
            }
            
        except Exception as e:
            logger.error(f"Error assessing risk: {str(e)}")
            return self._get_empty_risk_assessment()

    def _analyze_clause_risk(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze risk for individual clause
        """
        try:
            clause_text = clause.get('content', '').lower()
            clause_type = clause.get('clause_type', 'general')
            
            # Start with base risk score for clause type
            risk_score = self.base_risk_scores.get(clause_type, 4)
            risk_factors = []
            
            # Check for high-risk terms
            for category, terms in self.high_risk_terms.items():
                for term in terms:
                    if term.lower() in clause_text:
                        risk_score += self.risk_weights['high_risk_term']
                        risk_factors.append(f"High-risk term: '{term}'")
            
            # Check for medium-risk terms
            for category, terms in self.medium_risk_terms.items():
                for term in terms:
                    if term.lower() in clause_text:
                        risk_score += self.risk_weights['medium_risk_term']
                        risk_factors.append(f"Medium-risk term: '{term}'")
            
            # Check for low-risk (protective) terms
            for category, terms in self.low_risk_terms.items():
                for term in terms:
                    if term.lower() in clause_text:
                        risk_score += self.risk_weights['low_risk_term']
                        risk_factors.append(f"Protective term: '{term}'")
            
            # Additional risk factors
            risk_score, additional_factors = self._check_additional_risk_factors(
                clause_text, risk_score
            )
            risk_factors.extend(additional_factors)
            
            # Normalize score to 1-10 range
            risk_score = max(1, min(10, risk_score))
            
            return {
                'score': risk_score,
                'level': self._score_to_level(risk_score),
                'factors': risk_factors
            }
            
        except Exception as e:
            logger.error(f"Error analyzing clause risk: {str(e)}")
            return {'score': 5, 'level': 'medium', 'factors': ['Analysis error']}

    def _check_additional_risk_factors(self, clause_text: str, current_score: int) -> Tuple[int, List[str]]:
        """
        Check for additional risk indicators
        """
        additional_factors = []
        score_adjustment = 0
        
        # Check for unclear/ambiguous language
        ambiguous_terms = ['reasonable', 'appropriate', 'satisfactory', 'adequate', 'fair']
        ambiguous_count = sum(1 for term in ambiguous_terms if term in clause_text)
        if ambiguous_count >= 2:
            score_adjustment += self.risk_weights['unclear_language']
            additional_factors.append("Contains ambiguous language")
        
        # Check for one-sided clauses
        one_sided_indicators = [
            'sole discretion', 'absolute right', 'unilateral', 'without limitation',
            'at our option', 'we may', 'company reserves'
        ]
        for indicator in one_sided_indicators:
            if indicator in clause_text:
                score_adjustment += self.risk_weights['one_sided_clause']
                additional_factors.append("One-sided clause favoring other party")
                break
        
        # Check for broad scope
        broad_scope_terms = ['all', 'any', 'every', 'entire', 'complete', 'total']
        broad_count = sum(1 for term in broad_scope_terms if f' {term} ' in clause_text)
        if broad_count >= 3:
            score_adjustment += self.risk_weights['broad_scope']
            additional_factors.append("Unusually broad scope")
        
        # Check for time pressure elements
        time_pressure_terms = ['immediately', 'forthwith', 'without delay', 'urgently']
        for term in time_pressure_terms:
            if term in clause_text:
                score_adjustment += self.risk_weights['time_pressure']
                additional_factors.append("Contains time pressure elements")
                break
        
        return current_score + score_adjustment, additional_factors

    def _determine_overall_risk(self, avg_score: float, max_score: int, high_risk_count: int) -> str:
        """
        Determine overall document risk level
        """
        if avg_score >= 7 or max_score >= 9 or high_risk_count >= 3:
            return 'high'
        elif avg_score >= 5 or max_score >= 7 or high_risk_count >= 1:
            return 'medium'
        else:
            return 'low'

    def _score_to_level(self, score: int) -> str:
        """Convert numeric score to risk level"""
        if score >= 7:
            return 'high'
        elif score >= 4:
            return 'medium'
        else:
            return 'low'

    def _generate_risk_summary(self, avg_score: float, high_risk_count: int, 
                             total_clauses: int, clause_breakdown: Dict) -> str:
        """
        Generate human-readable risk summary
        """
        try:
            summary_parts = []
            
            # Overall assessment
            if avg_score >= 7:
                summary_parts.append("This document presents HIGH risk")
            elif avg_score >= 5:
                summary_parts.append("This document presents MEDIUM risk")
            else:
                summary_parts.append("This document presents LOW risk")
            
            # Risk distribution
            if high_risk_count > 0:
                percentage = (high_risk_count / total_clauses) * 100
                summary_parts.append(f"{high_risk_count} out of {total_clauses} clauses ({percentage:.1f}%) are high-risk")
            
            # Most problematic areas
            highest_risk_types = []
            for clause_type, scores in clause_breakdown.items():
                if scores and max(scores) >= 7:
                    highest_risk_types.append(clause_type.replace('_', ' '))
            
            if highest_risk_types:
                summary_parts.append(f"Highest risk areas: {', '.join(highest_risk_types)}")
            
            return '. '.join(summary_parts) + '.'
            
        except Exception as e:
            return f"Risk summary generation failed: {str(e)}"

    def _identify_top_risks(self, clause_breakdown: Dict, clauses: List[Dict]) -> List[Dict]:
        """
        Identify top risk areas in the document
        """
        try:
            risk_areas = []
            
            for clause_type, scores in clause_breakdown.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    max_score = max(scores)
                    
                    if avg_score >= 6 or max_score >= 8:
                        # Find the specific clause with highest risk
                        highest_clause = None
                        for clause in clauses:
                            if clause.get('clause_type') == clause_type:
                                if clause.get('risk_score', 0) == max_score:
                                    highest_clause = clause
                                    break
                        
                        risk_areas.append({
                            'area': clause_type.replace('_', ' ').title(),
                            'avg_risk_score': round(avg_score, 1),
                            'max_risk_score': max_score,
                            'clause_count': len(scores),
                            'description': self._get_risk_area_description(clause_type),
                            'sample_clause': highest_clause.get('simplified', '') if highest_clause else ''
                        })
            
            # Sort by average risk score
            risk_areas.sort(key=lambda x: x['avg_risk_score'], reverse=True)
            return risk_areas[:5]  # Return top 5 risk areas
            
        except Exception as e:
            logger.error(f"Error identifying top risks: {str(e)}")
            return []

    def _get_risk_area_description(self, clause_type: str) -> str:
        """
        Get description of what makes this clause type risky
        """
        descriptions = {
            'liability': "Defines your financial responsibility if something goes wrong",
            'termination': "Controls how and when the contract can be ended",
            'payment': "Governs payment obligations and potential penalties",
            'indemnification': "Requires you to protect the other party from certain losses",
            'dispute_resolution': "Determines how conflicts will be resolved",
            'obligations': "Specifies what you must do under the contract",
            'warranties': "Contains promises about performance or quality",
            'intellectual_property': "Governs ownership of ideas and creative work",
            'confidentiality': "Controls sharing of sensitive information",
            'force_majeure': "Addresses what happens during extraordinary circumstances"
        }
        return descriptions.get(clause_type, "Important contractual provision")

    def _generate_recommendations(self, overall_risk: str, risk_factors: List[str], 
                                clause_breakdown: Dict) -> List[str]:
        """
        Generate actionable recommendations based on risk assessment
        """
        recommendations = []
        
        try:
            # Overall recommendations based on risk level
            if overall_risk == 'high':
                recommendations.append("🚨 CRITICAL: This contract has significant risks. Strongly consider legal review before signing.")
                recommendations.append("Negotiate key terms to reduce your exposure, especially in liability and termination clauses.")
            elif overall_risk == 'medium':
                recommendations.append("⚠️ CAUTION: This contract has moderate risks. Review carefully and consider legal consultation.")
                recommendations.append("Focus on understanding and potentially negotiating the higher-risk clauses.")
            else:
                recommendations.append("✅ This contract appears to have manageable risk levels.")
            
            # Specific recommendations based on risk factors
            unique_factors = set(risk_factors)
            
            if any('unlimited liability' in factor.lower() for factor in unique_factors):
                recommendations.append("Consider negotiating a liability cap to limit your financial exposure.")
            
            if any('immediate termination' in factor.lower() for factor in unique_factors):
                recommendations.append("Request a cure period or notice requirement for termination clauses.")
            
            if any('one-sided' in factor.lower() for factor in unique_factors):
                recommendations.append("Push for more balanced terms that don't heavily favor the other party.")
            
            if any('ambiguous' in factor.lower() for factor in unique_factors):
                recommendations.append("Request clarification on vague or ambiguous language.")
            
            # Clause-specific recommendations
            for clause_type, scores in clause_breakdown.items():
                if scores and max(scores) >= 8:
                    if clause_type == 'payment':
                        recommendations.append("Review payment terms carefully - consider negotiating penalties and fees.")
                    elif clause_type == 'liability':
                        recommendations.append("The liability clause is high-risk - consider insurance or indemnification.")
                    elif clause_type == 'termination':
                        recommendations.append("Termination terms are unfavorable - negotiate for more balanced conditions.")
            
            # General recommendations
            if len(recommendations) == 1:  # Only the overall risk recommendation
                recommendations.append("Ensure you understand all terms before signing.")
                recommendations.append("Keep copies of all documents and correspondence.")
            
            return recommendations[:10]  # Limit to 10 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Unable to generate specific recommendations. Consider professional legal review."]

    def _calculate_risk_distribution(self, risk_scores: List[int]) -> Dict[str, Any]:
        """
        Calculate distribution of risk scores
        """
        try:
            if not risk_scores:
                return {'low': 0, 'medium': 0, 'high': 0}
            
            low_count = sum(1 for score in risk_scores if score < 4)
            medium_count = sum(1 for score in risk_scores if 4 <= score < 7)
            high_count = sum(1 for score in risk_scores if score >= 7)
            
            total = len(risk_scores)
            
            return {
                'low': round((low_count / total) * 100, 1),
                'medium': round((medium_count / total) * 100, 1),
                'high': round((high_count / total) * 100, 1),
                'counts': {
                    'low': low_count,
                    'medium': medium_count,
                    'high': high_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk distribution: {str(e)}")
            return {'low': 0, 'medium': 100, 'high': 0}

    def _get_empty_risk_assessment(self) -> Dict[str, Any]:
        """
        Return empty risk assessment structure
        """
        return {
            'overall_risk': 'unknown',
            'risk_score': 0,
            'max_risk_score': 0,
            'high_risk_clauses': 0,
            'total_clauses': 0,
            'risk_summary': 'No clauses available for risk analysis',
            'top_risk_areas': [],
            'risk_factors': [],
            'clause_breakdown': {},
            'recommendations': ['Document analysis required'],
            'risk_distribution': {'low': 0, 'medium': 0, 'high': 0}
        }

    def generate_risk_report(self, risk_assessment: Dict[str, Any], document_name: str) -> str:
        """
        Generate a formatted risk report
        """
        try:
            report_lines = [
                f"RISK ASSESSMENT REPORT",
                f"Document: {document_name}",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"",
                f"OVERALL RISK LEVEL: {risk_assessment['overall_risk'].upper()}",
                f"Risk Score: {risk_assessment['risk_score']}/10",
                f"",
                f"SUMMARY:",
                f"{risk_assessment['risk_summary']}",
                f"",
                f"RISK DISTRIBUTION:",
                f"• Low Risk: {risk_assessment['risk_distribution']['low']}%",
                f"• Medium Risk: {risk_assessment['risk_distribution']['medium']}%",
                f"• High Risk: {risk_assessment['risk_distribution']['high']}%",
                f""
            ]
            
            if risk_assessment['top_risk_areas']:
                report_lines.append("TOP RISK AREAS:")
                for area in risk_assessment['top_risk_areas'][:3]:
                    report_lines.append(f"• {area['area']}: {area['avg_risk_score']}/10")
                report_lines.append("")
            
            if risk_assessment['recommendations']:
                report_lines.append("RECOMMENDATIONS:")
                for rec in risk_assessment['recommendations'][:5]:
                    report_lines.append(f"• {rec}")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            return f"Error generating risk report: {str(e)}"