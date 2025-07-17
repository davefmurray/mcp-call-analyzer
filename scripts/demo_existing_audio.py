#!/usr/bin/env python3
"""
Process Existing Audio File with Enhanced Features
Shows the full power of enhanced transcription on a real call
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.transcription import EnhancedDeepgramTranscriber
from dotenv import load_dotenv

load_dotenv()


async def process_existing_audio():
    """Process the existing audio file with enhanced features"""
    
    print("🎯 PROCESSING EXISTING AUDIO WITH ENHANCED FEATURES")
    print("=" * 80)
    
    # Audio file path
    audio_path = "downloads/CAa5cbe57a8f3acfa11b034c41856d9cb7.mp3"
    
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    print(f"✅ Found audio file: {audio_path}")
    
    # Initialize enhanced transcriber
    transcriber = EnhancedDeepgramTranscriber(
        api_key=os.getenv("DEEPGRAM_API_KEY")
    )
    
    # Mock call info
    call_info = {
        'call_id': 'CAa5cbe57a8f3acfa11b034c41856d9cb7',
        'customer_name': 'CUSTOMER',
        'duration_seconds': 180,
        'call_direction': 'inbound'  # Assume inbound
    }
    
    print(f"\n📞 Processing audio file...")
    print(f"Direction: {call_info['call_direction']}")
    print(f"Expected Duration: ~{call_info['duration_seconds']} seconds")
    
    # Process with enhanced features
    result = await transcriber.transcribe_with_advanced_features(
        audio_path=audio_path,
        call_direction=call_info['call_direction']
    )
    
    if result.get('success'):
        print("\n✅ TRANSCRIPTION SUCCESSFUL!")
        
        # 1. Basic Info
        print("\n📊 BASIC INFORMATION")
        print("-" * 60)
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Language: {result.get('language', 'en-US')}")
        
        # 2. Transcript Sample
        print("\n📝 TRANSCRIPT SAMPLE")
        print("-" * 60)
        transcript = result['transcript']
        print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
        
        # 3. Speaker Analysis
        print("\n👥 SPEAKER ANALYSIS")
        print("-" * 60)
        speakers = result['speakers']
        print(f"Employee Channel: {speakers['employee']['channel']}")
        print(f"Customer Channel: {speakers['customer']['channel']}")
        
        if result['quality_metrics']['talk_ratio']:
            print(f"Employee Talk Time: {result['quality_metrics']['talk_ratio']['employee']:.1f}%")
            print(f"Customer Talk Time: {result['quality_metrics']['talk_ratio']['customer']:.1f}%")
        
        print(f"\nEmployee Utterances: {len(speakers['employee']['utterances'])}")
        print(f"Customer Utterances: {len(speakers['customer']['utterances'])}")
        
        # 4. Sentiment Analysis
        print("\n😊 SENTIMENT ANALYSIS")
        print("-" * 60)
        sentiment = result['sentiment']
        print(f"Overall Sentiment: {sentiment['overall']:.2f} (-1 to +1)")
        
        if sentiment['by_speaker']:
            print(f"Customer Sentiment: {sentiment['by_speaker'].get('customer', 0):.2f}")
            print(f"Employee Sentiment: {sentiment['by_speaker'].get('employee', 0):.2f}")
        
        # Show sentiment journey
        if sentiment['timeline']:
            print("\nSentiment Journey:")
            for i, point in enumerate(sentiment['timeline'][:10]):
                bar_length = int((point['sentiment'] + 1) * 10)
                bar = "█" * bar_length
                print(f"  {point['time']:6.1f}s [{point['speaker']:8}]: {bar}")
        
        # 5. Topics and Entities
        print("\n🏷️ TOPICS & ENTITIES")
        print("-" * 60)
        if result['topics']:
            print(f"Topics: {', '.join(result['topics'])}")
        else:
            print("Topics: None detected")
        
        if result['entities']:
            print("\nEntities:")
            for entity_type, values in result['entities'].items():
                if values:
                    print(f"  • {entity_type}: {', '.join(values[:5])}")
        
        # 6. Script Compliance
        print("\n✅ SCRIPT COMPLIANCE")
        print("-" * 60)
        compliance = result['script_compliance']
        print(f"Compliance Score: {compliance['score']:.0f}%")
        
        print("\nComponents:")
        for component in compliance['found_components']:
            print(f"  ✅ {component}")
        for component in compliance['missing_components']:
            print(f"  ❌ {component}")
        
        # 7. Sales Metrics
        print("\n💰 SALES METRICS")
        print("-" * 60)
        sales = result['sales_metrics']
        print(f"Outcome: {sales['outcome'].replace('_', ' ').title()}")
        print(f"Appointment Scheduled: {'✅' if sales['appointment_scheduled'] else '❌'}")
        
        if sales['services_mentioned']:
            print(f"Services Mentioned: {', '.join(sales['services_mentioned'])}")
        
        if sales['prices_mentioned']:
            print(f"Prices Discussed: {', '.join(sales['prices_mentioned'])}")
        
        print(f"Upsell Attempted: {'✅' if sales['upsell_attempted'] else '❌'}")
        if sales['upsell_attempted']:
            print(f"Upsell Accepted: {'✅' if sales['upsell_accepted'] else '❌'}")
        
        # 8. Call Quality
        print("\n📊 CALL QUALITY METRICS")
        print("-" * 60)
        quality = result['quality_metrics']
        print(f"Interruptions: {quality['interruptions']}")
        print(f"Silence Periods: {quality['silence_periods']}")
        print(f"Empathy Indicators: {quality['empathy_indicators']}")
        print(f"Professionalism Score: {quality['professionalism_score']:.0f}%")
        
        # 9. Conversation Sample
        print("\n💬 CONVERSATION SAMPLE")
        print("-" * 60)
        if result['utterances']:
            for i, utt in enumerate(result['utterances'][:10]):
                icon = "👤" if utt['speaker'] == 'customer' else "🎧"
                text = utt['text'][:80] + "..." if len(utt['text']) > 80 else utt['text']
                print(f"{icon} {utt['speaker'].upper()}: {text}")
                if 'sentiment' in utt:
                    print(f"   [Sentiment: {utt['sentiment']:.2f}]")
        
        # 10. Summary
        if result.get('summary'):
            print("\n📝 AI SUMMARY")
            print("-" * 60)
            print(result['summary'])
        
        # Save full results
        output_file = f"enhanced_audio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n✅ Full results saved to: {output_file}")
        
    else:
        print(f"\n❌ Transcription failed: {result.get('error', 'Unknown error')}")
    
    print("\n🎉 Demo complete!")


if __name__ == "__main__":
    asyncio.run(process_existing_audio())