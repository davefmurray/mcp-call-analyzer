#!/usr/bin/env python3
"""
Demo Enhanced Features with Sample Data
Shows what the enhanced transcription output looks like
"""

import json
from datetime import datetime

# Sample enhanced transcription output
sample_enhanced_output = {
    "success": True,
    "transcript": "Thank you for calling JJ Auto Service this is Mike how can I help you today. Hi Mike this is Jane Smith I need to schedule an oil change for my 2018 Honda Accord. Sure I can help you with that when was the last time you had it serviced. I think it was about four months ago maybe five thousand miles ago. Perfect timing then we recommend oil changes every five thousand miles or six months do you know what type of oil your Accord uses. I believe it's synthetic but I'm not completely sure. No problem we can check that when you come in we have Thursday at 2 PM available would that work for you. Yes that works great. Excellent and while you're here we can also do a complimentary multi-point inspection to check your brakes tires and fluids would you like us to include that. Sure that sounds good. Great I have you scheduled for Thursday at 2 PM for an oil change and inspection the synthetic oil change is typically around 65 dollars. That's fine. Perfect we'll send you a reminder text the day before is there anything else I can help you with today. No that's everything thank you. You're welcome Jane thank you for choosing JJ Auto Service and we'll see you Thursday have a great day. You too bye.",
    "confidence": 0.97,
    "language": "en-US",
    
    "speakers": {
        "employee": {
            "channel": 0,
            "utterances": [
                "Thank you for calling JJ Auto Service this is Mike how can I help you today.",
                "Sure I can help you with that when was the last time you had it serviced.",
                "Perfect timing then we recommend oil changes every five thousand miles or six months do you know what type of oil your Accord uses.",
                "No problem we can check that when you come in we have Thursday at 2 PM available would that work for you.",
                "Excellent and while you're here we can also do a complimentary multi-point inspection to check your brakes tires and fluids would you like us to include that.",
                "Great I have you scheduled for Thursday at 2 PM for an oil change and inspection the synthetic oil change is typically around 65 dollars.",
                "Perfect we'll send you a reminder text the day before is there anything else I can help you with today.",
                "You're welcome Jane thank you for choosing JJ Auto Service and we'll see you Thursday have a great day."
            ]
        },
        "customer": {
            "channel": 1,
            "utterances": [
                "Hi Mike this is Jane Smith I need to schedule an oil change for my 2018 Honda Accord.",
                "I think it was about four months ago maybe five thousand miles ago.",
                "I believe it's synthetic but I'm not completely sure.",
                "Yes that works great.",
                "Sure that sounds good.",
                "That's fine.",
                "No that's everything thank you.",
                "You too bye."
            ]
        }
    },
    
    "sentiment": {
        "overall": 0.82,
        "by_speaker": {
            "customer": 0.75,
            "employee": 0.89
        },
        "timeline": [
            {"time": 0.0, "sentiment": 0.9, "speaker": "employee"},
            {"time": 5.2, "sentiment": 0.6, "speaker": "customer"},
            {"time": 12.4, "sentiment": 0.85, "speaker": "employee"},
            {"time": 18.7, "sentiment": 0.7, "speaker": "customer"},
            {"time": 25.3, "sentiment": 0.9, "speaker": "employee"},
            {"time": 32.1, "sentiment": 0.8, "speaker": "customer"},
            {"time": 38.9, "sentiment": 0.95, "speaker": "employee"},
            {"time": 45.6, "sentiment": 0.85, "speaker": "customer"}
        ]
    },
    
    "topics": [
        "oil change",
        "appointment scheduling", 
        "vehicle maintenance",
        "multi-point inspection",
        "pricing"
    ],
    
    "entities": {
        "person": ["Mike", "Jane Smith"],
        "organization": ["JJ Auto Service"],
        "vehicle": ["2018 Honda Accord"],
        "service": ["oil change", "multi-point inspection"],
        "time": ["Thursday at 2 PM", "four months ago"],
        "price": ["65 dollars"],
        "quantity": ["five thousand miles"]
    },
    
    "utterances": [
        {
            "speaker": "employee",
            "text": "Thank you for calling JJ Auto Service this is Mike how can I help you today.",
            "start": 0.0,
            "end": 5.1,
            "confidence": 0.98,
            "sentiment": 0.9
        },
        {
            "speaker": "customer", 
            "text": "Hi Mike this is Jane Smith I need to schedule an oil change for my 2018 Honda Accord.",
            "start": 5.2,
            "end": 12.3,
            "confidence": 0.96,
            "sentiment": 0.6
        }
    ],
    
    "summary": "Jane Smith called to schedule an oil change for her 2018 Honda Accord. Mike scheduled her for Thursday at 2 PM and offered a complimentary multi-point inspection which she accepted. The price of $65 for synthetic oil was confirmed.",
    
    "script_compliance": {
        "score": 100.0,
        "missing_components": [],
        "found_components": ["greeting", "qualification", "recommendation", "appointment_booking", "closing"],
        "details": {
            "greeting": {
                "found": True,
                "keyword": "thank you for calling"
            },
            "qualification": {
                "found": True,
                "keyword": "how can I help"
            },
            "recommendation": {
                "found": True, 
                "keyword": "recommend"
            },
            "appointment_booking": {
                "found": True,
                "keyword": "scheduled"
            },
            "closing": {
                "found": True,
                "keyword": "anything else"
            }
        }
    },
    
    "sales_metrics": {
        "appointment_scheduled": True,
        "services_mentioned": ["oil change", "multi-point inspection", "brake", "tire", "fluid"],
        "price_discussed": True,
        "prices_mentioned": ["$65", "65 dollars"],
        "upsell_attempted": True,
        "upsell_accepted": True,
        "competitor_mentioned": False,
        "follow_up_scheduled": False,
        "outcome": "appointment_scheduled"
    },
    
    "quality_metrics": {
        "interruptions": 0,
        "silence_periods": 0,
        "talk_ratio": {
            "employee": 62.3,
            "customer": 37.7
        },
        "average_response_time": 1.2,
        "empathy_indicators": 5,
        "professionalism_score": 95.0
    }
}

