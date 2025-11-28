#!/usr/bin/env python3
"""Script to test API endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login
print("=" * 60)
print("1. Testing LOGIN")
print("=" * 60)
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "juan@example.com",
    "password": "password123"
})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    token = data["token"]
    print(f"✅ Login successful!")
    print(f"Token: {token[:50]}...")
    print(f"User: {data['user']}")
else:
    print(f"❌ Login failed: {response.text}")
    exit(1)

headers = {"X-Access-Token": token}

# 2. Get Posts
print("\n" + "=" * 60)
print("2. Testing GET /posts - Feed de posts")
print("=" * 60)
response = requests.get(f"{BASE_URL}/posts", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    posts = response.json()
    print(f"✅ Retrieved {len(posts.get('items', []))} posts")
    if posts.get('items'):
        print(f"\nFirst post:")
        post = posts['items'][0]
        print(f"  ID: {post.get('id')}")
        print(f"  Text: {post.get('text', '')[:100]}...")
        print(f"  Author: {post.get('author', {}).get('username')}")
        print(f"  Channel: {post.get('channel', {}).get('name')}")
else:
    print(f"❌ Failed: {response.text}")

# 3. Get Channels
print("\n" + "=" * 60)
print("3. Testing GET /channels - Listar canales")
print("=" * 60)
response = requests.get(f"{BASE_URL}/channels", headers=headers)
print(f"Status: {response.status_code}")
channels = None
if response.status_code == 200:
    channels = response.json()
    print(f"✅ Retrieved {len(channels.get('items', []))} channels")
    for ch in channels.get('items', []):
        print(f"  - {ch.get('name')} (ID: {ch.get('id')})")
else:
    print(f"❌ Failed: {response.text}")

# 4. Get Events
print("\n" + "=" * 60)
print("4. Testing GET /events - Listar eventos")
print("=" * 60)
response = requests.get(f"{BASE_URL}/events", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    events = response.json()
    print(f"✅ Retrieved {len(events.get('items', []))} events")
    for ev in events.get('items', []):
        print(f"  - {ev.get('title')} (ID: {ev.get('id')})")
        print(f"    Date: {ev.get('start_date')}")
        print(f"    Location: {ev.get('location')}")
else:
    print(f"❌ Failed: {response.text}")

# 5. Get single channel
if channels and channels.get('items'):
    channel_id = channels['items'][0]['id']
    print("\n" + "=" * 60)
    print(f"5. Testing GET /channels/{channel_id} - Detalle de canal")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/channels/{channel_id}", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        channel = response.json()
        print(f"✅ Retrieved channel:")
        print(f"  Name: {channel.get('name')}")
        print(f"  Description: {channel.get('description', '')[:100]}")
        print(f"  Subscribers: {channel.get('subscriber_count', 0)}")
    else:
        print(f"❌ Failed: {response.text}")

print("\n" + "=" * 60)
print("Testing completed!")
print("=" * 60)
