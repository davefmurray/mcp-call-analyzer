#!/usr/bin/env python3
"""
Process Real Calls with Enhanced Features
Let's see the power of the enhanced transcription system!
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipelines.enhanced_hybrid_pipeline import EnhancedHybridPipeline
from dotenv import load_dotenv

load_dotenv()


async def process_real_calls():
    """Process real calls with enhanced features"""
    
    print("🚀 PROCESSING REAL CALLS WITH ENHANCED FEATURES")
    print("=" * 80)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Initialize enhanced pipeline
    pipeline = EnhancedHybridPipeline()
    
    # Fetch recent calls
    print("\n📞 Fetching recent calls...")
    calls = await pipeline.fetch_calls_batch(limit=10, days_back=30)
    
    print(f"✅ Found {len(calls)} calls with recordings")
    
    if not calls:
        print("❌ No calls found. Exiting.")
        return
    
    # Process up to 3 calls for demo
    calls_to_process = calls[:3]
    print(f"\n🎯 Processing {len(calls_to_process)} calls with enhanced features...")
    
    results = []
    
    for i, call in enumerate(calls_to_process, 1):
        print(f"\n{'='*80}")
        print(f"📞 CALL {i}/{len(calls_to_process)}")
        print(f"{'='*80}")
        print(f"Customer: {call.get('customer_name', 'Unknown')}")
        print(f"Duration: {call.get('duration_seconds', 0)} seconds")
        print(f"Direction: {call.get('call_direction', 'inbound')}")
        print(f"Date: {call.get('date_created', 'Unknown')}")
        
        # Process with enhanced features
        result = await pipeline.process_call_complete(call)
        
        if result['success']:
            results.append(result)
            
            # Display enhanced results
            transcription = result['transcription']
            analysis = result['analysis']
            insights = result['insights']
            
            print("\n✅ PROCESSING COMPLETE")
            
            # 1. Speaker Breakdown
            print("\n👥 SPEAKER ANALYSIS")
            print("-" * 60)
            print(f"Call Direction: {call.get('call_direction', 'inbound').upper()}")
            
            if 'quality_metrics' in transcription:
                quality = transcription['quality_metrics']
                print(f"Employee Talk Time: {quality['talk_ratio'].get('employee', 0):.1f}%")
                print(f"Customer Talk Time: {quality['talk_ratio'].get('customer', 0):.1f}%")
            
            # 2. Sentiment Journey
            print("\n😊 SENTIMENT JOURNEY")
            print("-" * 60)
            if 'sentiment' in transcription:
                sentiment = transcription['sentiment']
                print(f"Overall: {sentiment.get('overall', 0):.2f} (-1 to +1)")
                
                if 'by_speaker' in sentiment:
                    print(f"Customer: {sentiment['by_speaker'].get('customer', 0):.2f}")
                    print(f"Employee: {sentiment['by_speaker'].get('employee', 0):.2f}")
                
                # Show sentiment flow
                if 'timeline' in sentiment and sentiment['timeline']:
                    print("\nSentiment Flow:")
                    for j, point in enumerate(sentiment['timeline'][:5]):
                        bar_length = int((point['sentiment'] + 1) * 10)
                        bar = "█" * bar_length
                        print(f"  {point['time']:.1f}s [{point['speaker']}]: {bar}")
            
            # 3. Topics & Entities
            print("\n🏷️ TOPICS & ENTITIES")
            print("-" * 60)
            if 'topics' in transcription:
                print(f"Topics: {', '.join(transcription['topics'][:5])}")
            
            if 'entities' in transcription:
                print("Key Entities:")
                for entity_type, values in list(transcription['entities'].items())[:3]:
                    if values:
                        print(f"  • {entity_type}: {', '.join(values[:3])}")
            
            # 4. Script Compliance
            print("\n✅ SCRIPT COMPLIANCE")
            print("-" * 60)
            if 'script_compliance' in transcription:
                compliance = transcription['script_compliance']
                print(f"Score: {compliance['score']:.0f}%")
                
                if compliance['missing_components']:
                    print(f"Missing: {', '.join(compliance['missing_components'])}")
                else:
                    print("All components present! 🌟")
            
            # 5. Sales Metrics
            print("\n💰 SALES METRICS")
            print("-" * 60)
            if 'sales_metrics' in transcription:
                sales = transcription['sales_metrics']
                print(f"Outcome: {sales['outcome'].replace('_', ' ').title()}")
                
                if sales['services_mentioned']:
                    print(f"Services: {', '.join(sales['services_mentioned'][:5])}")
                
                if sales['appointment_scheduled']:
                    print("✅ Appointment Scheduled!")
                
                if sales['upsell_attempted']:
                    status = "✅ Accepted" if sales['upsell_accepted'] else "❌ Declined"
                    print(f"Upsell: Attempted - {status}")
            
            # 6. Call Quality
            print("\n📊 CALL QUALITY")
            print("-" * 60)
            if 'quality_metrics' in transcription:
                quality = transcription['quality_metrics']
                print(f"Interruptions: {quality.get('interruptions', 0)}")
                print(f"Professionalism: {quality.get('professionalism_score', 0):.0f}%")
                print(f"Empathy Score: {quality.get('empathy_indicators', 0)}")
            
            # 7. Key Insights
            print("\n💡 KEY INSIGHTS")
            print("-" * 60)
            if insights:
                # Business intelligence
                if 'business_intelligence' in insights:
                    bi = insights['business_intelligence']
                    print(f"Conversion Likelihood: {bi.get('conversion_likelihood', 'Unknown').upper()}")
                    print(f"Price Sensitivity: {bi.get('price_sensitivity', 'Unknown').upper()}")
                
                # Coaching opportunities
                if insights.get('coaching_opportunities'):
                    print("\nCoaching Needed:")
                    for opp in insights['coaching_opportunities'][:2]:
                        print(f"  ⚠️ {opp['area']}: {opp.get('recommendation', '')}")
                
                # Action items
                if insights.get('action_items'):
                    print("\nAction Required:")
                    for item in insights['action_items'][:2]:
                        print(f"  🔴 [{item['priority'].upper()}] {item['action']}")
            
            # 8. Sample Conversation
            print("\n💬 CONVERSATION SAMPLE")
            print("-" * 60)
            if 'utterances' in transcription and transcription['utterances']:
                for utt in transcription['utterances'][:6]:  # First 6 exchanges
                    icon = "👤" if utt['speaker'] == 'customer' else "🎧"
                    text = utt['text'][:100] + "..." if len(utt['text']) > 100 else utt['text']
                    print(f"{icon} {utt['speaker'].upper()}: {text}")
            
            # 9. Summary
            if 'summary' in transcription:
                print("\n📝 AI SUMMARY")
                print("-" * 60)
                print(transcription['summary'])
        
        else:
            print(f"\n❌ Processing failed: {result.get('error', 'Unknown error')}")
            results.append(result)
    
    # Generate aggregate insights
    print(f"\n\n{'='*80}")
    print("📊 AGGREGATE INSIGHTS")
    print(f"{'='*80}")
    
    successful_results = [r for r in results if r.get('success')]
    
    if successful_results:
        # Calculate averages
        avg_sentiment = sum(
            r['transcription'].get('sentiment', {}).get('overall', 0) 
            for r in successful_results
        ) / len(successful_results)
        
        avg_compliance = sum(
            r['transcription'].get('script_compliance', {}).get('score', 0)
            for r in successful_results
        ) / len(successful_results)
        
        appointments_scheduled = sum(
            1 for r in successful_results
            if r['transcription'].get('sales_metrics', {}).get('appointment_scheduled')
        )
        
        upsells_accepted = sum(
            1 for r in successful_results
            if r['transcription'].get('sales_metrics', {}).get('upsell_accepted')
        )
        
        print(f"Calls Processed: {len(successful_results)}")
        print(f"Average Sentiment: {avg_sentiment:.2f}")
        print(f"Average Script Compliance: {avg_compliance:.0f}%")
        print(f"Appointments Scheduled: {appointments_scheduled}/{len(successful_results)}")
        print(f"Upsells Accepted: {upsells_accepted}/{len(successful_results)}")
        
        # Common topics
        all_topics = []
        for r in successful_results:
            all_topics.extend(r['transcription'].get('topics', []))
        
        if all_topics:
            from collections import Counter
            topic_counts = Counter(all_topics)
            print("\nMost Common Topics:")
            for topic, count in topic_counts.most_common(5):
                print(f"  • {topic}: {count} mentions")
        
        # Common services
        all_services = []
        for r in successful_results:
            all_services.extend(
                r['transcription'].get('sales_metrics', {}).get('services_mentioned', [])
            )
        
        if all_services:
            service_counts = Counter(all_services)
            print("\nMost Requested Services:")
            for service, count in service_counts.most_common(5):
                print(f"  • {service}: {count} times")
    
    # Save results
    output_file = f"enhanced_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n\n✅ Results saved to: {output_file}")
    print("🎉 Enhanced processing complete!")


if __name__ == "__main__":
    asyncio.run(process_real_calls())