# Interactive Demo - MCP Call Analyzer

This interactive demo will walk you through using the MCP Call Analyzer with real examples.

## 🎯 Demo Overview

We'll process a sample automotive service call through the complete pipeline:
1. Fetch call metadata
2. Download audio recording
3. Transcribe with Deepgram
4. Analyze with GPT-4
5. View insights

## 📞 Sample Call Scenario

**Customer**: Jane Smith  
**Duration**: 3 minutes 42 seconds  
**Type**: Inbound service inquiry  
**Outcome**: Scheduled oil change appointment

## 🚀 Let's Start!

### Step 1: Initialize Pipeline

```python
from src.pipelines.final_hybrid_pipeline import FinalHybridPipeline
import asyncio
import json

# Create pipeline instance
pipeline = FinalHybridPipeline()

# Authenticate
print("🔐 Authenticating...")
token = await pipeline.authenticate()
print(f"✅ Authenticated successfully!")
```

### Step 2: Fetch Recent Calls

```python
# Fetch calls from last 7 days
print("\n📞 Fetching recent calls...")
calls = await pipeline.fetch_calls_batch(limit=10, days_back=7)

# Display summary
print(f"\n📊 Found {len(calls)} calls:")
for i, call in enumerate(calls[:5]):
    print(f"{i+1}. {call['customer_name']} - {call['duration_seconds']}s - {call['date_created']}")
```

**Expected Output:**
```
📊 Found 10 calls:
1. JANE SMITH - 222s - 2024-01-15T10:30:00
2. JOHN DOE - 185s - 2024-01-15T09:15:00
3. MARY JOHNSON - 340s - 2024-01-14T14:22:00
4. ROBERT BROWN - 95s - 2024-01-14T11:45:00
5. LISA DAVIS - 415s - 2024-01-13T16:30:00
```

### Step 3: Process a Single Call

Let's process Jane Smith's call:

```python
# Select Jane's call
jane_call = calls[0]

print(f"\n🎯 Processing call: {jane_call['call_id']}")
print(f"   Customer: {jane_call['customer_name']}")
print(f"   Duration: {jane_call['duration_seconds']} seconds")

# Process through pipeline
result = await pipeline.process_call_complete(jane_call)
```

### Step 4: Monitor Progress

The pipeline will show real-time progress:

```
🎯 Processing call: CAa4dc3d3112ae5ef2bb7a4ffb23b2dbb3
   Customer: JANE SMITH
   Duration: 222 seconds

📥 Downloading audio...
   ✅ Audio downloaded: downloads/CAa4dc3d3112ae5ef2bb7a4ffb23b2dbb3.mp3

🎙️ Transcribing with Deepgram...
   ✅ Transcription complete (1,247 characters)

🤖 Analyzing with GPT-4...
   ✅ Analysis complete

💾 Storing results...
   ✅ Results saved to database

✅ Successfully processed call!
```

### Step 5: View Transcription

```python
# Get transcription from database
from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Fetch transcription
trans_result = supabase.table('transcriptions').select("*").eq('call_id', jane_call['call_id']).single().execute()
transcript = trans_result.data['transcript']

print("\n📝 TRANSCRIPTION:")
print("-" * 60)
print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
```

**Sample Transcription:**
```
📝 TRANSCRIPTION:
------------------------------------------------------------
Agent: Good morning, JJ Auto Service, this is Mike speaking. How can I help you today?

Customer: Hi Mike, this is Jane Smith. I'm calling about getting an oil change for my 2018 Honda Accord.

Agent: Hi Jane! I'd be happy to help you with that. When was the last time you had your oil changed?

Customer: I think it was about 4 months ago, maybe 5,000 miles ago.

Agent: Perfect timing then. We recommend oil changes every 5,000 miles or 6 months. Do you know what type of oil your Accord uses?

Customer: I believe it's synthetic, but I'm not completely sure...
```

### Step 6: View AI Analysis

```python
# Fetch analysis
analysis_result = supabase.table('call_analysis').select("*").eq('call_id', jane_call['call_id']).single().execute()
analysis = analysis_result.data['analysis_data']

print("\n🤖 AI ANALYSIS:")
print("-" * 60)
print(json.dumps(analysis, indent=2))
```

**Sample Analysis:**
```json
{
  "summary": "Jane Smith called to schedule an oil change for her 2018 Honda Accord. The service advisor Mike provided excellent customer service, confirming the vehicle details and scheduling an appointment for Thursday at 2 PM.",
  
  "customer_intent": "Schedule routine oil change service",
  
  "outcome": "Successfully scheduled oil change appointment for Thursday at 2:00 PM",
  
  "sentiment": "positive",
  
  "category": "appointment_scheduling",
  
  "follow_up_needed": "Yes - Send appointment reminder on Wednesday",
  
  "key_metrics": {
    "vehicle": "2018 Honda Accord",
    "service": "Oil change (synthetic)",
    "appointment": "Thursday 2:00 PM",
    "estimated_cost": "$65"
  },
  
  "missed_opportunity": "Agent could have mentioned the multi-point inspection included with oil change and current tire rotation special",
  
  "agent_performance": {
    "greeting": "Professional and friendly",
    "knowledge": "Good - knew oil change intervals",
    "closing": "Confirmed appointment details clearly"
  },
  
  "action_items": [
    "Send appointment confirmation email",
    "Add to Thursday's schedule",
    "Prepare synthetic oil for Honda Accord",
    "Note customer preference for afternoon appointments"
  ]
}
```

