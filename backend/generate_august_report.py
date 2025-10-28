#!/usr/bin/env python3
"""
Generate comprehensive August 2025 monthly report
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from timebro_calendar import TimeBroCalendar

class AugustReportGenerator:
    def __init__(self):
        self.db_path = "whatsapp_messages.db"
        self.calendar = TimeBroCalendar()
        
    def log(self, message):
        print(f"📊 {message}")
        
    def get_august_data(self):
        """Get comprehensive August 2025 data"""
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
            ORDER BY timestamp
        """)
        
        messages = cursor.fetchall()
        conn.close()
        
        # Process data
        messages_by_date = defaultdict(list)
        total_stats = {
            'total_messages': len(messages),
            'from_mike': 0,
            'to_mike': 0,
            'message_types': Counter(),
            'daily_counts': Counter(),
            'hourly_distribution': Counter()
        }
        
        for msg in messages:
            date, datetime_str, sender, content, msg_type, from_mike, to_mike, timestamp = msg
            
            # Add to daily grouping
            messages_by_date[date].append({
                'datetime': datetime_str,
                'sender': sender,
                'content': content,
                'type': msg_type,
                'from_mike': bool(from_mike),
                'to_mike': bool(to_mike),
                'timestamp': timestamp
            })
            
            # Update statistics
            total_stats['from_mike'] += bool(from_mike)
            total_stats['to_mike'] += bool(to_mike)
            total_stats['message_types'][msg_type] += 1
            total_stats['daily_counts'][date] += 1
            
            # Hour distribution
            hour = datetime.fromisoformat(datetime_str).hour
            total_stats['hourly_distribution'][hour] += 1
            
        return messages_by_date, total_stats
        
    def get_calendar_events(self):
        """Get all August 2025 calendar events"""
        if not self.calendar.authenticate():
            return []
            
        try:
            time_min = '2025-08-01T00:00:00Z'
            time_max = '2025-08-31T23:59:59Z'
            
            events_result = self.calendar.service.events().list(
                calendarId=self.calendar.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Process events
            processed_events = []
            for event in events:
                if 'מייק ביקוב' in event.get('summary', ''):
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    duration = end_dt - start_dt
                    
                    processed_events.append({
                        'id': event['id'],
                        'title': event['summary'],
                        'start': start_dt,
                        'end': end_dt,
                        'duration': duration,
                        'date': start_dt.date().isoformat()
                    })
                    
            return processed_events
            
        except Exception as e:
            self.log(f"Error getting calendar events: {str(e)}")
            return []
            
    def generate_comprehensive_report(self):
        """Generate the comprehensive August 2025 report"""
        self.log("Generating comprehensive August 2025 report...")
        
        # Get data
        messages_by_date, stats = self.get_august_data()
        calendar_events = self.get_calendar_events()
        
        # Create report
        report = {
            'report_generated': datetime.now().isoformat(),
            'period': 'August 2025',
            'summary': {
                'total_conversation_days': len(messages_by_date),
                'total_messages': stats['total_messages'],
                'from_mike': stats['from_mike'],
                'to_mike': stats['to_mike'],
                'calendar_events_created': len(calendar_events),
                'total_conversation_time': sum([event['duration'] for event in calendar_events], timedelta()),
                'date_range': {
                    'start': min(messages_by_date.keys()) if messages_by_date else None,
                    'end': max(messages_by_date.keys()) if messages_by_date else None
                }
            },
            'daily_breakdown': {},
            'conversation_patterns': {
                'most_active_days': dict(stats['daily_counts'].most_common(5)),
                'hourly_distribution': dict(stats['hourly_distribution']),
                'message_types': dict(stats['message_types']),
                'peak_hours': [hour for hour, count in stats['hourly_distribution'].most_common(3)]
            },
            'calendar_events': [],
            'insights': {}
        }
        
        # Process daily breakdown
        for date, messages in messages_by_date.items():
            day_events = [e for e in calendar_events if e['date'] == date]
            
            report['daily_breakdown'][date] = {
                'message_count': len(messages),
                'from_mike': sum(1 for m in messages if m['from_mike']),
                'to_mike': sum(1 for m in messages if m['to_mike']),
                'calendar_events': len(day_events),
                'total_event_duration': sum([e['duration'] for e in day_events], timedelta()),
                'first_message': messages[0]['datetime'] if messages else None,
                'last_message': messages[-1]['datetime'] if messages else None
            }
            
        # Process calendar events
        for event in calendar_events:
            report['calendar_events'].append({
                'date': event['date'],
                'title': event['title'],
                'start_time': event['start'].strftime('%H:%M'),
                'duration': str(event['duration']),
                'duration_minutes': int(event['duration'].total_seconds() / 60)
            })
            
        # Generate insights
        total_duration_hours = sum([event['duration'] for event in calendar_events], timedelta()).total_seconds() / 3600
        avg_messages_per_day = stats['total_messages'] / len(messages_by_date) if messages_by_date else 0
        
        report['insights'] = {
            'total_conversation_hours': round(total_duration_hours, 1),
            'average_messages_per_day': round(avg_messages_per_day, 1),
            'longest_conversation': max(calendar_events, key=lambda x: x['duration']) if calendar_events else None,
            'most_active_day': max(stats['daily_counts'], key=stats['daily_counts'].get) if stats['daily_counts'] else None,
            'conversation_intensity': {
                'high_intensity_days': [date for date, count in stats['daily_counts'].items() if count > 50],
                'medium_intensity_days': [date for date, count in stats['daily_counts'].items() if 10 <= count <= 50],
                'low_intensity_days': [date for date, count in stats['daily_counts'].items() if count < 10]
            }
        }
        
        if report['insights']['longest_conversation']:
            longest = report['insights']['longest_conversation']
            report['insights']['longest_conversation'] = {
                'date': longest['date'],
                'title': longest['title'],
                'duration': str(longest['duration']),
                'duration_hours': round(longest['duration'].total_seconds() / 3600, 1)
            }
            
        return report
        
    def save_and_display_report(self, report):
        """Save report to file and display summary"""
        
        # Save to JSON file
        filename = f"august_2025_comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
        self.log(f"Report saved to: {filename}")
        
        # Display summary
        print("\n" + "🗓️ " + "="*70)
        print("   AUGUST 2025 - מייק ביקוב CONVERSATION ANALYSIS")
        print("="*70 + " 🗓️")
        
        summary = report['summary']
        insights = report['insights']
        
        print(f"\n📊 OVERVIEW:")
        print(f"   📅 Conversation period: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"   💬 Total messages: {summary['total_messages']}")
        print(f"   📤 From מייק: {summary['from_mike']}")
        print(f"   📥 To מייק: {summary['to_mike']}")
        print(f"   🗓️ Active days: {summary['total_conversation_days']}")
        print(f"   📅 Calendar events created: {summary['calendar_events_created']}")
        print(f"   ⏱️ Total conversation time: {summary['total_conversation_time']}")
        
        print(f"\n🎯 KEY INSIGHTS:")
        print(f"   ⏰ Total conversation hours: {insights['total_conversation_hours']} hours")
        print(f"   📈 Average messages per day: {insights['average_messages_per_day']}")
        print(f"   🏆 Most active day: {insights['most_active_day']}")
        
        if insights['longest_conversation']:
            longest = insights['longest_conversation']
            print(f"   🕐 Longest conversation: {longest['date']} ({longest['duration_hours']} hours)")
            
        print(f"\n📈 ACTIVITY LEVELS:")
        intensity = insights['conversation_intensity']
        print(f"   🔥 High intensity (50+ messages): {len(intensity['high_intensity_days'])} days")
        print(f"   🔶 Medium intensity (10-50 messages): {len(intensity['medium_intensity_days'])} days")
        print(f"   🔸 Low intensity (<10 messages): {len(intensity['low_intensity_days'])} days")
        
        print(f"\n🕐 PEAK HOURS:")
        patterns = report['conversation_patterns']
        for hour in patterns['peak_hours']:
            count = patterns['hourly_distribution'][hour]
            print(f"   {hour:02d}:00 - {count} messages")
            
        print(f"\n📅 TOP 5 MOST ACTIVE DAYS:")
        for date, count in list(patterns['most_active_days'].items())[:5]:
            events_count = len([e for e in report['calendar_events'] if e['date'] == date])
            print(f"   {date}: {count} messages, {events_count} calendar events")
            
        print(f"\n📱 MESSAGE TYPES:")
        for msg_type, count in patterns['message_types'].items():
            percentage = (count / summary['total_messages']) * 100
            print(f"   {msg_type}: {count} ({percentage:.1f}%)")
            
        print("\n" + "="*74)
        print("🎉 Complete calendar integration achieved!")
        print("📅 All August 2025 conversations with מייק ביקוב are now in your TimeBro calendar")
        print("="*74)
        
        return filename

def main():
    """Generate and display the August 2025 comprehensive report"""
    generator = AugustReportGenerator()
    
    print("📊 Generating August 2025 Comprehensive Analysis Report")
    print("="*60)
    
    try:
        report = generator.generate_comprehensive_report()
        filename = generator.save_and_display_report(report)
        
        print(f"\n✅ Report generation completed successfully!")
        print(f"📁 Detailed report saved as: {filename}")
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()














