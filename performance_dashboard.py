#!/usr/bin/env python3
"""Simplified Mental Math Performance Dashboard - Focus on Key Metrics"""

import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import seaborn as sns
from datetime import datetime

# Set style for clean visualizations
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_history(filepath='mental_math_history.jsonl'):
    """Load history from JSONL file."""
    sessions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        session = json.loads(line)
                        sessions.append(session)
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        print(f"File '{filepath}' not found. Please check the filename.")
        return []
    
    return sessions

def process_sessions(sessions):
    """Process all sessions into structured format."""
    processed = []
    for session in sessions:
        config = session.get('config', {})
        summary = session.get('summary', {})
        
        processed.append({
            'timestamp': session.get('timestamp', 'unknown'),
            'preset': config.get('preset', 'custom'),
            'total': summary.get('total', 0),
            'correct': summary.get('correct', 0),
            'wrong': summary.get('wrong', 0),
            'skipped': summary.get('skipped', 0),
            'score_percent': summary.get('score_percent', 0),
            'mean_time': summary.get('mean_correct_time'),
            'categories': summary.get('category_stats', {})
        })
    return processed

def aggregate_category_performance(sessions):
    """Aggregate performance data across all sessions."""
    category_data = defaultdict(lambda: {
        'attempts': 0,
        'correct': 0,
        'wrong': 0,
        'skipped': 0,
        'times': []
    })
    
    for session in sessions:
        for cat, stats in session.get('categories', {}).items():
            if stats.get('attempts', 0) > 0:
                data = category_data[cat]
                data['attempts'] += stats.get('attempts', 0)
                data['correct'] += stats.get('correct', 0)
                data['skipped'] += stats.get('skipped', 0)
                
                # Calculate wrong attempts
                attempts = stats.get('attempts', 0)
                correct = stats.get('correct', 0)
                skipped = stats.get('skipped', 0)
                data['wrong'] += attempts - correct - skipped
                
                if stats.get('mean_correct_time'):
                    data['times'].append(stats['mean_correct_time'])
    
    # Calculate metrics for each category
    for cat, data in category_data.items():
        attempts = data['attempts']
        if attempts > 0:
            data['accuracy'] = (data['correct'] / attempts * 100)
            data['wrong_rate'] = (data['wrong'] / attempts * 100)
            data['skip_rate'] = (data['skipped'] / attempts * 100)
            data['avg_time'] = np.mean(data['times']) if data['times'] else None
    
    return category_data

def get_timestamp():
    """Get current timestamp for filename."""
    now = datetime.now()
    # Format: YYYYMMDD_HHMM
    return now.strftime("%Y%m%d_%H%M")

