#!/usr/bin/env python3
"""
Latency Test Results Comparison Tool
Compares multiple latency test results and generates performance reports
"""

import json
import os
import statistics
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

def load_test_results(directory="../exports"):
    """Load all latency test results from exports directory"""
    results = []
    
    if not os.path.exists(directory):
        print(f"❌ Exports directory not found: {directory}")
        return results
    
    for filename in os.listdir(directory):
        if filename.startswith(("latency_test_", "advanced_latency_test_")) and filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    data['filename'] = filename
                    results.append(data)
                print(f"✅ Loaded: {filename}")
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    
    return results

def analyze_results(results):
    """Analyze and compare test results"""
    if not results:
        print("❌ No test results found")
        return
    
    print("\n" + "="*80)
    print("📊 LATENCY TEST COMPARISON REPORT")
    print("="*80)
    
    # Group by test type
    basic_tests = [r for r in results if r['filename'].startswith('latency_test_')]
    advanced_tests = [r for r in results if r['filename'].startswith('advanced_latency_test_')]
    
    print(f"\n📈 BASIC TESTS: {len(basic_tests)}")
    if basic_tests:
        for test in basic_tests:
            print(f"  {test['filename']}: {test['total_tests']} tests")
            if 'statistics' in test and 'intervals' in test['statistics']:
                stats = test['statistics']['intervals']
                print(f"    Mean interval: {stats['mean']:.2f}ms")
    
    print(f"\n📈 ADVANCED TESTS: {len(advanced_tests)}")
    if advanced_tests:
        for test in advanced_tests:
            print(f"  {test['filename']}: {test['successful_measurements']} measurements")
            if 'statistics' in test and test['statistics']:
                stats = test['statistics']
                print(f"    Mean latency: {stats['mean']:.2f}ms")
                print(f"    Min latency: {stats['min']:.2f}ms")
                print(f"    Max latency: {stats['max']:.2f}ms")
    
    # Performance trends
    if len(advanced_tests) > 1:
        print(f"\n📊 PERFORMANCE TRENDS:")
        latencies = []
        timestamps = []
        
        for test in advanced_tests:
            if 'latencies_ms' in test and test['latencies_ms']:
                latencies.extend(test['latencies_ms'])
                timestamps.append(datetime.fromisoformat(test['timestamp']))
        
        if latencies:
            print(f"  Total measurements: {len(latencies)}")
            print(f"  Overall mean: {statistics.mean(latencies):.2f}ms")
            print(f"  Overall median: {statistics.median(latencies):.2f}ms")
            print(f"  Best performance: {min(latencies):.2f}ms")
            print(f"  Worst performance: {max(latencies):.2f}ms")
            
            # Performance categories
            fast = [l for l in latencies if l < 10]
            medium = [l for l in latencies if 10 <= l < 20]
            slow = [l for l in latencies if l >= 20]
            
            print(f"\n  Performance Distribution:")
            print(f"    Fast (<10ms): {len(fast)} ({len(fast)/len(latencies)*100:.1f}%)")
            print(f"    Medium (10-20ms): {len(medium)} ({len(medium)/len(latencies)*100:.1f}%)")
            print(f"    Slow (≥20ms): {len(slow)} ({len(slow)/len(latencies)*100:.1f}%)")

