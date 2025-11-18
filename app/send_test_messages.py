#!/usr/bin/env python3
"""Send multiple test messages to Kafka to trigger Spark processing"""
import time
from producer import send_crawled_item

print("Sending 10 test messages to Kafka...")
for i in range(10):
    test_msg = {
        "title": f"Test Article {i+1}",
        "link": f"https://test.com/article-{i+1}",
        "src": f"https://test.com/image-{i+1}.jpg",
        "timestamp": time.time()
    }
    send_crawled_item(test_msg)
    print(f"  ✓ Sent message {i+1}/10")
    time.sleep(0.1)

print("\n✓ All messages sent! Check Spark logs to see consumption.")
