"""Quick script to check Redis cache contents."""
import os
import redis
import json

r = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT')),
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)

print("All Redis keys:", r.keys('*'))
print("\nVaR metrics:")
for key in r.keys('VaR:*'):
    print(f"  {key}: {r.get(key)}")

print("\nSharpe metrics:")
for key in r.keys('Sharpe:*'):
    print(f"  {key}: {r.get(key)}")

print("\nBeta metrics:")
for key in r.keys('Beta:*'):
    print(f"  {key}: {r.get(key)}")
