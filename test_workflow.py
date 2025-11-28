#!/usr/bin/env python3
"""Test workflow: Create channel -> Create post -> View posts"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MyIsImV4cCI6MTc2NDg4NDY2NCwidHlwZSI6ImFjY2VzcyJ9.Ci13sFT_CwImdQLbmY2VVLpVESbNuNxOpdymkffHzdY"
HEADERS = {"X-Access-Token": TOKEN, "Content-Type": "application/json"}

def main():
    print("=" * 60)
    print("PRUEBA COMPLETA DE ENDPOINTS")
    print("=" * 60)

    # PASO 1: Obtener organizaciones disponibles
    print("\n[PASO 1] Obteniendo organizaciones...")
    response = requests.get(f"{BASE_URL}/organizations", headers=HEADERS)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        organizations = response.json()
        if organizations:
            organization_id = organizations[0]["id"]
            print(f"✓ Usando organización: {organizations[0]['name']} (ID: {organization_id})")
        else:
            print("✗ No hay organizaciones disponibles")
            return
    else:
        print(f"✗ Error: {response.text}")
        return

    # PASO 2: Crear un canal
    print("\n[PASO 2] Creando canal...")
    channel_data = {
        "name": "Canal de Prueba",
        "description": "Canal para probar endpoints",
        "organization_id": organization_id
    }
    response = requests.post(f"{BASE_URL}/channels", json=channel_data, headers=HEADERS)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        channel = response.json()
        channel_id = channel["id"]
        print(f"✓ Canal creado con ID: {channel_id}")
        print(f"  Nombre: {channel['name']}")
        print(f"  Suscrito: {channel.get('is_subscribed', 'N/A')}")
    else:
        print(f"✗ Error: {response.text}")
        return

    # PASO 3: Verificar que el canal aparece en la lista (subscribed_only=true por defecto)
    print("\n[PASO 3] Obteniendo canales suscritos...")
    response = requests.get(f"{BASE_URL}/channels", headers=HEADERS)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        channels = response.json()
        print(f"✓ Total de canales suscritos: {channels['total']}")
        if channels['channels']:
            print(f"  - {channels['channels'][0]['name']}")
    else:
        print(f"✗ Error: {response.text}")

    # PASO 4: Crear un post en el canal
    print("\n[PASO 4] Creando post en el canal...")
    post_data = {
        "channel_id": channel_id,
        "text": "Este es un post de prueba para verificar el funcionamiento de los endpoints"
    }
    response = requests.post(f"{BASE_URL}/posts", json=post_data, headers=HEADERS)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        post = response.json()
        post_id = post["id"]
        print(f"✓ Post creado con ID: {post_id}")
        print(f"  Texto: {post['text'][:50]}...")
    else:
        print(f"✗ Error: {response.text}")
        return

    # PASO 5: Ver posts (subscribed_only=true por defecto)
    print("\n[PASO 5] Obteniendo posts de canales suscritos...")
    response = requests.get(f"{BASE_URL}/posts", headers=HEADERS)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        posts = response.json()
        print(f"✓ Total de posts: {posts['total']}")
        if posts['posts']:
            print(f"  - Post ID {posts['posts'][0]['id']}: {posts['posts'][0]['text'][:50]}...")
    else:
        print(f"✗ Error: {response.text}")

    # PASO 6: Probar subscribed_only=false
    print("\n[PASO 6] Obteniendo TODOS los posts (subscribed_only=false)...")
    response = requests.get(f"{BASE_URL}/posts?subscribed_only=false", headers=HEADERS)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        posts = response.json()
        print(f"✓ Total de posts (todos): {posts['total']}")
    else:
        print(f"✗ Error: {response.text}")

    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
