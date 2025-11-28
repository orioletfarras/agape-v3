#!/usr/bin/env python3
"""Test image upload workflow: Upload image -> Create post with image"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MyIsImV4cCI6MTc2NDg4NDY2NCwidHlwZSI6ImFjY2VzcyJ9.Ci13sFT_CwImdQLbmY2VVLpVESbNuNxOpdymkffHzdY"
HEADERS = {"X-Access-Token": TOKEN}

def main():
    print("=" * 60)
    print("PRUEBA DE SUBIDA DE IMAGEN Y CREACIÓN DE POST")
    print("=" * 60)

    # PASO 1: Obtener un canal existente
    print("\n[PASO 1] Obteniendo canales...")
    response = requests.get(f"{BASE_URL}/channels", headers=HEADERS)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        channels_data = response.json()
        if channels_data['channels']:
            channel_id = channels_data['channels'][0]['id']
            print(f"✓ Usando canal: {channels_data['channels'][0]['name']} (ID: {channel_id})")
        else:
            print("✗ No hay canales disponibles")
            return
    else:
        print(f"✗ Error: {response.text}")
        return

    # PASO 2: Subir imagen
    print("\n[PASO 2] Subiendo imagen de prueba...")
    with open('/tmp/test_post_image.png', 'rb') as f:
        files = {'file': ('test_image.png', f, 'image/png')}
        response = requests.post(
            f"{BASE_URL}/posts/upload-image",
            files=files,
            headers={"X-Access-Token": TOKEN}
        )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        image_url = result['image_url']
        print(f"✓ Imagen subida exitosamente")
        print(f"  URL: {image_url}")
    else:
        print(f"✗ Error: {response.text}")
        return

    # PASO 3: Crear post con la imagen
    print("\n[PASO 3] Creando post con imagen...")
    post_data = {
        "channel_id": channel_id,
        "text": "Este es un post de prueba con una imagen adjunta",
        "images": [image_url]
    }
    response = requests.post(
        f"{BASE_URL}/posts",
        json=post_data,
        headers=HEADERS
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        post = response.json()
        print(f"✓ Post creado con ID: {post['id']}")
        print(f"  Texto: {post['text']}")
        print(f"  Imágenes: {post.get('images', [])}")
    else:
        print(f"✗ Error: {response.text}")
        return

    # PASO 4: Verificar que el post se ve correctamente
    print("\n[PASO 4] Verificando post creado...")
    response = requests.get(
        f"{BASE_URL}/posts/{post['id']}",
        headers=HEADERS
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        post_retrieved = response.json()
        print(f"✓ Post recuperado exitosamente")
        print(f"  Texto: {post_retrieved['text']}")
        print(f"  Imágenes: {post_retrieved.get('images', [])}")
        if post_retrieved.get('images'):
            print(f"  ✓ La imagen está presente en el post")
        else:
            print(f"  ✗ La imagen NO está presente en el post")
    else:
        print(f"✗ Error: {response.text}")

    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
