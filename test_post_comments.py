"""
Test script for post comments
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
print("PRUEBA DE COMENTARIOS EN POSTS")
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
    "text": "Este es un post de prueba para comentarios"
}
response = requests.post(f"{BASE_URL}/posts", json=post_data, headers=HEADERS)
if response.status_code == 201:
    post = response.json()
    post_id = post["id"]
    print(f"✓ Post creado con ID: {post_id}")
    print(f"  Texto: {post['text']}")
    print(f"  Comentarios: {post.get('comments_count', 0)}")
else:
    print(f"✗ Error creando post: {response.text}")
    exit(1)

# PASO 3: Añadir primer comentario
print(f"\n[PASO 3] Añadiendo primer comentario al post {post_id}...")
comment_data = {
    "post_id": post_id,
    "content": "Este es el primer comentario de prueba"
}
response = requests.post(f"{BASE_URL}/comments", json=comment_data, headers=HEADERS)
if response.status_code == 201:
    comment1 = response.json()
    comment1_id = comment1["id"]
    print(f"✓ Comentario creado con ID: {comment1_id}")
    print(f"  Contenido: {comment1['content']}")
    print(f"  Autor: {comment1.get('author', {}).get('username', 'N/A')}")
else:
    print(f"✗ Error creando comentario: {response.text}")

# PASO 4: Añadir segundo comentario
print(f"\n[PASO 4] Añadiendo segundo comentario al post {post_id}...")
comment_data = {
    "post_id": post_id,
    "content": "Este es el segundo comentario de prueba"
}
response = requests.post(f"{BASE_URL}/comments", json=comment_data, headers=HEADERS)
if response.status_code == 201:
    comment2 = response.json()
    comment2_id = comment2["id"]
    print(f"✓ Comentario creado con ID: {comment2_id}")
    print(f"  Contenido: {comment2['content']}")
else:
    print(f"✗ Error creando comentario: {response.text}")

# PASO 5: Obtener comentarios del post
print(f"\n[PASO 5] Obteniendo comentarios del post {post_id}...")
response = requests.get(f"{BASE_URL}/comments/post/{post_id}", headers=HEADERS)
if response.status_code == 200:
    comments_response = response.json()
    comments = comments_response.get("comments", [])
    total = comments_response.get("total", 0)
    print(f"✓ Comentarios obtenidos: {total}")
    for i, comment in enumerate(comments, 1):
        print(f"  {i}. ID: {comment['id']} - {comment['content']}")
        print(f"     Autor: {comment.get('author', {}).get('username', 'N/A')}")
else:
    print(f"✗ Error obteniendo comentarios: {response.text}")

# PASO 6: Editar el primer comentario
print(f"\n[PASO 6] Editando el primer comentario (ID: {comment1_id})...")
update_data = {
    "content": "Este comentario ha sido editado"
}
response = requests.put(f"{BASE_URL}/comments/{comment1_id}", json=update_data, headers=HEADERS)
if response.status_code == 200:
    updated_comment = response.json()
    print(f"✓ Comentario editado")
    print(f"  Nuevo contenido: {updated_comment['content']}")
else:
    print(f"✗ Error editando comentario: {response.text}")

# PASO 7: Verificar comentarios después de editar
print(f"\n[PASO 7] Verificando comentarios después de editar...")
response = requests.get(f"{BASE_URL}/comments/post/{post_id}", headers=HEADERS)
if response.status_code == 200:
    comments_response = response.json()
    comments = comments_response.get("comments", [])
    print(f"✓ Comentarios obtenidos: {len(comments)}")
    for i, comment in enumerate(comments, 1):
        print(f"  {i}. ID: {comment['id']} - {comment['content']}")
else:
    print(f"✗ Error obteniendo comentarios: {response.text}")

# PASO 8: Eliminar el segundo comentario
print(f"\n[PASO 8] Eliminando el segundo comentario (ID: {comment2_id})...")
response = requests.delete(f"{BASE_URL}/comments/{comment2_id}", headers=HEADERS)
if response.status_code == 200:
    result = response.json()
    print(f"✓ Comentario eliminado")
    print(f"  Mensaje: {result.get('message', 'N/A')}")
else:
    print(f"✗ Error eliminando comentario: {response.text}")

# PASO 9: Verificar comentarios después de eliminar
print(f"\n[PASO 9] Verificando comentarios después de eliminar...")
response = requests.get(f"{BASE_URL}/comments/post/{post_id}", headers=HEADERS)
if response.status_code == 200:
    comments_response = response.json()
    comments = comments_response.get("comments", [])
    total = comments_response.get("total", 0)
    print(f"✓ Comentarios restantes: {total}")
    for i, comment in enumerate(comments, 1):
        print(f"  {i}. ID: {comment['id']} - {comment['content']}")
else:
    print(f"✗ Error obteniendo comentarios: {response.text}")

# PASO 10: Verificar el post para ver el contador de comentarios
print(f"\n[PASO 10] Verificando post {post_id} para ver contador de comentarios...")
response = requests.get(f"{BASE_URL}/posts/{post_id}", headers=HEADERS)
if response.status_code == 200:
    post = response.json()
    print(f"✓ Post recuperado")
    print(f"  Texto: {post['text']}")
    print(f"  Comentarios: {post.get('comments_count', 0)}")
else:
    print(f"✗ Error recuperando post: {response.text}")

print("\n" + "=" * 60)
print("PRUEBA COMPLETADA")
print("=" * 60)
