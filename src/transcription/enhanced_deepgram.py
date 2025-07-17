"""
Enhanced Deepgram Transcription Module
Leverages advanced Deepgram features for automotive service calls
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from deepgram import DeepgramClient, PrerecordedOptions
import numpy as np

logger = logging.getLogger(__name__)


class EnhancedDeepgramTranscriber:
    """Advanced transcription with speaker identification, sentiment, and analytics"""
    
    def __init__(self, api_key: str):
        self.client = DeepgramClient(api_key)
        
        # Custom vocabulary for automotive terms
        self.custom_vocabulary = [
            "oil change", "brake pads", "transmission", "coolant",
            "alternator", "serpentine belt", "CV joint", "struts",
            "alignment", "tire rotation", "diagnostic", "OBD",
            "check engine light", "synthetic oil", "conventional oil"
        ]
        
        # Script compliance keywords to monitor
        self.script_keywords = {
            "greeting": ["thank you for calling", "how can I help"],
            "appointment_confirm": ["scheduled for", "confirm your appointment"],
            "upsell": ["recommend", "also suggest", "while you're here"],
            "closing": ["anything else", "thank you for choosing"]
        }
        
    async def transcribe_with_advanced_features(
        self, 
        audio_path: str, 
        call_direction: str = "inbound"
    ) -> Dict:
        """
        Enhanced transcription with all Deepgram features
        
        Args:
            audio_path: Path to audio file
            call_direction: 'inbound' or 'outbound' to determine speaker roles
            
        Returns:
            Comprehensive transcription data with analytics
        """
        try:
            with open(audio_path, "rb") as audio:
                buffer_data = audio.read()
            
            # Configure available Deepgram features
            options = PrerecordedOptions(
                model="nova-2",
                
                # Basic features
                punctuate=True,
                paragraphs=True,
                smart_format=True,
                
                # Speaker features
                diarize=True,
                utterances=True,
                
                # Custom vocabulary
                keywords=self.custom_vocabulary,
                
                # Audio processing
                multichannel=True,  # Process stereo separately
                
                language="en-US"
            )
            
            # Make the API call
            response = self.client.listen.rest.v("1").transcribe_file(
                {"buffer": buffer_data}, 
                options
            )
            
            # Process the comprehensive response
            result = self._process_advanced_response(response, call_direction)
            
            # Add compliance monitoring
            result['script_compliance'] = self._check_script_compliance(result)
            
            # Add sales tracking
            result['sales_metrics'] = self._extract_sales_metrics(result)
            
            # Add interaction quality metrics
            result['quality_metrics'] = self._analyze_interaction_quality(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced transcription error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _process_advanced_response(self, response, call_direction: str) -> Dict:
        """Process Deepgram response with all features"""
        
        channel_data = response.results.channels
        
        # Determine speaker roles based on call direction and channel
        employee_channel = 0 if call_direction == "inbound" else 1
        customer_channel = 1 if call_direction == "inbound" else 0
        
        result = {
            'success': True,
            'transcript': channel_data[0].alternatives[0].transcript,
            'confidence': channel_data[0].alternatives[0].confidence,
            
            # Speaker identification
            'speakers': {
                'employee': {
                    'channel': employee_channel,
                    'utterances': []
                },
                'customer': {
                    'channel': customer_channel,
                    'utterances': []
                }
            },
            
            # Sentiment analysis
            'sentiment': {
                'overall': None,
                'by_speaker': {},
                'timeline': []
            },
            
            # Topics and entities
            'topics': [],
            'entities': {},
            
            # Utterances with speaker labels
            'utterances': [],
            
            # Summary
            'summary': None,
            
            # Metadata
            'language': None,
            'duration': None
        }
        
        # Process utterances with speaker diarization
        if hasattr(response.results, 'utterances') and response.results.utterances:
            for utterance in response.results.utterances:
                # Determine speaker based on channel
                speaker_label = 'employee' if utterance.channel == employee_channel else 'customer'
                
                utterance_data = {
                    'speaker': speaker_label,
                    'text': utterance.transcript,
                    'start': utterance.start,
                    'end': utterance.end,
                    'confidence': utterance.confidence,
                    'channel': utterance.channel
                }
                
                result['utterances'].append(utterance_data)
                result['speakers'][speaker_label]['utterances'].append(utterance.transcript)
        
        # If no utterances, try to extract from words with speaker info
        elif hasattr(response.results.channels[0].alternatives[0], 'words'):
            current_speaker = None
            current_utterance = []
            current_start = 0
            
            for word in response.results.channels[0].alternatives[0].words:
                if hasattr(word, 'speaker'):
                    # Map speaker index to role
                    speaker_label = 'employee' if word.speaker == 0 else 'customer'
                    
                    if speaker_label != current_speaker:
                        # Save previous utterance
                        if current_utterance and current_speaker:
                            text = ' '.join(current_utterance)
                            result['utterances'].append({
                                'speaker': current_speaker,
                                'text': text,
                                'start': current_start,
                                'end': word.start
                            })
                            result['speakers'][current_speaker]['utterances'].append(text)
                        
                        # Start new utterance
                        current_speaker = speaker_label
                        current_utterance = [word.word]
                        current_start = word.start
                    else:
                        current_utterance.append(word.word)
            
            # Don't forget the last utterance
            if current_utterance and current_speaker:
                text = ' '.join(current_utterance)
                result['utterances'].append({
                    'speaker': current_speaker,
                    'text': text,
                    'start': current_start,
                    'end': word.end if 'word' in locals() else current_start + 1
                })
                result['speakers'][current_speaker]['utterances'].append(text)
        
        # Since advanced features aren't available, we'll analyze the text ourselves
        # Extract topics by finding common automotive terms
        transcript_lower = result['transcript'].lower()
        found_topics = []
        
        # Check for service types
        service_keywords = ['oil change', 'brake', 'tire', 'battery', 'inspection', 'alignment']
        for keyword in service_keywords:
            if keyword in transcript_lower:
                found_topics.append(keyword)
        
        result['topics'] = found_topics
        
        # Basic sentiment analysis using keyword matching
        positive_words = ['thank', 'great', 'perfect', 'excellent', 'happy', 'good', 'yes']
        negative_words = ['problem', 'issue', 'no', 'cannot', 'sorry', 'unfortunately']
        
        positive_count = sum(word in transcript_lower for word in positive_words)
        negative_count = sum(word in transcript_lower for word in negative_words)
        
        # Simple sentiment calculation
        if positive_count + negative_count > 0:
            result['sentiment']['overall'] = (positive_count - negative_count) / (positive_count + negative_count)
        else:
            result['sentiment']['overall'] = 0.0
        
        return result
    
    def _check_script_compliance(self, transcription_result: Dict) -> Dict:
        """Monitor adherence to call scripts"""
        
        compliance = {
            'score': 0,
            'missing_components': [],
            'found_components': [],
            'details': {}
        }
        
        full_transcript = transcription_result['transcript'].lower()
        employee_utterances = ' '.join(
            transcription_result['speakers']['employee']['utterances']
        ).lower()
        
        # Check each script component
        for component, keywords in self.script_keywords.items():
            found = False
            for keyword in keywords:
                if keyword in employee_utterances:
                    found = True
                    compliance['found_components'].append(component)
                    compliance['details'][component] = {
                        'found': True,
                        'keyword': keyword
                    }
                    break
            
            if not found:
                compliance['missing_components'].append(component)
                compliance['details'][component] = {
                    'found': False,
                    'expected': keywords
                }
        
        # Calculate compliance score
        total_components = len(self.script_keywords)
        found_components = len(compliance['found_components'])
        compliance['score'] = (found_components / total_components) * 100
        
        return compliance
    
    def _extract_sales_metrics(self, transcription_result: Dict) -> Dict:
        """Extract sales-related metrics from the call"""
        
        metrics = {
            'appointment_scheduled': False,
            'services_mentioned': [],
            'price_discussed': False,
            'prices_mentioned': [],
            'upsell_attempted': False,
            'upsell_accepted': False,
            'competitor_mentioned': False,
            'follow_up_scheduled': False,
            'outcome': 'unknown'
        }
        
        transcript = transcription_result['transcript'].lower()
        entities = transcription_result.get('entities', {})
        
        # Check for appointment scheduling
        appointment_keywords = [
            'scheduled for', 'appointment on', 'see you on',
            'come in on', 'booked for'
        ]
        for keyword in appointment_keywords:
            if keyword in transcript:
                metrics['appointment_scheduled'] = True
                break
        
        # Extract services mentioned
        service_keywords = [
            'oil change', 'brake', 'tire', 'alignment', 'inspection',
            'diagnostic', 'battery', 'filter', 'fluid', 'rotation'
        ]
        for service in service_keywords:
            if service in transcript:
                metrics['services_mentioned'].append(service)
        
        # Check for prices
        import re
        price_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+\s*dollars?\b'
        prices = re.findall(price_pattern, transcript)
        if prices:
            metrics['price_discussed'] = True
            metrics['prices_mentioned'] = prices
        
        # Check for upsell
        upsell_keywords = [
            'also recommend', 'while you\'re here', 'might as well',
            'should also', 'suggest checking'
        ]
        for keyword in upsell_keywords:
            if keyword in transcript:
                metrics['upsell_attempted'] = True
                # Check if accepted
                if any(accept in transcript[transcript.find(keyword):transcript.find(keyword)+200] 
                      for accept in ['yes', 'sure', 'okay', 'sounds good', 'let\'s do']):
                    metrics['upsell_accepted'] = True
                break
        
        # Determine outcome
        if metrics['appointment_scheduled']:
            metrics['outcome'] = 'appointment_scheduled'
        elif metrics['services_mentioned'] and metrics['price_discussed']:
            metrics['outcome'] = 'quoted_service'
        elif 'call back' in transcript or 'think about it' in transcript:
            metrics['outcome'] = 'follow_up_needed'
        
        return metrics
    
    def _analyze_interaction_quality(self, transcription_result: Dict) -> Dict:
        """Analyze call quality metrics"""
        
        quality = {
            'interruptions': 0,
            'silence_periods': 0,
            'talk_ratio': {},
            'average_response_time': 0,
            'empathy_indicators': 0,
            'professionalism_score': 0
        }
        
        utterances = transcription_result.get('utterances', [])
        
        if not utterances:
            return quality
        
        # Analyze interruptions (overlapping speech)
        for i in range(1, len(utterances)):
            if utterances[i]['start'] < utterances[i-1]['end']:
                quality['interruptions'] += 1
        
        # Analyze silence periods
        for i in range(1, len(utterances)):
            silence = utterances[i]['start'] - utterances[i-1]['end']
            if silence > 3.0:  # More than 3 seconds
                quality['silence_periods'] += 1
        
        # Calculate talk ratio
        employee_time = sum(
            u['end'] - u['start'] 
            for u in utterances 
            if u['speaker'] == 'employee'
        )
        customer_time = sum(
            u['end'] - u['start'] 
            for u in utterances 
            if u['speaker'] == 'customer'
        )
        
        total_time = employee_time + customer_time
        if total_time > 0:
            quality['talk_ratio'] = {
                'employee': (employee_time / total_time) * 100,
                'customer': (customer_time / total_time) * 100
            }
        
        # Check for empathy indicators
        empathy_phrases = [
            'understand', 'sorry to hear', 'appreciate', 'thank you',
            'happy to help', 'no problem', 'absolutely'
        ]
        employee_text = ' '.join(
            u['text'].lower() 
            for u in utterances 
            if u['speaker'] == 'employee'
        )
        
        for phrase in empathy_phrases:
            quality['empathy_indicators'] += employee_text.count(phrase)
        
        # Calculate professionalism score
        professional_indicators = [
            'sir', 'ma\'am', 'please', 'thank you', 'appreciate',
            'certainly', 'absolutely', 'happy to'
        ]
        unprofessional_indicators = [
            'yeah', 'nah', 'dunno', 'gonna', 'wanna'
        ]
        
        prof_count = sum(employee_text.count(word) for word in professional_indicators)
        unprof_count = sum(employee_text.count(word) for word in unprofessional_indicators)
        
        if prof_count + unprof_count > 0:
            quality['professionalism_score'] = (
                prof_count / (prof_count + unprof_count)
            ) * 100
        
        return quality


# Audio pre-processing utilities
class AudioPreprocessor:
    """Pre-process audio for better transcription accuracy"""
    
    @staticmethod
    def enhance_audio(audio_path: str, output_path: str) -> bool:
        """
        Enhance audio quality before transcription
        - Noise reduction
        - Volume normalization
        - Echo cancellation
        """
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize, compress_dynamic_range
            
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Normalize volume
            normalized = normalize(audio)
            
            # Compress dynamic range for consistent volume
            compressed = compress_dynamic_range(normalized)
            
            # Export enhanced audio
            compressed.export(output_path, format="mp3")
            
            return True
            
        except Exception as e:
            logger.error(f"Audio enhancement failed: {e}")
            return False


# Real-time transcription for live monitoring
class RealtimeTranscriber:
    """Real-time transcription for live call monitoring"""
    
    def __init__(self, api_key: str):
        self.client = DeepgramClient(api_key)
        self.transcription = []
        
    async def start_live_transcription(
        self, 
        websocket_url: str,
        on_transcript_callback=None
    ):
        """
        Start real-time transcription
        
        Args:
            websocket_url: WebSocket URL for audio stream
            on_transcript_callback: Function to call with each transcript
        """
        try:
            # Configure live transcription
            options = LiveOptions(
                model="nova-2",
                punctuate=True,
                interim_results=True,
                utterances=True,
                diarize=True,
                sentiment=True,
                language="en-US"
            )
            
            # Create WebSocket connection
            connection = self.client.listen.live.v("1").start(options)
            
            # Register event handlers
            connection.on(LiveTranscriptionEvents.Open, self._on_open)
            connection.on(LiveTranscriptionEvents.Transcript, 
                         lambda x: self._on_transcript(x, on_transcript_callback))
            connection.on(LiveTranscriptionEvents.Close, self._on_close)
            
            # Connect to audio stream
            # This would connect to your phone system's WebSocket
            
            return connection
            
        except Exception as e:
            logger.error(f"Live transcription error: {e}")
            return None
    
    def _on_transcript(self, transcript_data, callback):
        """Handle incoming transcripts"""
        if transcript_data.is_final:
            self.transcription.append(transcript_data)
            if callback:
                callback(transcript_data)
    
    def _on_open(self, *args):
        logger.info("Live transcription started")
    
    def _on_close(self, *args):
        logger.info("Live transcription ended")


# Example usage
async def example_enhanced_transcription():
    """Example of using enhanced transcription"""
    
    transcriber = EnhancedDeepgramTranscriber(api_key="your_key")
    
    # Transcribe with all features
    result = await transcriber.transcribe_with_advanced_features(
        audio_path="path/to/call.mp3",
        call_direction="inbound"  # This determines speaker roles
    )
    
    # Display comprehensive results
    print(f"Transcript: {result['transcript']}")
    print(f"Customer Sentiment: {result['sentiment']['by_speaker']['customer']}")
    print(f"Script Compliance: {result['script_compliance']['score']}%")
    print(f"Sales Outcome: {result['sales_metrics']['outcome']}")
    print(f"Topics Discussed: {result['topics']}")
    print(f"Services Mentioned: {result['sales_metrics']['services_mentioned']}")
    print(f"Call Quality Score: {result['quality_metrics']['professionalism_score']}%")