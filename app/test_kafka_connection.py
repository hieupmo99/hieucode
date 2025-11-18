#!/usr/bin/env python3
"""Quick test to verify Kafka connectivity from Python"""
import os
from producer import send_crawled_item

# Test message
test_msg = {
    "title": "Test Article",
    "link": "https://test.com/article",
    "src": "https://test.com/image.jpg",
    "timestamp": 1234567890.0
}

print("Testing Kafka connection...")
try:
    send_crawled_item(test_msg)
    print("✓ Successfully sent test message to Kafka!")
    print(f"  Topic: {os.environ.get('KAFKA_TOPIC', 'vnexpress_topic')}")
    print(f"  Bootstrap: {os.environ.get('KAFKA_BOOTSTRAP', 'localhost:19092,localhost:29092,localhost:39092')}")
except Exception as e:
    print(f"✗ Failed to send message: {e}")
    raise