# Sample insights generated
sample_insights = {
    "key_findings": [
        "Perfect script compliance - all components present",
        "Successful upsell of multi-point inspection",
        "Positive customer sentiment throughout",
        "Professional handling with high empathy score"
    ],
    
    "action_items": [],
    
    "coaching_opportunities": [],
    
    "business_intelligence": {
        "services_discussed": ["oil change", "multi-point inspection"],
        "price_sensitivity": "low",
        "conversion_likelihood": "high",
        "customer_topics": ["oil change", "appointment scheduling", "vehicle maintenance"]
    }
}

def display_enhanced_demo():
    """Display enhanced transcription features with sample data"""
    
    print("\n🎯 ENHANCED TRANSCRIPTION OUTPUT DEMONSTRATION")
    print("=" * 80)
    print("This shows what your calls will look like with all enhanced features enabled")
    print("=" * 80)
    
    # 1. Basic Transcript vs Enhanced
    print("\n📝 TRANSCRIPT COMPARISON")
    print("-" * 60)
    print("BEFORE (Basic):")
    print("Thank you for calling JJ Auto this is Mike hi Jane I need an oil change...")
    print("\nAFTER (Enhanced with Speaker Labels):")
    for i, utt in enumerate(sample_enhanced_output['utterances'][:4]):
        icon = "👤" if utt['speaker'] == 'customer' else "🎧"
        print(f"\n{icon} {utt['speaker'].upper()}: {utt['text']}")
        print(f"   [Confidence: {utt['confidence']:.0%}, Sentiment: {utt['sentiment']:.2f}]")
    
    # 2. Sentiment Analysis
    print("\n\n😊 SENTIMENT ANALYSIS")
    print("-" * 60)
    sentiment = sample_enhanced_output['sentiment']
    print(f"Overall Call Sentiment: {sentiment['overall']:.2f} (Scale: -1 to +1)")
    print(f"Customer Sentiment: {sentiment['by_speaker']['customer']:.2f}")
    print(f"Employee Sentiment: {sentiment['by_speaker']['employee']:.2f}")
    
    print("\nSentiment Flow Over Time:")
    print("Time  | Speaker  | Sentiment | Visualization")
    print("------|----------|-----------|" + "-" * 20)
    for point in sentiment['timeline']:
        bar_length = int((point['sentiment'] + 1) * 10)  # Scale to 0-20
        bar = "█" * bar_length
        print(f"{point['time']:5.1f}s | {point['speaker']:8} | {point['sentiment']:9.2f} | {bar}")
    
    # 3. Topics and Entities
    print("\n\n🏷️ TOPICS & ENTITIES DETECTED")
    print("-" * 60)
    print(f"Topics: {', '.join(sample_enhanced_output['topics'])}")
    print("\nEntities Found:")
    for entity_type, values in sample_enhanced_output['entities'].items():
        print(f"  • {entity_type.title()}: {', '.join(values)}")
    
    # 4. Script Compliance
    print("\n\n✅ SCRIPT COMPLIANCE")
    print("-" * 60)
    compliance = sample_enhanced_output['script_compliance']
    print(f"Compliance Score: {compliance['score']:.0f}%")
    print("\nScript Components:")
    for component, details in compliance['details'].items():
        status = "✅" if details['found'] else "❌"
        print(f"  {status} {component.title()}: {'Found - ' + details.get('keyword', '') if details['found'] else 'Missing'}")
    
    # 5. Sales Metrics
    print("\n\n💰 SALES & BUSINESS METRICS")
    print("-" * 60)
    sales = sample_enhanced_output['sales_metrics']
    print(f"Outcome: {sales['outcome'].replace('_', ' ').title()}")
    print(f"Appointment Scheduled: {'✅ Yes' if sales['appointment_scheduled'] else '❌ No'}")
    print(f"Services Mentioned: {', '.join(sales['services_mentioned'])}")
    print(f"Price Discussed: {'✅ Yes - ' + ', '.join(sales['prices_mentioned']) if sales['price_discussed'] else '❌ No'}")
    print(f"Upsell Attempted: {'✅ Yes' if sales['upsell_attempted'] else '❌ No'}")
    print(f"Upsell Accepted: {'✅ Yes' if sales['upsell_accepted'] else '❌ No'}")
    
    # 6. Call Quality
    print("\n\n📊 CALL QUALITY METRICS")
    print("-" * 60)
    quality = sample_enhanced_output['quality_metrics']
    print(f"Talk Time Ratio - Employee: {quality['talk_ratio']['employee']:.1f}%, Customer: {quality['talk_ratio']['customer']:.1f}%")
    print(f"Interruptions: {quality['interruptions']}")
    print(f"Silence Periods: {quality['silence_periods']}")
    print(f"Empathy Indicators: {quality['empathy_indicators']}")
    print(f"Professionalism Score: {quality['professionalism_score']:.0f}%")
    
    # 7. AI Summary
    print("\n\n🤖 AI-GENERATED SUMMARY")
    print("-" * 60)
    print(sample_enhanced_output['summary'])
    
    # 8. Actionable Insights
    print("\n\n💡 ACTIONABLE INSIGHTS")
    print("-" * 60)
    print("Key Findings:")
    for finding in sample_insights['key_findings']:
        print(f"  ✓ {finding}")
    
    print("\nBusiness Intelligence:")
    bi = sample_insights['business_intelligence']
    print(f"  • Conversion Likelihood: {bi['conversion_likelihood'].upper()}")
    print(f"  • Price Sensitivity: {bi['price_sensitivity'].upper()}")
    print(f"  • Topics of Interest: {', '.join(bi['customer_topics'])}")
    
    # 9. Visual Dashboard Preview
    print("\n\n📈 ANALYTICS DASHBOARD PREVIEW")
    print("-" * 60)
    print("Daily Metrics (Sample):")
    print("┌─────────────────────┬──────────┐")
    print("│ Metric              │ Value    │")
    print("├─────────────────────┼──────────┤")
    print("│ Script Compliance   │ 100.0%   │")
    print("│ Customer Sentiment  │ +0.75    │")
    print("│ Upsell Success Rate │ 100.0%   │")
    print("│ Prof. Score         │ 95.0%    │")
    print("│ Appointment Booked  │ ✅ Yes   │")
    print("└─────────────────────┴──────────┘")
    
    print("\n\n🎉 ENHANCED FEATURES SUMMARY")
    print("=" * 80)
    print("With these enhanced features, you now get:")
    print("  1. Clear speaker identification (Employee vs Customer)")
    print("  2. Real-time sentiment tracking with timeline")
    print("  3. Automatic topic and entity extraction")
    print("  4. Script compliance monitoring (100% in this example)")
    print("  5. Comprehensive sales metrics and outcome tracking")
    print("  6. Call quality analysis with actionable metrics")
    print("  7. AI-generated summaries for quick review")
    print("  8. Business intelligence insights")
    print("\nAll powered by Deepgram's advanced features that we weren't using before! 🚀")


if __name__ == "__main__":
    display_enhanced_demo()