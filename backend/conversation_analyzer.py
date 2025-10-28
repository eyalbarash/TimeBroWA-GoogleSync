#!/usr/bin/env python3
"""
Intelligent Conversation Analyzer for מייק ביקוב August 2025
Analyzes conversations, groups them by topic, and creates smart calendar events
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import re
from timebro_calendar import TimeBroCalendar

class ConversationAnalyzer:
    def __init__(self):
        self.db_path = "whatsapp_messages.db"
        self.calendar = TimeBroCalendar()
        self.mike_name = "מייק ביקוב"
        self.conversations = []
        self.topics = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "🔍" if level == "ANALYZE" else "ℹ️"
        print(f"[{timestamp}] {emoji} {message}")
        
    def get_august_messages_by_date(self, start_date="2025-08-01", end_date="2025-08-31"):
        """Get all August messages grouped by date"""
        self.log("Loading August 2025 messages from database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(datetime_str) as date,
                datetime_str,
                sender,
                content,
                message_type,
                from_mike,
                to_mike,
                timestamp
            FROM august_messages 
            WHERE DATE(datetime_str) BETWEEN ? AND ?
            ORDER BY timestamp
        """, (start_date, end_date))
        
        messages = cursor.fetchall()
        conn.close()
        
        # Group by date
        messages_by_date = defaultdict(list)
        for msg in messages:
            date, datetime_str, sender, content, msg_type, from_mike, to_mike, timestamp = msg
            messages_by_date[date].append({
                'datetime': datetime_str,
                'sender': sender,
                'content': content,
                'type': msg_type,
                'from_mike': bool(from_mike),
                'to_mike': bool(to_mike),
                'timestamp': timestamp
            })
            
        self.log(f"Loaded {len(messages)} messages across {len(messages_by_date)} days")
        return messages_by_date
        
    def analyze_conversation_context(self, messages, previous_day_messages=None):
        """Analyze conversation context and identify topics"""
        self.log("Analyzing conversation context and topics...", "ANALYZE")
        
        # Key topics and patterns to look for
        topic_patterns = {
            'technical_work': [
                'api', 'טמפלט', 'סנריו', 'פאוורלינק', 'powerlink', 'template', 'scenario',
                'בדיקה', 'test', 'bug', 'שגיאה', 'error', 'fix', 'תיקון'
            ],
            'project_management': [
                'פרוייקט', 'project', 'משימה', 'task', 'deadline', 'מועד', 'סיום',
                'התקדמות', 'progress', 'סטטוס', 'status'
            ],
            'client_communication': [
                'לקוח', 'client', 'customer', 'פגישה', 'meeting', 'שיחה', 'call',
                'הצעה', 'proposal', 'הסכם', 'agreement'
            ],
            'urgent_issues': [
                'דחוף', 'urgent', 'חשוב', 'important', 'בעיה', 'problem', 'issue',
                'מיידי', 'immediate', 'עכשיו', 'now'
            ],
            'coordination': [
                'תיאום', 'coordination', 'זמן', 'time', 'מתי', 'when', 'איפה', 'where',
                'מקום', 'location', 'להיפגש', 'meet'
            ]
        }
        
        # Analyze message content for topics
        detected_topics = set()
        context_summary = []
        
        for msg in messages:
            content_lower = msg['content'].lower()
            
            # Check for topic patterns
            for topic, patterns in topic_patterns.items():
                if any(pattern in content_lower for pattern in patterns):
                    detected_topics.add(topic)
                    
            # Extract key context phrases
            if len(msg['content']) > 20 and msg['type'] == 'text':
                context_summary.append(msg['content'][:100])
                
        # Check continuity with previous day
        is_continuation = False
        if previous_day_messages:
            # Simple heuristic: if similar topics discussed in previous day
            prev_topics = set()
            for msg in previous_day_messages[-5:]:  # Check last 5 messages of previous day
                content_lower = msg['content'].lower()
                for topic, patterns in topic_patterns.items():
                    if any(pattern in content_lower for pattern in patterns):
                        prev_topics.add(topic)
                        
            if detected_topics & prev_topics:  # If there's overlap in topics
                is_continuation = True
                
        return {
            'topics': list(detected_topics),
            'context_summary': context_summary[:3],  # Top 3 context snippets
            'is_continuation': is_continuation,
            'message_count': len(messages)
        }
        
    def identify_conversation_sessions(self, messages):
        """Identify conversation sessions based on time gaps"""
        self.log("Identifying conversation sessions...", "ANALYZE")
        
        if not messages:
            return []
            
        sessions = []
        current_session = []
        
        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda x: x['timestamp'])
        
        for i, msg in enumerate(sorted_messages):
            if not current_session:
                current_session = [msg]
            else:
                # Check time gap from last message
                last_msg_time = datetime.fromtimestamp(current_session[-1]['timestamp'])
                current_msg_time = datetime.fromtimestamp(msg['timestamp'])
                time_gap = current_msg_time - last_msg_time
                
                # If gap > 2 hours, start new session
                if time_gap > timedelta(hours=2):
                    if current_session:
                        sessions.append(current_session)
                        current_session = [msg]
                else:
                    current_session.append(msg)
                    
        # Add the last session
        if current_session:
            sessions.append(current_session)
            
        self.log(f"Identified {len(sessions)} conversation sessions")
        return sessions
        
    def create_event_from_session(self, session, date, context, session_num=1):
        """Create a calendar event from a conversation session"""
        if not session:
            return None
            
        # Calculate session start and end times
        start_time = datetime.fromtimestamp(session[0]['timestamp'])
        end_time = datetime.fromtimestamp(session[-1]['timestamp'])
        
        # Ensure minimum 15 minutes duration
        if (end_time - start_time).total_seconds() < 900:  # Less than 15 minutes
            end_time = start_time + timedelta(minutes=15)
            
        # Create event title based on topics and context
        topics_str = ", ".join(context['topics']) if context['topics'] else "General Discussion"
        
        title_parts = []
        if context['is_continuation']:
            title_parts.append("📱 מייק ביקוב - המשך שיחה")
        else:
            title_parts.append("📱 מייק ביקוב - שיחה")
            
        if len(context['topics']) == 1:
            topic_hebrew = {
                'technical_work': 'עבודה טכנית',
                'project_management': 'ניהול פרויקט', 
                'client_communication': 'תקשורת לקוחות',
                'urgent_issues': 'נושאים דחופים',
                'coordination': 'תיאום'
            }
            title_parts.append(f"- {topic_hebrew.get(context['topics'][0], topics_str)}")
        elif len(context['topics']) > 1:
            title_parts.append("- נושאים מרובים")
            
        if len(sessions := self.identify_conversation_sessions([session[0]])) > 1:
            title_parts.append(f"(שיחה {session_num})")
            
        title = " ".join(title_parts)
        
        # Create description
        description_parts = [
            f"שיחת WhatsApp עם מייק ביקוב",
            f"📅 תאריך: {date}",
            f"💬 {len(session)} הודעות",
            f"⏱️ משך: {end_time - start_time}",
            ""
        ]
        
        if context['topics']:
            description_parts.extend([
                "🎯 נושאים:",
                "\n".join([f"  • {topic}" for topic in context['topics']]),
                ""
            ])
            
        if context['context_summary']:
            description_parts.extend([
                "📝 תוכן עיקרי:",
                "\n".join([f"  • {snippet}..." for snippet in context['context_summary']]),
                ""
            ])
            
        if context['is_continuation']:
            description_parts.append("🔄 המשך שיחה מהיום הקודם")
            
        description_parts.extend([
            "",
            "🤖 נוצר אוטומטית על ידי מערכת ניתוח WhatsApp"
        ])
        
        description = "\n".join(description_parts)
        
        # Create the calendar event
        try:
            event = self.calendar.create_event(
                title=title,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                description=description,
                timezone="Asia/Jerusalem"
            )
            
            if event:
                self.log(f"Created event: {title}", "SUCCESS")
                return {
                    'event': event,
                    'title': title,
                    'start_time': start_time,
                    'end_time': end_time,
                    'topics': context['topics'],
                    'message_count': len(session)
                }
            else:
                self.log(f"Failed to create event for {date}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"Error creating event: {str(e)}", "ERROR")
            return None
            
    def analyze_and_create_events(self, start_date="2025-08-01", end_date="2025-08-03"):
        """Main function to analyze conversations and create calendar events"""
        self.log(f"Starting analysis for {start_date} to {end_date}")
        
        # Authenticate calendar
        if not self.calendar.authenticate():
            self.log("Calendar authentication failed", "ERROR")
            return []
            
        # Get messages by date
        messages_by_date = self.get_august_messages_by_date(start_date, end_date)
        
        created_events = []
        previous_day_messages = None
        
        # Process each date
        dates = sorted(messages_by_date.keys())
        
        for date in dates:
            self.log(f"\n📅 Processing {date}")
            print("-" * 50)
            
            daily_messages = messages_by_date[date]
            
            if not daily_messages:
                self.log(f"No messages found for {date}")
                continue
                
            self.log(f"Found {len(daily_messages)} messages on {date}")
            
            # Analyze conversation context
            context = self.analyze_conversation_context(daily_messages, previous_day_messages)
            
            self.log(f"Detected topics: {', '.join(context['topics']) if context['topics'] else 'None'}")
            if context['is_continuation']:
                self.log("Detected as continuation of previous day's conversation")
                
            # Identify conversation sessions
            sessions = self.identify_conversation_sessions(daily_messages)
            
            # Create events for each session
            for i, session in enumerate(sessions, 1):
                self.log(f"Creating event for session {i} ({len(session)} messages)")
                
                event_data = self.create_event_from_session(session, date, context, i)
                if event_data:
                    created_events.append(event_data)
                    
            # Store messages for next day analysis
            previous_day_messages = daily_messages
            
        return created_events
        
    def generate_summary_report(self, events):
        """Generate a summary report of created events"""
        self.log("\n" + "="*60)
        self.log("📊 CONVERSATION ANALYSIS SUMMARY")
        self.log("="*60)
        
        if not events:
            self.log("No events were created")
            return
            
        total_messages = sum(event['message_count'] for event in events)
        all_topics = set()
        for event in events:
            all_topics.update(event['topics'])
            
        self.log(f"📅 Total events created: {len(events)}")
        self.log(f"💬 Total messages analyzed: {total_messages}")
        self.log(f"🎯 Unique topics identified: {len(all_topics)}")
        
        if all_topics:
            self.log(f"📋 Topics: {', '.join(sorted(all_topics))}")
            
        self.log("\n📝 Created Events:")
        for i, event in enumerate(events, 1):
            duration = event['end_time'] - event['start_time']
            self.log(f"   {i}. {event['title']}")
            self.log(f"      ⏰ {event['start_time'].strftime('%Y-%m-%d %H:%M')} - {event['end_time'].strftime('%H:%M')}")
            self.log(f"      💬 {event['message_count']} messages, {duration}")
            if event['topics']:
                self.log(f"      🎯 {', '.join(event['topics'])}")
            print()

def main():
    """Main function for testing the conversation analyzer"""
    print("🧠 מייק ביקוב Conversation Analyzer")
    print("="*50)
    
    analyzer = ConversationAnalyzer()
    
    # Run full August 2025 analysis
    events = analyzer.analyze_and_create_events("2025-08-04", "2025-08-26")
    
    # Generate summary report
    analyzer.generate_summary_report(events)
    
    if events:
        print(f"\n🎉 SUCCESS! Created {len(events)} calendar events")
        print("📅 Check your TimeBro calendar to see the new events")
    else:
        print("\n⚠️ No events were created. Check the logs above for details.")

if __name__ == "__main__":
    main()
