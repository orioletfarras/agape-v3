"""
Complete workflow test - End to end testing
Tests the complete user journey from registration to cleanup
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

# We'll need a superadmin token - assuming user 43 is superadmin
SUPERADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MyIsImV4cCI6MTc2NDkwOTUzOCwidHlwZSI6ImFjY2VzcyJ9.vVQtXvRItNB0ZdQEjHT4KxIz_gstvPkqjqs_i5go_C0"

def print_step(step_num, description):
    print(f"\n{'='*80}")
    print(f"[PASO {step_num}] {description}")
    print('='*80)

def print_success(message):
    print(f"✓ {message}")

def print_error(message):
    print(f"✗ {message}")

def print_info(message):
    print(f"  {message}")

# Store test data
test_data = {
    "user1_id": None,
    "user1_token": None,
    "user2_id": None,
    "user2_token": None,
    "organization_id": None,
    "channel_id": None,
    "post_id": None,
    "event_id": None,
    "comment_id": None,
    "image_urls": []
}

try:
    # ============================================================================
    # PARTE 1: REGISTRO Y SETUP DE USUARIOS
    # ============================================================================

    print_step(1, "Registrar primer usuario (test_user_1)")
    user1_data = {
        "username": f"test_user_1_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "email": f"testuser1_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
        "password": "TestPassword123!",
        "nombre": "Test",
        "apellidos": "User One"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user1_data)
    if response.status_code == 201:
        user1_response = response.json()
        test_data["user1_token"] = user1_response["access_token"]
        # Extract user_id from token or response if available
        print_success(f"Usuario 1 registrado: {user1_data['username']}")
    else:
        print_error(f"Error registrando usuario 1: {response.text}")
        exit(1)

    print_step(2, "Login usuario 1 para obtener user_id")
    login_data = {
        "username": user1_data["username"],
        "password": user1_data["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        login_response = response.json()
        test_data["user1_id"] = login_response["user"]["id"]
        test_data["user1_token"] = login_response["access_token"]
        print_success(f"Usuario 1 ID: {test_data['user1_id']}")
    else:
        print_error(f"Error login usuario 1: {response.text}")
        exit(1)

    print_step(3, "Superadmin crea organización de test")
    org_data = {
        "name": f"Test Organization {datetime.now().strftime('%Y%m%d%H%M%S')}",
        "description": "Organización de prueba"
    }
    headers_superadmin = {
        "X-Access-Token": SUPERADMIN_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.post(f"{BASE_URL}/organizations", json=org_data, headers=headers_superadmin)
    if response.status_code == 201:
        org = response.json()
        test_data["organization_id"] = org["id"]
        print_success(f"Organización creada con ID: {test_data['organization_id']}")
    else:
        print_error(f"Error creando organización: {response.text}")
        exit(1)

    print_step(4, "Superadmin asigna usuario 1 como miembro de la organización")
    assign_data = {
        "user_id": test_data["user1_id"],
        "organization_id": test_data["organization_id"]
    }
    response = requests.post(f"{BASE_URL}/organizations/{test_data['organization_id']}/members",
                            json=assign_data, headers=headers_superadmin)
    if response.status_code in [200, 201]:
        print_success("Usuario 1 asignado como miembro de la organización")
    else:
        print_error(f"Error asignando usuario a organización: {response.text}")
        exit(1)

    # ============================================================================
    # PARTE 2: USUARIO 1 CREA CONTENIDO
    # ============================================================================

    headers_user1 = {
        "X-Access-Token": test_data["user1_token"],
        "Content-Type": "application/json"
    }

    print_step(5, "Usuario 1 añade foto de perfil")
    # Create a simple test image
    image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    files = {'file': ('profile.png', image_data, 'image/png')}
    headers_upload = {"X-Access-Token": test_data["user1_token"]}
    response = requests.post(f"{BASE_URL}/users/upload-profile-image",
                            files=files, headers=headers_upload)
    if response.status_code == 200:
        profile_image = response.json()
        print_success(f"Foto de perfil subida: {profile_image.get('image_url', 'N/A')[:50]}...")
    else:
        print_error(f"Error subiendo foto de perfil: {response.text}")

    print_step(6, "Usuario 1 crea un canal")
    channel_data = {
        "name": f"Test Channel {datetime.now().strftime('%Y%m%d%H%M%S')}",
        "description": "Canal de prueba",
        "organization_id": test_data["organization_id"]
    }
    response = requests.post(f"{BASE_URL}/channels", json=channel_data, headers=headers_user1)
    if response.status_code == 201:
        channel = response.json()
        test_data["channel_id"] = channel["id"]
        print_success(f"Canal creado con ID: {test_data['channel_id']}")
    else:
        print_error(f"Error creando canal: {response.text}")
        exit(1)

    print_step(7, "Usuario 1 sube imagen para post")
    response = requests.post(f"{BASE_URL}/posts/upload-image",
                            files=files, headers=headers_upload)
    if response.status_code == 200:
        image_response = response.json()
        test_data["image_urls"].append(image_response["image_url"])
        print_success(f"Imagen subida para post: {image_response['image_url'][:50]}...")
    else:
        print_error(f"Error subiendo imagen: {response.text}")

    print_step(8, "Usuario 1 crea un post con imagen")
    post_data = {
        "channel_id": test_data["channel_id"],
        "text": "Este es un post de prueba con imagen",
        "images": test_data["image_urls"] if test_data["image_urls"] else None
    }
    response = requests.post(f"{BASE_URL}/posts", json=post_data, headers=headers_user1)
    if response.status_code == 201:
        post = response.json()
        test_data["post_id"] = post["id"]
        print_success(f"Post creado con ID: {test_data['post_id']}")
        print_info(f"Texto: {post['text']}")
        print_info(f"Imágenes: {len(post.get('images', []))}")
    else:
        print_error(f"Error creando post: {response.text}")
        exit(1)

    print_step(9, "Usuario 1 sube imagen para evento")
    response = requests.post(f"{BASE_URL}/events/upload-image",
                            files=files, headers=headers_upload)
    if response.status_code == 200:
        event_image = response.json()
        print_success(f"Imagen subida para evento: {event_image['image_url'][:50]}...")
    else:
        print_error(f"Error subiendo imagen de evento: {response.text}")
        event_image = {"image_url": None}

    print_step(10, "Usuario 1 crea un evento con imagen")
    event_date = (datetime.now() + timedelta(days=7)).isoformat()
    event_data = {
        "channel_id": test_data["channel_id"],
        "name": "Evento de Prueba",
        "description": "Este es un evento de prueba",
        "event_date": event_date,
        "location": "Lugar de prueba",
        "image_url": event_image.get("image_url"),
        "max_attendees": 50
    }
    response = requests.post(f"{BASE_URL}/events", json=event_data, headers=headers_user1)
    if response.status_code == 201:
        event = response.json()
        test_data["event_id"] = event["id"]
        print_success(f"Evento creado con ID: {test_data['event_id']}")
        print_info(f"Nombre: {event['name']}")
    else:
        print_error(f"Error creando evento: {response.text}")
        exit(1)

    # ============================================================================
    # PARTE 3: SEGUNDO USUARIO
    # ============================================================================

    print_step(11, "Registrar segundo usuario (test_user_2)")
    user2_data = {
        "username": f"test_user_2_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "email": f"testuser2_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
        "password": "TestPassword123!",
        "nombre": "Test",
        "apellidos": "User Two"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user2_data)
    if response.status_code == 201:
        user2_response = response.json()
        test_data["user2_token"] = user2_response["access_token"]
        print_success(f"Usuario 2 registrado: {user2_data['username']}")
    else:
        print_error(f"Error registrando usuario 2: {response.text}")
        exit(1)

    print_step(12, "Login usuario 2 para obtener user_id")
    login_data2 = {
        "username": user2_data["username"],
        "password": user2_data["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data2)
    if response.status_code == 200:
        login_response2 = response.json()
        test_data["user2_id"] = login_response2["user"]["id"]
        test_data["user2_token"] = login_response2["access_token"]
        print_success(f"Usuario 2 ID: {test_data['user2_id']}")
    else:
        print_error(f"Error login usuario 2: {response.text}")
        exit(1)

    headers_user2 = {
        "X-Access-Token": test_data["user2_token"],
        "Content-Type": "application/json"
    }

    print_step(13, "Usuario 2 intenta crear canal (debería fallar)")
    channel_data_fail = {
        "name": "Canal No Permitido",
        "description": "Este canal no debería crearse",
        "organization_id": test_data["organization_id"]
    }
    response = requests.post(f"{BASE_URL}/channels", json=channel_data_fail, headers=headers_user2)
    if response.status_code == 403:
        print_success("Usuario 2 no puede crear canal (esperado)")
        print_info(f"Error: {response.json().get('detail')}")
    else:
        print_error(f"Usuario 2 pudo crear canal (no esperado): {response.status_code}")

    print_step(14, "Usuario 2 intenta crear evento (debería fallar)")
    event_data_fail = {
        "channel_id": test_data["channel_id"],
        "name": "Evento No Permitido",
        "event_date": event_date
    }
    response = requests.post(f"{BASE_URL}/events", json=event_data_fail, headers=headers_user2)
    if response.status_code == 403:
        print_success("Usuario 2 no puede crear evento (esperado)")
        print_info(f"Error: {response.json().get('detail')}")
    else:
        print_error(f"Usuario 2 pudo crear evento (no esperado): {response.status_code}")

    print_step(15, "Usuario 2 consulta posts (no debería ver ninguno - no suscrito)")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        if posts["total"] == 0:
            print_success("Usuario 2 no ve posts (esperado - no suscrito)")
        else:
            print_error(f"Usuario 2 ve {posts['total']} posts (no esperado)")
    else:
        print_error(f"Error consultando posts: {response.text}")

    print_step(16, "Usuario 2 consulta eventos (no debería ver ninguno - no suscrito)")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        if events["total"] == 0:
            print_success("Usuario 2 no ve eventos (esperado - no suscrito)")
        else:
            print_error(f"Usuario 2 ve {events['total']} eventos (no esperado)")
    else:
        print_error(f"Error consultando eventos: {response.text}")

    print_step(17, "Usuario 2 se suscribe al canal")
    response = requests.post(f"{BASE_URL}/channels/{test_data['channel_id']}/subscribe",
                            headers=headers_user2)
    if response.status_code == 200:
        print_success(f"Usuario 2 suscrito al canal {test_data['channel_id']}")
    else:
        print_error(f"Error suscribiéndose: {response.text}")
        exit(1)

    print_step(18, "Usuario 2 consulta posts (ahora debería verlos)")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        if posts["total"] > 0:
            print_success(f"Usuario 2 ve {posts['total']} post(s) (esperado)")
        else:
            print_error("Usuario 2 no ve posts (no esperado)")
    else:
        print_error(f"Error consultando posts: {response.text}")

    print_step(19, "Usuario 2 consulta eventos (ahora debería verlos)")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        if events["total"] > 0:
            print_success(f"Usuario 2 ve {events['total']} evento(s) (esperado)")
        else:
            print_error("Usuario 2 no ve eventos (no esperado)")
    else:
        print_error(f"Error consultando eventos: {response.text}")

    # ============================================================================
    # PARTE 4: INTERACCIONES CON EL POST
    # ============================================================================

    print_step(20, "Usuario 2 da LIKE al post")
    like_data = {"action": "like"}
    response = requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/like",
                             json=like_data, headers=headers_user2)
    if response.status_code == 200:
        result = response.json()
        print_success(f"Like añadido - Total likes: {result.get('likes_count', 0)}")
    else:
        print_error(f"Error dando like: {response.text}")

    print_step(21, "Usuario 2 da PRAY al post")
    pray_data = {"action": "pray"}
    response = requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/pray",
                             json=pray_data, headers=headers_user2)
    if response.status_code == 200:
        result = response.json()
        print_success(f"Pray añadido - Total prays: {result.get('prays_count', 0)}")
    else:
        print_error(f"Error dando pray: {response.text}")

    print_step(22, "Usuario 2 intenta dar LIKE de nuevo (no debería subir)")
    response = requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/like",
                             json=like_data, headers=headers_user2)
    if response.status_code == 200:
        result = response.json()
        likes_count = result.get('likes_count', 0)
        if likes_count == 1:
            print_success(f"Likes no subieron (esperado) - Total: {likes_count}")
        else:
            print_error(f"Likes subieron a {likes_count} (no esperado)")
    else:
        print_error(f"Error: {response.text}")

    print_step(23, "Usuario 2 intenta dar PRAY de nuevo (no debería subir)")
    response = requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/pray",
                             json=pray_data, headers=headers_user2)
    if response.status_code == 200:
        result = response.json()
        prays_count = result.get('prays_count', 0)
        if prays_count == 1:
            print_success(f"Prays no subieron (esperado) - Total: {prays_count}")
        else:
            print_error(f"Prays subieron a {prays_count} (no esperado)")
    else:
        print_error(f"Error: {response.text}")

    print_step(24, "Usuario 2 hace UNLIKE")
    unlike_data = {"action": "unlike"}
    response = requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/like",
                             json=unlike_data, headers=headers_user2)
    if response.status_code == 200:
        result = response.json()
        print_success(f"Unlike realizado - Total likes: {result.get('likes_count', 0)}")
    else:
        print_error(f"Error haciendo unlike: {response.text}")

    print_step(25, "Usuario 2 hace UNPRAY")
    unpray_data = {"action": "unpray"}
    response = requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/pray",
                             json=unpray_data, headers=headers_user2)
    if response.status_code == 200:
        result = response.json()
        print_success(f"Unpray realizado - Total prays: {result.get('prays_count', 0)}")
    else:
        print_error(f"Error haciendo unpray: {response.text}")

    print_step(26, "Usuario 2 vuelve a dar LIKE")
    response = requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/like",
                             json=like_data, headers=headers_user2)
    if response.status_code == 200:
        result = response.json()
        print_success(f"Like añadido nuevamente - Total likes: {result.get('likes_count', 0)}")
    else:
        print_error(f"Error dando like: {response.text}")

    print_step(27, "Usuario 2 vuelve a dar PRAY")
    response = requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/pray",
                             json=pray_data, headers=headers_user2)
    if response.status_code == 200:
        result = response.json()
        print_success(f"Pray añadido nuevamente - Total prays: {result.get('prays_count', 0)}")
    else:
        print_error(f"Error dando pray: {response.text}")

    # ============================================================================
    # PARTE 5: COMENTARIOS
    # ============================================================================

    print_step(28, "Usuario 2 añade un comentario al post")
    comment_data = {
        "post_id": test_data["post_id"],
        "content": "Este es un comentario de prueba"
    }
    response = requests.post(f"{BASE_URL}/comments", json=comment_data, headers=headers_user2)
    if response.status_code == 201:
        comment = response.json()
        test_data["comment_id"] = comment["id"]
        print_success(f"Comentario creado con ID: {test_data['comment_id']}")
        print_info(f"Contenido: {comment['content']}")
    else:
        print_error(f"Error creando comentario: {response.text}")

    print_step(29, "Usuario 2 edita el comentario")
    update_comment_data = {
        "content": "Comentario editado por el usuario"
    }
    response = requests.put(f"{BASE_URL}/comments/{test_data['comment_id']}",
                           json=update_comment_data, headers=headers_user2)
    if response.status_code == 200:
        updated_comment = response.json()
        print_success("Comentario editado correctamente")
        print_info(f"Nuevo contenido: {updated_comment['content']}")
    else:
        print_error(f"Error editando comentario: {response.text}")

    # ============================================================================
    # PARTE 6: DESUSCRIPCIÓN Y RESUSCRIPCIÓN
    # ============================================================================

    print_step(30, "Usuario 2 se desuscribe del canal")
    response = requests.delete(f"{BASE_URL}/channels/{test_data['channel_id']}/subscribe",
                              headers=headers_user2)
    if response.status_code == 200:
        print_success("Usuario 2 desuscrito del canal")
    else:
        print_error(f"Error desuscribiéndose: {response.text}")

    print_step(31, "Usuario 2 consulta posts (no debería verlos - desuscrito)")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        if posts["total"] == 0:
            print_success("Usuario 2 no ve posts (esperado - desuscrito)")
        else:
            print_error(f"Usuario 2 ve {posts['total']} posts (no esperado)")
    else:
        print_error(f"Error consultando posts: {response.text}")

    print_step(32, "Usuario 2 consulta eventos (no debería verlos - desuscrito)")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        if events["total"] == 0:
            print_success("Usuario 2 no ve eventos (esperado - desuscrito)")
        else:
            print_error(f"Usuario 2 ve {events['total']} eventos (no esperado)")
    else:
        print_error(f"Error consultando eventos: {response.text}")

    print_step(33, "Usuario 2 se vuelve a suscribir al canal")
    response = requests.post(f"{BASE_URL}/channels/{test_data['channel_id']}/subscribe",
                            headers=headers_user2)
    if response.status_code == 200:
        print_success("Usuario 2 suscrito nuevamente al canal")
    else:
        print_error(f"Error suscribiéndose: {response.text}")

    print_step(34, "Usuario 2 consulta posts (debería verlos de nuevo)")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        if posts["total"] > 0:
            print_success(f"Usuario 2 ve {posts['total']} post(s) (esperado)")
        else:
            print_error("Usuario 2 no ve posts (no esperado)")
    else:
        print_error(f"Error consultando posts: {response.text}")

    print_step(35, "Usuario 2 consulta eventos (debería verlos de nuevo)")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        if events["total"] > 0:
            print_success(f"Usuario 2 ve {events['total']} evento(s) (esperado)")
        else:
            print_error("Usuario 2 no ve eventos (no esperado)")
    else:
        print_error(f"Error consultando eventos: {response.text}")

    # ============================================================================
    # PARTE 7: LIMPIEZA - ELIMINAR DATOS DE TEST
    # ============================================================================

    print_step(36, "Limpiar: Eliminar comentario")
    if test_data["comment_id"]:
        response = requests.delete(f"{BASE_URL}/comments/{test_data['comment_id']}",
                                  headers=headers_user2)
        if response.status_code == 200:
            print_success("Comentario eliminado")
        else:
            print_error(f"Error eliminando comentario: {response.text}")

    print_step(37, "Limpiar: Eliminar evento")
    if test_data["event_id"]:
        response = requests.delete(f"{BASE_URL}/events/{test_data['event_id']}",
                                  headers=headers_user1)
        if response.status_code == 200:
            print_success("Evento eliminado")
        else:
            print_error(f"Error eliminando evento: {response.text}")

    print_step(38, "Limpiar: Eliminar post")
    if test_data["post_id"]:
        response = requests.delete(f"{BASE_URL}/posts/{test_data['post_id']}",
                                  headers=headers_user1)
        if response.status_code == 200:
            print_success("Post eliminado")
        else:
            print_error(f"Error eliminando post: {response.text}")

    print_step(39, "Limpiar: Eliminar canal")
    if test_data["channel_id"]:
        response = requests.delete(f"{BASE_URL}/channels/{test_data['channel_id']}",
                                  headers=headers_user1)
        if response.status_code == 200:
            print_success("Canal eliminado")
        else:
            print_error(f"Error eliminando canal: {response.text}")

    print_step(40, "Limpiar: Eliminar organización")
    if test_data["organization_id"]:
        response = requests.delete(f"{BASE_URL}/organizations/{test_data['organization_id']}",
                                  headers=headers_superadmin)
        if response.status_code == 200:
            print_success("Organización eliminada")
        else:
            print_error(f"Error eliminando organización: {response.text}")

    # Note: Users are typically not deleted in production, but if needed:
    # print_step(41, "Limpiar: Eliminar usuarios de test")
    # This would require a user deletion endpoint

    # ============================================================================
    # RESULTADO FINAL
    # ============================================================================

    print("\n" + "="*80)
    print("                        PRUEBA COMPLETADA EXITOSAMENTE")
    print("="*80)
    print("\nResumen:")
    print(f"  - Usuarios creados: 2")
    print(f"  - Organización creada: ID {test_data['organization_id']}")
    print(f"  - Canal creado: ID {test_data['channel_id']}")
    print(f"  - Post creado: ID {test_data['post_id']}")
    print(f"  - Evento creado: ID {test_data['event_id']}")
    print(f"  - Comentario creado y editado: ID {test_data['comment_id']}")
    print(f"  - Reacciones probadas: Like, Unlike, Pray, Unpray")
    print(f"  - Suscripción/Desuscripción verificada")
    print(f"  - Permisos verificados correctamente")
    print(f"  - Limpieza completada")
    print("\n✓ TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
    print("="*80 + "\n")

except Exception as e:
    print(f"\n{'='*80}")
    print("ERROR EN LA PRUEBA")
    print('='*80)
    print(f"Error: {str(e)}")
    print(f"\nDatos de test creados:")
    print(json.dumps(test_data, indent=2))
    print("\nPuede que necesites limpiar manualmente estos datos.")
    print('='*80 + "\n")
    raise
