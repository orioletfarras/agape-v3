"""
Test script for post reactions (like and pray)
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MyIsImV4cCI6MTc2NDkwOTUzOCwidHlwZSI6ImFjY2VzcyJ9.vVQtXvRItNB0ZdQEjHT4KxIz_gstvPkqjqs_i5go_C0"

HEADERS = {
    "X-Access-Token": TOKEN,
    "Content-Type": "application/json"
}

print("=" * 60)
print("PRUEBA DE REACCIONES A POSTS - LIKE Y PRAY")
print("=" * 60)

# PASO 1: Obtener canales
print("\n[PASO 1] Obteniendo canales...")
response = requests.get(f"{BASE_URL}/channels", headers=HEADERS)
if response.status_code == 200:
    channels = response.json().get("channels", [])
    if channels:
        channel_id = channels[0]["id"]
        print(f"✓ Canal seleccionado: {channel_id}")
    else:
        print("✗ No hay canales disponibles")
        exit(1)
else:
    print(f"✗ Error obteniendo canales: {response.text}")
    exit(1)

# PASO 2: Crear un post
print(f"\n[PASO 2] Creando post en canal {channel_id}...")
post_data = {
    "channel_id": channel_id,
    "text": "Este es un post de prueba para reacciones"
}
response = requests.post(f"{BASE_URL}/posts", json=post_data, headers=HEADERS)
if response.status_code == 201:
    post = response.json()
    post_id = post["id"]
    print(f"✓ Post creado con ID: {post_id}")
    print(f"  Texto: {post['text']}")
    print(f"  Likes: {post['likes_count']}")
    print(f"  Prays: {post['prays_count']}")
    print(f"  Usuario ha dado like: {post['is_liked']}")
    print(f"  Usuario ha rezado: {post['is_prayed']}")
else:
    print(f"✗ Error creando post: {response.text}")
    exit(1)

# PASO 3: Dar LIKE al post
print(f"\n[PASO 3] Dando LIKE al post {post_id}...")
like_data = {"action": "like"}
response = requests.patch(f"{BASE_URL}/posts/{post_id}/like", json=like_data, headers=HEADERS)
if response.status_code == 200:
    result = response.json()
    print(f"✓ Reacción actualizada")
    print(f"  Mensaje: {result.get('message', 'N/A')}")
    print(f"  Likes count: {result.get('likes_count', 'N/A')}")
    print(f"  Usuario ha dado like: {result.get('is_liked', 'N/A')}")
else:
    print(f"✗ Error dando like: {response.text}")

# PASO 4: Verificar el post con el like
print(f"\n[PASO 4] Verificando post {post_id} después del like...")
response = requests.get(f"{BASE_URL}/posts/{post_id}", headers=HEADERS)
if response.status_code == 200:
    post = response.json()
    print(f"✓ Post recuperado")
    print(f"  Likes: {post['likes_count']}")
    print(f"  Prays: {post['prays_count']}")
    print(f"  Usuario ha dado like: {post['is_liked']}")
    print(f"  Usuario ha rezado: {post['is_prayed']}")
else:
    print(f"✗ Error recuperando post: {response.text}")

# PASO 5: Dar PRAY al post
print(f"\n[PASO 5] Dando PRAY al post {post_id}...")
pray_data = {"action": "pray"}
response = requests.patch(f"{BASE_URL}/posts/{post_id}/pray", json=pray_data, headers=HEADERS)
if response.status_code == 200:
    result = response.json()
    print(f"✓ Reacción actualizada")
    print(f"  Mensaje: {result.get('message', 'N/A')}")
    print(f"  Prays count: {result.get('prays_count', 'N/A')}")
    print(f"  Usuario ha rezado: {result.get('is_prayed', 'N/A')}")
else:
    print(f"✗ Error dando pray: {response.text}")

# PASO 6: Verificar el post con like y pray
print(f"\n[PASO 6] Verificando post {post_id} con like y pray...")
response = requests.get(f"{BASE_URL}/posts/{post_id}", headers=HEADERS)
if response.status_code == 200:
    post = response.json()
    print(f"✓ Post recuperado")
    print(f"  Likes: {post['likes_count']}")
    print(f"  Prays: {post['prays_count']}")
    print(f"  Usuario ha dado like: {post['is_liked']}")
    print(f"  Usuario ha rezado: {post['is_prayed']}")
else:
    print(f"✗ Error recuperando post: {response.text}")

# PASO 7: Quitar el LIKE
print(f"\n[PASO 7] Quitando LIKE del post {post_id}...")
unlike_data = {"action": "unlike"}
response = requests.patch(f"{BASE_URL}/posts/{post_id}/like", json=unlike_data, headers=HEADERS)
if response.status_code == 200:
    result = response.json()
    print(f"✓ Reacción actualizada")
    print(f"  Mensaje: {result.get('message', 'N/A')}")
    print(f"  Likes count: {result.get('likes_count', 'N/A')}")
    print(f"  Usuario ha dado like: {result.get('is_liked', 'N/A')}")
else:
    print(f"✗ Error quitando like: {response.text}")

# PASO 8: Verificar estado después de quitar like
print(f"\n[PASO 8] Verificando estado después de quitar like...")
response = requests.get(f"{BASE_URL}/posts/{post_id}", headers=HEADERS)
if response.status_code == 200:
    post = response.json()
    print(f"✓ Post recuperado")
    print(f"  Likes: {post['likes_count']}")
    print(f"  Prays: {post['prays_count']}")
    print(f"  Usuario ha dado like: {post['is_liked']}")
    print(f"  Usuario ha rezado: {post['is_prayed']}")
else:
    print(f"✗ Error recuperando post: {response.text}")

# PASO 9: Quitar el PRAY
print(f"\n[PASO 9] Quitando PRAY del post {post_id}...")
unpray_data = {"action": "unpray"}
response = requests.patch(f"{BASE_URL}/posts/{post_id}/pray", json=unpray_data, headers=HEADERS)
if response.status_code == 200:
    result = response.json()
    print(f"✓ Reacción actualizada")
    print(f"  Mensaje: {result.get('message', 'N/A')}")
    print(f"  Prays count: {result.get('prays_count', 'N/A')}")
    print(f"  Usuario ha rezado: {result.get('is_prayed', 'N/A')}")
else:
    print(f"✗ Error quitando pray: {response.text}")

# PASO 10: Verificar estado final (sin likes ni prays)
print(f"\n[PASO 10] Verificando estado final del post {post_id}...")
response = requests.get(f"{BASE_URL}/posts/{post_id}", headers=HEADERS)
if response.status_code == 200:
    post = response.json()
    print(f"✓ Post recuperado")
    print(f"  Likes: {post['likes_count']}")
    print(f"  Prays: {post['prays_count']}")
    print(f"  Usuario ha dado like: {post['is_liked']}")
    print(f"  Usuario ha rezado: {post['is_prayed']}")
else:
    print(f"✗ Error recuperando post: {response.text}")

print("\n" + "=" * 60)
print("PRUEBA COMPLETADA")
print("=" * 60)
