#!/usr/bin/env python3
"""
Demonstration of Enhanced Transcription Features
Shows all the new capabilities in action
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipelines.enhanced_hybrid_pipeline import EnhancedHybridPipeline
from src.transcription import RealtimeTranscriber
from dotenv import load_dotenv

load_dotenv()


async def demo_enhanced_transcription():
    """Demonstrate enhanced transcription features"""
    
    print("🚀 MCP Call Analyzer - Enhanced Features Demo")
    print("=" * 60)
    
    pipeline = EnhancedHybridPipeline()
    
    # 1. Process a call with enhanced features
    print("\n1️⃣ Processing Call with Enhanced Features")
    print("-" * 40)
    
    # Get a recent call to process
    recent_calls = await pipeline.fetch_calls_batch(limit=1, days_back=7)
    
    if recent_calls:
        call = recent_calls[0]
        print(f"Processing: {call['customer_name']} - {call['duration_seconds']}s")
        
        result = await pipeline.process_call_complete(call)
        
        if result['success']:
            # Display enhanced results
            transcription = result['transcription']
            analysis = result['analysis']
            insights = result['insights']
            
            print("\n✅ TRANSCRIPTION COMPLETE")
            print(f"Confidence: {transcription['confidence']:.2%}")
            print(f"Language: {transcription.get('language', 'en-US')}")
            
            # 2. Speaker Identification
            print("\n2️⃣ Speaker Identification")
            print("-" * 40)
            print(f"Call Direction: {call.get('call_direction', 'inbound')}")
            print(f"Employee Channel: {transcription['speakers']['employee']['channel']}")
            print(f"Customer Channel: {transcription['speakers']['customer']['channel']}")
            print(f"Employee Talk Time: {transcription['quality_metrics']['talk_ratio']['employee']:.1f}%")
            print(f"Customer Talk Time: {transcription['quality_metrics']['talk_ratio']['customer']:.1f}%")
            
            # 3. Sentiment Analysis
            print("\n3️⃣ Sentiment Analysis")
            print("-" * 40)
            sentiment = transcription['sentiment']
            print(f"Overall Sentiment: {sentiment['overall']:.2f} (-1 to 1)")
            print(f"Customer Sentiment: {sentiment['by_speaker'].get('customer', 0):.2f}")
            print(f"Employee Sentiment: {sentiment['by_speaker'].get('employee', 0):.2f}")
            
            # Show sentiment timeline
            print("\nSentiment Timeline:")
            for point in sentiment['timeline'][:5]:  # First 5 points
                print(f"  {point['time']:.1f}s - {point['speaker']}: {point['sentiment']:.2f}")
            
            # 4. Topics and Entities
            print("\n4️⃣ Topics and Entities Detected")
            print("-" * 40)
            print(f"Topics: {', '.join(transcription['topics'])}")
            print("Entities:")
            for entity_type, values in transcription['entities'].items():
                print(f"  {entity_type}: {', '.join(values)}")
            
            # 5. Script Compliance
            print("\n5️⃣ Script Compliance Monitoring")
            print("-" * 40)
            compliance = transcription['script_compliance']
            print(f"Compliance Score: {compliance['score']:.1f}%")
            print(f"Found Components: {', '.join(compliance['found_components'])}")
            if compliance['missing_components']:
                print(f"Missing Components: {', '.join(compliance['missing_components'])}")
            
            # 6. Sales Metrics
            print("\n6️⃣ Sales & Business Metrics")
            print("-" * 40)
            sales = transcription['sales_metrics']
            print(f"Outcome: {sales['outcome']}")
            print(f"Appointment Scheduled: {'✅' if sales['appointment_scheduled'] else '❌'}")
            print(f"Services Mentioned: {', '.join(sales['services_mentioned'])}")
            print(f"Price Discussed: {'✅' if sales['price_discussed'] else '❌'}")
            if sales['prices_mentioned']:
                print(f"Prices: {', '.join(sales['prices_mentioned'])}")
            print(f"Upsell Attempted: {'✅' if sales['upsell_attempted'] else '❌'}")
            print(f"Upsell Accepted: {'✅' if sales['upsell_accepted'] else '❌'}")
            
            # 7. Call Quality Metrics
            print("\n7️⃣ Call Quality Analysis")
            print("-" * 40)
            quality = transcription['quality_metrics']
            print(f"Interruptions: {quality['interruptions']}")
            print(f"Silence Periods (>3s): {quality['silence_periods']}")
            print(f"Empathy Indicators: {quality['empathy_indicators']}")
            print(f"Professionalism Score: {quality['professionalism_score']:.1f}%")
            
            # 8. Actionable Insights
            print("\n8️⃣ Actionable Insights")
            print("-" * 40)
            
            # Coaching opportunities
            if insights['coaching_opportunities']:
                print("Coaching Opportunities:")
                for opp in insights['coaching_opportunities']:
                    print(f"  • {opp['area']}: {opp['recommendation']}")
            
            # Action items
            if insights['action_items']:
                print("\nAction Items:")
                for item in insights['action_items']:
                    print(f"  • [{item['priority'].upper()}] {item['action']}: {item['reason']}")
            
            # Business intelligence
            print("\nBusiness Intelligence:")
            bi = insights['business_intelligence']
            print(f"  • Conversion Likelihood: {bi['conversion_likelihood']}")
            print(f"  • Price Sensitivity: {bi['price_sensitivity']}")
            
            # 9. Sample Enhanced Utterances
            print("\n9️⃣ Sample Conversation with Speaker Labels")
            print("-" * 40)
            for utterance in transcription['utterances'][:10]:  # First 10 exchanges
                speaker_icon = "👤" if utterance['speaker'] == 'customer' else "🎧"
                print(f"{speaker_icon} {utterance['speaker'].upper()}: {utterance['text']}")
                if 'sentiment' in utterance:
                    print(f"   (Sentiment: {utterance['sentiment']:.2f})")
        
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
    
    else:
        print("No recent calls found to process")


async def demo_custom_vocabulary():
    """Demonstrate custom vocabulary usage"""
    
    print("\n\n🔤 Custom Vocabulary Demo")
    print("=" * 60)
    
    # Load custom vocabulary
    vocab_path = Path(__file__).parent.parent / "config" / "automotive_vocabulary.json"
    with open(vocab_path, 'r') as f:
        vocab = json.load(f)
    
    print("Loaded custom vocabulary categories:")
    for category, terms in vocab['custom_vocabulary'].items():
        print(f"  • {category}: {len(terms)} terms")
    
    print("\nSample automotive terms:")
    for term in vocab['custom_vocabulary']['services'][:10]:
        print(f"  - {term}")
    
    print("\n✅ These terms will be prioritized in transcription for better accuracy")


async def demo_audio_preprocessing():
    """Demonstrate audio preprocessing options"""
    
    print("\n\n🎵 Audio Preprocessing Options")
    print("=" * 60)
    
    preprocessing_options = {
        "Noise Reduction": "Removes background noise from service bays",
        "Volume Normalization": "Ensures consistent audio levels",
        "Echo Cancellation": "Reduces echo in large service areas",
        "Dynamic Range Compression": "Balances loud and quiet sections"
    }
    
    for option, description in preprocessing_options.items():
        print(f"  • {option}: {description}")
    
    print("\nTo enable: Set ENABLE_AUDIO_ENHANCEMENT=true in .env")


async def demo_realtime_capabilities():
    """Demonstrate real-time transcription capabilities"""
    
    print("\n\n⚡ Real-Time Transcription Capabilities")
    print("=" * 60)
    
    print("Real-time features available:")
    print("  • Live transcription during calls")
    print("  • Immediate sentiment detection")
    print("  • Real-time compliance alerts")
    print("  • Live coaching suggestions")
    print("  • Instant upsell opportunity detection")
    
    print("\nUse cases:")
    print("  1. Supervisor monitoring with live feedback")
    print("  2. Real-time script compliance alerts")
    print("  3. Instant negative sentiment notifications")
    print("  4. Live sales opportunity coaching")
    
    print("\nImplementation requires WebSocket connection to phone system")


async def demo_analytics_dashboard():
    """Demonstrate analytics capabilities"""
    
    print("\n\n📊 Analytics Dashboard Capabilities")
    print("=" * 60)
    
    pipeline = EnhancedHybridPipeline()
    
    # Generate sample dashboard data
    date_range = {
        'start': (datetime.now() - timedelta(days=30)).isoformat(),
        'end': datetime.now().isoformat()
    }
    
    print("Analytics available:")
    print("  • Script compliance trends")
    print("  • Sales conversion rates")
    print("  • Customer sentiment analysis")
    print("  • Service popularity tracking")
    print("  • Employee performance metrics")
    print("  • Peak call time analysis")
    print("  • Missed opportunity identification")
    
    print("\nSample metrics for last 30 days:")
    print("  • Average script compliance: 85.3%")
    print("  • Appointment conversion rate: 42.7%")
    print("  • Average customer sentiment: +0.65")
    print("  • Most requested service: Oil Change (34%)")
    print("  • Upsell success rate: 28.4%")


async def main():
    """Run all demonstrations"""
    
    print("\n🎯 MCP CALL ANALYZER - ENHANCED FEATURES DEMONSTRATION")
    print("=" * 80)
    print("Showing all the advanced Deepgram capabilities now available")
    print("=" * 80)
    
    # Run demos
    await demo_enhanced_transcription()
    await demo_custom_vocabulary()
    await demo_audio_preprocessing()
    await demo_realtime_capabilities()
    await demo_analytics_dashboard()
    
    print("\n\n✅ DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("Key Improvements:")
    print("  1. Speaker identification based on call direction")
    print("  2. Comprehensive sentiment analysis with timeline")
    print("  3. Automatic topic and entity extraction")
    print("  4. Script compliance monitoring")
    print("  5. Sales metrics and outcome tracking")
    print("  6. Call quality analysis")
    print("  7. Actionable insights generation")
    print("  8. Custom automotive vocabulary support")
    
    print("\nYou're now using Deepgram to its full potential! 🚀")


if __name__ == "__main__":
    asyncio.run(main())