def create_visualization(results, output_dir="../exports"):
    """Create visualization charts for test results"""
    advanced_tests = [r for r in results if r['filename'].startswith('advanced_latency_test_')]
    
    if not advanced_tests:
        print("❌ No advanced test results for visualization")
        return
    
    # Prepare data for plotting
    all_latencies = []
    test_names = []
    
    for test in advanced_tests:
        if 'latencies_ms' in test and test['latencies_ms']:
            all_latencies.append(test['latencies_ms'])
            test_names.append(test['filename'].replace('advanced_latency_test_', '').replace('.json', ''))
    
    if not all_latencies:
        print("❌ No latency data for visualization")
        return
    
    # Create box plot
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    plt.boxplot(all_latencies, labels=test_names)
    plt.title('Latency Distribution Comparison')
    plt.ylabel('Latency (ms)')
    plt.xticks(rotation=45)
    
    # Create histogram
    plt.subplot(2, 2, 2)
    all_data = [item for sublist in all_latencies for item in sublist]
    plt.hist(all_data, bins=20, alpha=0.7, edgecolor='black')
    plt.title('Overall Latency Distribution')
    plt.xlabel('Latency (ms)')
    plt.ylabel('Frequency')
    
    # Create performance over time
    plt.subplot(2, 2, 3)
    for i, test in enumerate(advanced_tests):
        if 'latencies_ms' in test and test['latencies_ms']:
            plt.plot(test['latencies_ms'], label=test_names[i], alpha=0.7)
    plt.title('Latency Over Time')
    plt.xlabel('Test Number')
    plt.ylabel('Latency (ms)')
    plt.legend()
    
    # Create performance summary
    plt.subplot(2, 2, 4)
    means = [statistics.mean(latencies) for latencies in all_latencies]
    medians = [statistics.median(latencies) for latencies in all_latencies]
    
    x = np.arange(len(test_names))
    width = 0.35
    
    plt.bar(x - width/2, means, width, label='Mean', alpha=0.7)
    plt.bar(x + width/2, medians, width, label='Median', alpha=0.7)
    
    plt.title('Performance Summary')
    plt.xlabel('Test')
    plt.ylabel('Latency (ms)')
    plt.xticks(x, test_names, rotation=45)
    plt.legend()
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plot_filename = os.path.join(output_dir, f"latency_comparison_{timestamp}.png")
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
    print(f"📊 Visualization saved: {plot_filename}")
    
    plt.show()

def generate_report(results, output_dir="../exports"):
    """Generate a comprehensive performance report"""
    if not results:
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = os.path.join(output_dir, f"performance_report_{timestamp}.md")
    
    with open(report_filename, 'w') as f:
        f.write("# DS4 Controller Latency Performance Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        basic_tests = [r for r in results if r['filename'].startswith('latency_test_')]
        advanced_tests = [r for r in results if r['filename'].startswith('advanced_latency_test_')]
        
        f.write(f"- Total test files: {len(results)}\n")
        f.write(f"- Basic tests: {len(basic_tests)}\n")
        f.write(f"- Advanced tests: {len(advanced_tests)}\n\n")
        
        # Advanced test details
        if advanced_tests:
            f.write("## Advanced Test Results\n\n")
            f.write("| Test | Measurements | Mean (ms) | Median (ms) | Min (ms) | Max (ms) |\n")
            f.write("|------|--------------|-----------|-------------|----------|----------|\n")
            
            for test in advanced_tests:
                if 'statistics' in test and test['statistics']:
                    stats = test['statistics']
                    f.write(f"| {test['filename']} | {test['successful_measurements']} | {stats['mean']:.2f} | {stats['median']:.2f} | {stats['min']:.2f} | {stats['max']:.2f} |\n")
        
        # Recommendations
        f.write("\n## Performance Recommendations\n\n")
        f.write("Based on the test results:\n\n")
        
        all_latencies = []
        for test in advanced_tests:
            if 'latencies_ms' in test:
                all_latencies.extend(test['latencies_ms'])
        
        if all_latencies:
            mean_latency = statistics.mean(all_latencies)
            if mean_latency < 10:
                f.write("- ✅ **Excellent performance**: Mean latency under 10ms\n")
            elif mean_latency < 20:
                f.write("- ⚠️ **Good performance**: Mean latency under 20ms\n")
            else:
                f.write("- ❌ **Poor performance**: Mean latency over 20ms\n")
            
            f.write(f"- Average latency: {mean_latency:.2f}ms\n")
            f.write(f"- Best single measurement: {min(all_latencies):.2f}ms\n")
            f.write(f"- Worst single measurement: {max(all_latencies):.2f}ms\n")
    
    print(f"📄 Performance report saved: {report_filename}")

def main():
    print("📊 Latency Test Results Comparison Tool")
    print("="*50)
    
    # Load results
    results = load_test_results()
    
    if not results:
        print("❌ No test results found. Run latency tests first.")
        return
    
    # Analyze results
    analyze_results(results)
    
    # Create visualization
    try:
        create_visualization(results)
    except ImportError:
        print("⚠️  matplotlib not available, skipping visualization")
    
    # Generate report
    generate_report(results)
    
    print(f"\n✅ Analysis complete! Found {len(results)} test result(s)")

if __name__ == "__main__":
    main() 