def create_dashboard(sessions):
    """Create a clean dashboard with 3 key visualizations."""
    if not sessions:
        print("No data to display")
        return
    
    # Get timestamp for filename
    timestamp = get_timestamp()
    
    # Process data
    processed = process_sessions(sessions)
    category_data = aggregate_category_performance(processed)
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Mental Math Performance Overview', fontsize=16, fontweight='bold')
    
    # 1. Category Performance Breakdown
    ax1 = axes[0]
    if category_data:
        # Sort by accuracy ascending (worst to best)
        sorted_cats = sorted(category_data.items(), key=lambda x: x[1]['accuracy'])
        
        categories = [cat[0].replace('_', ' ').title() for cat in sorted_cats]
        accuracies = [cat[1]['accuracy'] for cat in sorted_cats]
        wrong_rates = [cat[1]['wrong_rate'] for cat in sorted_cats]
        skip_rates = [cat[1]['skip_rate'] for cat in sorted_cats]
        
        y_pos = np.arange(len(categories))
        height = 0.6
        
        # Create stacked horizontal bar chart
        ax1.barh(y_pos, accuracies, height, label='Correct', color='#2ecc71', alpha=0.8)
        ax1.barh(y_pos, wrong_rates, height, label='Wrong', color='#e74c3c', alpha=0.8, left=accuracies)
        ax1.barh(y_pos, skip_rates, height, label='Skipped', color='#f39c12', alpha=0.8, 
                left=np.array(accuracies) + np.array(wrong_rates))
        
        # Add percentage labels
        for i, (cat, data) in enumerate(sorted_cats):
            accuracy = data['accuracy']
            
            # Add accuracy label at the start of the bar
            if accuracy > 15:
                ax1.text(accuracy/2, i, f'{accuracy:.0f}%', 
                        ha='center', va='center', fontsize=8, color='white', fontweight='bold')
            elif accuracy > 0:
                ax1.text(1, i, f'{accuracy:.0f}%', 
                        ha='left', va='center', fontsize=8)
            
            # Add total attempts
            attempts = data['attempts']
            ax1.text(105, i, f'n={attempts}', 
                    ha='left', va='center', fontsize=8, color='gray')
        
        ax1.set_xlabel('Percentage', fontsize=11)
        ax1.set_title('Category Performance Breakdown', fontsize=13, fontweight='bold')
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(categories, fontsize=9)
        ax1.legend(loc='lower right', fontsize=9)
        ax1.set_xlim(0, 115)
        ax1.grid(True, alpha=0.3, axis='x')
    
    # 2. Time Performance per Category
    ax2 = axes[1]
    # Filter categories with time data
    time_cats = [(cat, data['avg_time']) for cat, data in category_data.items() 
                if data['avg_time'] is not None and not np.isnan(data['avg_time'])]
    
    if time_cats:
        # Sort by time descending (slowest to fastest)
        time_cats.sort(key=lambda x: x[1], reverse=True)
        categories = [cat[0].replace('_', ' ').title() for cat in time_cats]
        times = [cat[1] for cat in time_cats]
        
        # Create color gradient based on speed
        max_time = max(times) if times else 1
        colors = plt.cm.RdYlGn_r(np.array(times) / max_time)
        
        bars = ax2.barh(categories, times, color=colors, alpha=0.8)
        
        # Add time labels
        for i, (bar, time_val) in enumerate(zip(bars, times)):
            width = bar.get_width()
            # Add speed indicator
            if time_val < 4:
                status = '⚡ Fast'
            elif time_val < 7:
                status = '✓ Avg'
            else:
                status = '🐢 Slow'
            ax2.text(width + 0.2, i, f'{time_val:.1f}s {status}', 
                    ha='left', va='center', fontsize=9)
        
        # Add overall average line
        avg_time = np.mean(times)
        ax2.axvline(x=avg_time, color='red', linestyle='--', alpha=0.7, 
                   label=f'Overall Avg: {avg_time:.1f}s')
        
        ax2.set_xlabel('Average Time (seconds)', fontsize=11)
        ax2.set_title('Time Performance by Category', fontsize=13, fontweight='bold')
        ax2.legend(loc='lower right', fontsize=9)
        ax2.grid(True, alpha=0.3, axis='x')
    
    # 3. Progress Trend
    ax3 = axes[2]
    if len(processed) > 0:
        # Sort sessions by timestamp
        sorted_sessions = sorted(processed, key=lambda x: x['timestamp'])
        
        session_num = range(1, len(sorted_sessions) + 1)
        scores = [s['score_percent'] for s in sorted_sessions]
        
        # Plot main score trend
        ax3.plot(session_num, scores, marker='o', linewidth=2.5, color='#3498db', 
                markersize=8, label='Score %')
        
        # Add trend line
        if len(scores) > 1:
            z = np.polyfit(session_num, scores, 1)
            p = np.poly1d(z)
            ax3.plot(session_num, p(session_num), "--", color='#e74c3c', 
                    linewidth=2, alpha=0.7, label='Trend')
        
        # Add session labels with dates
        dates = []
        for s in sorted_sessions:
            if s['timestamp'] != 'unknown':
                try:
                    date = datetime.fromisoformat(s['timestamp']).strftime('%m/%d')
                    dates.append(date)
                except:
                    dates.append(f"S{len(dates)+1}")
            else:
                dates.append(f"S{len(dates)+1}")
        
        ax3.set_xticks(session_num)
        ax3.set_xticklabels(dates, rotation=45, ha='right', fontsize=8)
        
        # Add score labels on points
        for i, (x, y) in enumerate(zip(session_num, scores)):
            ax3.text(x, y + 1, f'{y:.0f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # Add session count and accuracy info
        ax3.text(0.02, 0.98, f'Sessions: {len(scores)}', 
                transform=ax3.transAxes, fontsize=10, fontweight='bold')
        
        if len(scores) > 1:
            improvement = scores[-1] - scores[0]
            if improvement > 5:
                status = f'📈 +{improvement:.1f}% improvement!'
                color = '#27ae60'
            elif improvement > -5:
                status = f'➖ {improvement:+.1f}% change'
                color = '#f39c12'
            else:
                status = f'📉 {improvement:.1f}% decline'
                color = '#e74c3c'
            
            ax3.text(0.02, 0.90, status, transform=ax3.transAxes, 
                    fontsize=10, fontweight='bold', color=color)
        
        # Calculate and display moving average
        if len(scores) >= 3:
            window = min(3, len(scores))
            moving_avg = np.convolve(scores, np.ones(window)/window, mode='valid')
            ax3.plot(range(window, len(scores)+1), moving_avg, 
                    'g--', linewidth=1.5, alpha=0.6, label=f'{window}-session avg')
        
        ax3.set_xlabel('Session', fontsize=11)
        ax3.set_ylabel('Score (%)', fontsize=11)
        ax3.set_title('Progress Trend', fontsize=13, fontweight='bold')
        ax3.legend(loc='best', fontsize=9)
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(0, 100)
    
    plt.tight_layout()
    
    # Save with timestamp in filename only
    filename = f'visualisations/{timestamp}_progress_report.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"✅ Dashboard saved as '{filename}'")

def print_summary(sessions):
    """Print a concise summary of key metrics."""
    processed = process_sessions(sessions)
    category_data = aggregate_category_performance(processed)
    
    print("\n" + "="*70)
    print("📊 PERFORMANCE SUMMARY")
    print("="*70)
    
    # Overall stats
    total_questions = sum(s['total'] for s in processed)
    total_correct = sum(s['correct'] for s in processed)
    total_wrong = sum(s['wrong'] for s in processed)
    total_skipped = sum(s['skipped'] for s in processed)
    overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    print(f"\nOverall Accuracy: {overall_accuracy:.1f}%")
    print(f"  ✅ Correct: {total_correct}  ❌ Wrong: {total_wrong}  ⏭️ Skipped: {total_skipped}")
    
    # Best and worst categories
    if category_data:
        # Find best category (highest accuracy with at least 3 attempts)
        valid_cats = [(cat, data) for cat, data in category_data.items() 
                     if data['attempts'] >= 3]
        if valid_cats:
            best = max(valid_cats, key=lambda x: x[1]['accuracy'])
            worst = min(valid_cats, key=lambda x: x[1]['accuracy'])
            
            print(f"\n🏆 Best Category: {best[0].replace('_', ' ').title()} ({best[1]['accuracy']:.1f}% accuracy)")
            print(f"⚠️  Needs Work: {worst[0].replace('_', ' ').title()} ({worst[1]['accuracy']:.1f}% accuracy)")
    
    # Progress
    if len(processed) >= 2:
        first_score = processed[0]['score_percent']
        last_score = processed[-1]['score_percent']
        improvement = last_score - first_score
        
        if improvement > 0:
            print(f"\n📈 Progress: +{improvement:.1f}% improvement from first to last session")
        elif improvement < 0:
            print(f"\n📉 Progress: {improvement:.1f}% decline from first to last session")
        else:
            print(f"\n➖ Progress: No change from first to last session")
    
    # Recommendations
    if category_data:
        print("\n🎯 Quick Recommendations:")
        # Find weakest category with sufficient attempts
        weak_cats = [(cat, data) for cat, data in category_data.items() 
                    if data['attempts'] >= 3 and data['accuracy'] < 70]
        if weak_cats:
            weak_cats.sort(key=lambda x: x[1]['accuracy'])
            for cat, data in weak_cats[:2]:
                print(f"  • Focus on {cat.replace('_', ' ').title()} ({data['accuracy']:.1f}% accuracy)")
        
        # Check for time issues
        time_issues = [(cat, data) for cat, data in category_data.items() 
                      if data['avg_time'] and data['avg_time'] > 7 and data['attempts'] >= 3]
        if time_issues:
            time_issues.sort(key=lambda x: x[1]['avg_time'], reverse=True)
            print(f"  • Speed practice needed for {time_issues[0][0].replace('_', ' ').title()} ({time_issues[0][1]['avg_time']:.1f}s average)")

def main():
    """Main function to run the dashboard."""
    # Load history from JSONL file
    sessions = load_history('mental_math_history.jsonl')
    
    if not sessions:
        print("No valid sessions found in the history file.")
        print("Please ensure 'mental_math_history.jsonl' exists and contains data.")
        return
    
    print(f"📊 Analyzing {len(sessions)} sessions...")
    
    # Create the dashboard
    create_dashboard(sessions)
    
    # Print summary
    print_summary(sessions)

if __name__ == "__main__":
    main()
