#!/usr/bin/env python3
"""Test editing post images: add and remove"""
import requests
import json
import base64

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MyIsImV4cCI6MTc2NDg4NDY2NCwidHlwZSI6ImFjY2VzcyJ9.Ci13sFT_CwImdQLbmY2VVLpVESbNuNxOpdymkffHzdY"
HEADERS = {"X-Access-Token": TOKEN}

def create_test_image(filename="/tmp/test_edit_image.png"):
    """Create a small test image"""
    # Simple 10x10 red PNG
    img_data = base64.b64decode(
        b'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8z8BQz0AEYBxVSF+FABJADveWkH6oAAAAAElFTkSuQmCC'
    )
    with open(filename, 'wb') as f:
        f.write(img_data)
    return filename

def main():
    print("=" * 60)
    print("PRUEBA DE EDICIÓN DE POST - AGREGAR Y ELIMINAR IMÁGENES")
    print("=" * 60)

    # PASO 1: Crear un post SIN imágenes
    print("\n[PASO 1] Creando post inicial sin imágenes...")

    # Primero obtener un canal
    response = requests.get(f"{BASE_URL}/channels", headers=HEADERS)
    channels_data = response.json()
    channel_id = channels_data['channels'][0]['id']
    print(f"✓ Canal seleccionado: {channel_id}")

    # Crear post sin imágenes
    post_data = {
        "channel_id": channel_id,
        "text": "Post inicial sin imágenes",
        "images": []
    }
    response = requests.post(f"{BASE_URL}/posts", json=post_data, headers=HEADERS)

    if response.status_code == 201:
        post = response.json()
        post_id = post['id']
        print(f"✓ Post creado con ID: {post_id}")
        print(f"  Texto: {post['text']}")
        print(f"  Imágenes: {post.get('images', [])}")
    else:
        print(f"✗ Error al crear post: {response.text}")
        return

    # PASO 2: Subir dos imágenes
    print("\n[PASO 2] Subiendo dos imágenes...")

    create_test_image("/tmp/test_edit_image1.png")
    create_test_image("/tmp/test_edit_image2.png")

    image_urls = []

    for i, img_path in enumerate(["/tmp/test_edit_image1.png", "/tmp/test_edit_image2.png"], 1):
        with open(img_path, 'rb') as f:
            files = {'file': (f'test_image_{i}.png', f, 'image/png')}
            response = requests.post(
                f"{BASE_URL}/posts/upload-image",
                files=files,
                headers={"X-Access-Token": TOKEN}
            )

        if response.status_code == 200:
            result = response.json()
            image_url = result['image_url']
            image_urls.append(image_url)
            print(f"✓ Imagen {i} subida: {image_url}")
        else:
            print(f"✗ Error subiendo imagen {i}: {response.text}")
            return

    # PASO 3: Editar post para AGREGAR las dos imágenes
    print(f"\n[PASO 3] Editando post {post_id} para AGREGAR dos imágenes...")

    update_data = {
        "text": "Post editado con dos imágenes agregadas",
        "images": image_urls
    }

    response = requests.put(
        f"{BASE_URL}/posts/{post_id}",
        json=update_data,
        headers=HEADERS
    )

    if response.status_code == 200:
        updated_post = response.json()
        print(f"✓ Post actualizado")
        print(f"  Texto: {updated_post['text']}")
        print(f"  Imágenes ({len(updated_post.get('images', []))}): {updated_post.get('images', [])}")
    else:
        print(f"✗ Error al actualizar post: {response.text}")
        return

    # PASO 4: Editar post para ELIMINAR una imagen (dejar solo la primera)
    print(f"\n[PASO 4] Editando post {post_id} para ELIMINAR segunda imagen...")

    update_data = {
        "text": "Post con solo una imagen",
        "images": [image_urls[0]]  # Solo la primera imagen
    }

    response = requests.put(
        f"{BASE_URL}/posts/{post_id}",
        json=update_data,
        headers=HEADERS
    )

    if response.status_code == 200:
        updated_post = response.json()
        print(f"✓ Post actualizado")
        print(f"  Texto: {updated_post['text']}")
        print(f"  Imágenes ({len(updated_post.get('images', []))}): {updated_post.get('images', [])}")
    else:
        print(f"✗ Error al actualizar post: {response.text}")
        return

    # PASO 5: Editar post para ELIMINAR todas las imágenes
    print(f"\n[PASO 5] Editando post {post_id} para ELIMINAR todas las imágenes...")

    update_data = {
        "text": "Post sin imágenes de nuevo",
        "images": []
    }

    response = requests.put(
        f"{BASE_URL}/posts/{post_id}",
        json=update_data,
        headers=HEADERS
    )

    if response.status_code == 200:
        updated_post = response.json()
        print(f"✓ Post actualizado")
        print(f"  Texto: {updated_post['text']}")
        print(f"  Imágenes ({len(updated_post.get('images', []))}): {updated_post.get('images', [])}")
    else:
        print(f"✗ Error al actualizar post: {response.text}")
        return

    # PASO 6: Verificar el post final
    print(f"\n[PASO 6] Verificando estado final del post {post_id}...")

    response = requests.get(f"{BASE_URL}/posts/{post_id}", headers=HEADERS)

    if response.status_code == 200:
        final_post = response.json()
        print(f"✓ Post recuperado")
        print(f"  Texto: {final_post['text']}")
        print(f"  Imágenes ({len(final_post.get('images', []))}): {final_post.get('images', [])}")
    else:
        print(f"✗ Error al recuperar post: {response.text}")

    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