### Step 7: Generate Insights Dashboard

```python
# Get analytics for multiple calls
print("\n📊 CALL ANALYTICS SUMMARY:")
print("-" * 60)

# Fetch recent analyzed calls
analyzed_calls = supabase.table('v_call_details').select("*").eq('status', 'analyzed').limit(20).execute()

# Calculate metrics
sentiments = {"positive": 0, "neutral": 0, "negative": 0}
categories = {}
total_duration = 0

for call in analyzed_calls.data:
    # Sentiment
    sentiment = call.get('sentiment', 'neutral')
    sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
    
    # Category
    category = call.get('category', 'other')
    categories[category] = categories.get(category, 0) + 1
    
    # Duration
    total_duration += call.get('duration_seconds', 0)

# Display results
print(f"\n📈 Sentiment Distribution:")
for sent, count in sentiments.items():
    percentage = (count / len(analyzed_calls.data)) * 100
    print(f"   {sent.capitalize()}: {count} ({percentage:.1f}%)")

print(f"\n📂 Category Breakdown:")
for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    print(f"   {cat}: {count}")

print(f"\n⏱️ Average Call Duration: {total_duration / len(analyzed_calls.data):.1f} seconds")
```

**Expected Output:**
```
📊 CALL ANALYTICS SUMMARY:
------------------------------------------------------------

📈 Sentiment Distribution:
   Positive: 14 (70.0%)
   Neutral: 5 (25.0%)
   Negative: 1 (5.0%)

📂 Category Breakdown:
   appointment_scheduling: 8
   service_inquiry: 6
   status_check: 3
   parts_inquiry: 2
   complaint: 1

⏱️ Average Call Duration: 187.3 seconds
```

### Step 8: Identify Opportunities

```python
# Find missed opportunities
print("\n💡 MISSED OPPORTUNITIES:")
print("-" * 60)

opportunities = supabase.table('call_analysis').select(
    "call_id, analysis_data->missed_opportunity"
).not_.is_('analysis_data->missed_opportunity', 'null').limit(5).execute()

for opp in opportunities.data:
    if opp['missed_opportunity'] and opp['missed_opportunity'] != 'None':
        print(f"\n📞 Call {opp['call_id'][:8]}...")
        print(f"   💡 {opp['missed_opportunity']}")
```

### Step 9: Export Results

```python
# Export to CSV for reporting
import csv
from datetime import datetime

filename = f"call_analysis_report_{datetime.now().strftime('%Y%m%d')}.csv"

with open(filename, 'w', newline='') as csvfile:
    fieldnames = ['call_id', 'customer_name', 'date', 'duration', 'sentiment', 'category', 'follow_up_needed']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for call in analyzed_calls.data:
        writer.writerow({
            'call_id': call['call_id'],
            'customer_name': call['customer_name'],
            'date': call['date_created'],
            'duration': call['duration_seconds'],
            'sentiment': call['sentiment'],
            'category': call['category'],
            'follow_up_needed': call['follow_up_needed']
        })

print(f"\n📄 Report exported to: {filename}")
```

## 🎮 Interactive Commands

Try these interactive commands to explore the system:

### 1. Search Calls by Customer
```python
# Search for specific customer
customer_name = input("Enter customer name to search: ")
results = supabase.table('calls').select("*").ilike('customer_name', f'%{customer_name}%').execute()

print(f"\nFound {len(results.data)} calls for '{customer_name}'")
```

### 2. Filter by Sentiment
```python
# Get all negative sentiment calls
negative_calls = supabase.table('v_call_details').select("*").eq('sentiment', 'negative').execute()

print(f"\n⚠️ Found {len(negative_calls.data)} negative sentiment calls requiring attention")
```

### 3. Process New Batch
```python
# Process next batch of pending calls
pending = supabase.table('calls').select("*").eq('status', 'pending_download').limit(5).execute()

if pending.data:
    print(f"\n🔄 Processing {len(pending.data)} pending calls...")
    for call in pending.data:
        result = await pipeline.process_call_complete(call)
        print(f"   {'✅' if result['success'] else '❌'} {call['customer_name']}")
```

## 🎯 Demo Scenarios

### Scenario 1: High-Value Customer Analysis
```python
# Identify high-value customers (multiple calls)
frequent_customers = supabase.rpc('get_frequent_customers', {'min_calls': 3}).execute()
```

### Scenario 2: Service Advisor Performance
```python
# Analyze calls by extension/advisor
advisor_stats = supabase.table('calls').select("extension, count").group_by('extension').execute()
```

### Scenario 3: Peak Hours Analysis
```python
# Find busiest call times
hourly_calls = supabase.rpc('get_hourly_call_volume').execute()
```

## 🎉 Congratulations!

You've successfully:
- ✅ Processed calls through the complete pipeline
- ✅ Viewed transcriptions and AI analysis
- ✅ Generated analytics insights
- ✅ Identified business opportunities
- ✅ Exported results for reporting

## 📚 Next Steps

1. **Customize Analysis**: Modify the GPT-4 prompts for your specific needs
2. **Add Filters**: Create custom queries for your use cases
3. **Build Dashboard**: Create a web interface to visualize results
4. **Set Up Alerts**: Configure notifications for negative sentiment calls
5. **Integrate CRM**: Connect with your existing customer systems

---

Happy analyzing! 🚀