"""PC Building Agent Service - Conversational AI agent for helping users build PCs."""

import logging
from typing import Dict, Any, List, Optional
from app.models import Part, Build
from app.database import db
from app.services.compatibility_service import check_build_compatibility, calculate_build_price
from app.ml_model.recommender import MLRecommender

logger = logging.getLogger(__name__)


class PCBuildingAgent:
    """Conversational agent that helps users build PCs."""
    
    def __init__(self):
        """Initialize the agent."""
        self.recommender = MLRecommender()
    
    def process_message(self, 
                        message: str,
                        user_id: int,
                        conversation_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user message and generate a response.
        
        Args:
            message: User's message.
            user_id: ID of the user.
            conversation_context: Current conversation context.
        
        Returns:
            Dictionary with agent response and any recommendations.
        """
        if conversation_context is None:
            conversation_context = self._initialize_context()
        
        # Normalize message
        message_lower = message.lower().strip()
        
        # Intent recognition
        intent = self._recognize_intent(message_lower, conversation_context)
        
        # Update context based on intent
        self._update_context(conversation_context, intent, message)
        
        # Generate response based on intent
        response = self._generate_response(intent, conversation_context, user_id)
        
        return {
            'message': response['text'],
            'recommended_parts': response.get('recommended_parts', []),
            'build_suggestion': response.get('build_suggestion'),
            'updated_context': conversation_context
        }
    
    def _initialize_context(self) -> Dict[str, Any]:
        """Initialize a new conversation context.
        
        Returns:
            Empty context dictionary.
        """
        return {
            'budget': None,
            'use_case': None,
            'selected_parts': [],
            'part_types_needed': [],
            'conversation_stage': 'greeting',
            'build_name': None
        }
    
    def _recognize_intent(self, message: str, context: Dict[str, Any]) -> str:
        """Recognize user intent from message.
        
        Args:
            message: Normalized user message.
            context: Current conversation context.
        
        Returns:
            Intent string.
        """
        # Budget mentions
        if any(word in message for word in ['budget', 'price', 'cost', '$', 'dollar', 'spend']):
            return 'set_budget'
        
        # Use case mentions
        if any(word in message for word in ['gaming', 'game', 'stream', 'work', 'office', 'productivity', 'video', 'edit']):
            return 'set_use_case'
        
        # Part type requests
        part_types = ['cpu', 'gpu', 'ram', 'motherboard', 'storage', 'psu', 'case', 'cooler']
        for part_type in part_types:
            if part_type in message:
                return 'request_part'
        
        # Recommendation requests
        if any(word in message for word in ['recommend', 'suggest', 'suggestion', 'what', 'which', 'help']):
            return 'request_recommendation'
        
        # Build completion
        if any(word in message for word in ['done', 'complete', 'finish', 'save', 'ready']):
            return 'complete_build'
        
        # Compatibility check
        if any(word in message for word in ['compatible', 'compatibility', 'check', 'work together']):
            return 'check_compatibility'
        
        # Default: general inquiry
        return 'general'
    
    def _update_context(self, context: Dict[str, Any], intent: str, message: str) -> None:
        """Update conversation context based on intent.
        
        Args:
            context: Current context to update.
            intent: Recognized intent.
            message: User's message.
        """
        if intent == 'set_budget':
            # Extract budget amount
            import re
            amounts = re.findall(r'\$?(\d+)', message)
            if amounts:
                try:
                    budget = float(amounts[0])
                    context['budget'] = budget
                    context['conversation_stage'] = 'collecting_requirements'
                except ValueError:
                    pass
        
        elif intent == 'set_use_case':
            if 'gaming' in message or 'game' in message:
                context['use_case'] = 'gaming'
            elif 'work' in message or 'office' in message or 'productivity' in message:
                context['use_case'] = 'work'
            elif 'stream' in message:
                context['use_case'] = 'streaming'
            elif 'edit' in message or 'video' in message:
                context['use_case'] = 'content_creation'
            context['conversation_stage'] = 'collecting_requirements'
        
        elif intent == 'request_part':
            # Extract part type
            part_types = {
                'cpu': 'CPU', 'processor': 'CPU',
                'gpu': 'GPU', 'graphics': 'GPU', 'video card': 'GPU',
                'ram': 'RAM', 'memory': 'RAM',
                'motherboard': 'Motherboard', 'mobo': 'Motherboard',
                'storage': 'Storage', 'ssd': 'Storage', 'hard drive': 'Storage',
                'psu': 'PSU', 'power supply': 'PSU',
                'case': 'Case', 'chassis': 'Case',
                'cooler': 'Cooler', 'cooling': 'Cooler'
            }
            for key, part_type in part_types.items():
                if key in message:
                    if part_type not in context['part_types_needed']:
                        context['part_types_needed'].append(part_type)
                    break
        
        elif intent == 'complete_build':
            context['conversation_stage'] = 'completing'
    
    def _generate_response(self, 
                          intent: str,
                          context: Dict[str, Any],
                          user_id: int) -> Dict[str, Any]:
        """Generate agent response based on intent and context.
        
        Args:
            intent: Recognized intent.
            context: Conversation context.
            user_id: User ID.
        
        Returns:
            Response dictionary with text and optional recommendations.
        """
        response = {'text': '', 'recommended_parts': [], 'build_suggestion': None}
        
        if intent == 'set_budget':
            if context.get('budget'):
                response['text'] = f"Great! I'll help you build a PC within a ${context['budget']:.0f} budget. "
                response['text'] += "What will you primarily use this PC for? (gaming, work, streaming, etc.)"
            else:
                response['text'] = "I'd be happy to help! What's your budget for this build?"
        
        elif intent == 'set_use_case':
            use_case = context.get('use_case', 'general')
            budget = context.get('budget')
            if budget:
                response['text'] = f"Perfect! For {use_case}, I can recommend parts that will give you great performance. "
                response['text'] += "Let me suggest some components. What part would you like to start with? (CPU, GPU, RAM, etc.)"
            else:
                response['text'] = f"Got it! For {use_case}, I can help you build the perfect PC. What's your budget?"
        
        elif intent == 'request_part' or intent == 'request_recommendation':
            budget = context.get('budget')
            if not budget:
                response['text'] = "I'd love to recommend parts! First, what's your budget for this build?"
                return response
            
            # Get part type from context or message
            part_type = None
            if context.get('part_types_needed'):
                part_type = context['part_types_needed'][-1]
            
            # Get recommendations
            recommendations = self._get_recommendations(
                user_id=user_id,
                budget=budget,
                part_type=part_type,
                existing_parts=context.get('selected_parts', [])
            )
            
            if recommendations:
                response['recommended_parts'] = [r['part'] for r in recommendations[:5]]
                part_names = [r['part']['name'] for r in recommendations[:3]]
                response['text'] = f"Here are some great options:\n"
                for i, rec in enumerate(recommendations[:3], 1):
                    response['text'] += f"{i}. {rec['part']['name']} - ${rec['part'].get('price', 0):.2f}\n"
                    response['text'] += f"   {rec.get('reason', 'Good value')}\n"
                response['text'] += "\nWould you like to add any of these to your build?"
            else:
                response['text'] = "I couldn't find parts matching your criteria. Could you adjust your budget or preferences?"
        
        elif intent == 'check_compatibility':
            selected_parts = context.get('selected_parts', [])
            if not selected_parts:
                response['text'] = "You haven't selected any parts yet. Would you like me to recommend some?"
            elif len(selected_parts) < 2:
                response['text'] = "You need at least 2 parts to check compatibility. Let me recommend more parts!"
            else:
                try:
                    compat_result = check_build_compatibility(selected_parts)
                    if compat_result['is_compatible']:
                        response['text'] = "✓ Great news! Your selected parts are compatible with each other."
                    else:
                        response['text'] = "⚠ I found some compatibility issues:\n"
                        for issue in compat_result.get('issues', []):
                            response['text'] += f"- {issue}\n"
                        response['text'] += "\nWould you like me to suggest compatible alternatives?"
                except Exception as e:
                    logger.error(f"Error checking compatibility: {e}")
                    response['text'] = "I had trouble checking compatibility. Let me try again."
        
        elif intent == 'complete_build':
            selected_parts = context.get('selected_parts', [])
            if not selected_parts:
                response['text'] = "You haven't selected any parts yet. Let me help you choose some parts first!"
            else:
                try:
                    total_price = calculate_build_price(selected_parts)
                    compat_result = check_build_compatibility(selected_parts)
                    
                    build_suggestion = {
                        'name': context.get('build_name', 'My PC Build'),
                        'parts': selected_parts,
                        'total_price': total_price,
                        'is_compatible': compat_result['is_compatible'],
                        'compatibility_issues': compat_result.get('issues', [])
                    }
                    
                    response['build_suggestion'] = build_suggestion
                    response['text'] = f"Perfect! Here's your build summary:\n"
                    response['text'] += f"Total Price: ${total_price:.2f}\n"
                    response['text'] += f"Compatibility: {'✓ Compatible' if compat_result['is_compatible'] else '⚠ Issues Found'}\n"
                    response['text'] += "\nWould you like to save this build?"
                except Exception as e:
                    logger.error(f"Error completing build: {e}")
                    response['text'] = "I had trouble finalizing your build. Let me try again."
        
        elif intent == 'general' or context.get('conversation_stage') == 'greeting':
            response['text'] = "Hello! I'm your PC building assistant. I can help you:\n"
            response['text'] += "- Find parts within your budget\n"
            response['text'] += "- Check compatibility between parts\n"
            response['text'] += "- Build a complete PC step by step\n\n"
            response['text'] += "What's your budget for this build?"
            context['conversation_stage'] = 'collecting_requirements'
        
        else:
            response['text'] = "I'm here to help you build your PC! What would you like to know?"
        
        return response
    
    def _get_recommendations(self,
                            user_id: int,
                            budget: float,
                            part_type: Optional[str] = None,
                            existing_parts: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Get part recommendations.
        
        Args:
            user_id: User ID.
            budget: Budget constraint.
            part_type: Optional part type filter.
            existing_parts: Already selected part IDs.
        
        Returns:
            List of recommended parts with scores.
        """
        try:
            user_preferences = {
                'part_type': part_type,
                'budget': budget,
                'min_performance': 5,
                'budget_ratio': 0.3
            }
            
            recommendations = self.recommender.recommend_parts(
                user_preferences=user_preferences,
                budget=budget,
                existing_parts=existing_parts,
                num_recommendations=10,
                user_id=user_id
            )
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

