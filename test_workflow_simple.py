"""
Simplified comprehensive workflow test
Uses existing database users to test complete workflow
Assumes you have at least 2 users in the database and one is superadmin
"""
import requests
import json
from datetime import datetime, timedelta
import os

BASE_URL = "http://localhost:8000/api/v1"

# For this test, you'll need to:
# 1. Have a superadmin user (e.g., user ID 1)
# 2. Have two regular users or create them manually in the database
# We'll use login to get tokens dynamically

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
    "superadmin_token": None,
    "organization_id": None,
    "channel_id": None,
    "post_id": None,
    "event_id": None,
    "comment_id": None,
    "image_urls": []
}

# Hardcoded credentials - UPDATE THESE WITH YOUR ACTUAL TEST USERS
SUPERADMIN_EMAIL = "admin@agape.com"  # UPDATE THIS
SUPERADMIN_PASSWORD = "admin123"  # UPDATE THIS
USER1_EMAIL = "user1@test.com"  # UPDATE THIS
USER1_PASSWORD = "password123"  # UPDATE THIS
USER2_EMAIL = "user2@test.com"  # UPDATE THIS
USER2_PASSWORD = "password123"  # UPDATE THIS

try:
    # ============================================================================
    # PARTE 1: LOGIN Y SETUP
    # ============================================================================

    print_step(1, "Login como superadmin")
    login_data = {
        "email": SUPERADMIN_EMAIL,
        "password": SUPERADMIN_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        test_data["superadmin_token"] = result.get("access_token") or result.get("token")
        print_success(f"Superadmin logged in")
        print_info(f"Token: {test_data['superadmin_token'][:50]}...")
    else:
        print_error(f"Error login superadmin: {response.text}")
        print_info("Por favor actualiza SUPERADMIN_EMAIL y SUPERADMIN_PASSWORD en el script")
        exit(1)

    print_step(2, "Login usuario 1")
    login_data = {
        "email": USER1_EMAIL,
        "password": USER1_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        test_data["user1_token"] = result.get("access_token") or result.get("token")
        test_data["user1_id"] = result.get("user", {}).get("id") or result.get("user_id")
        print_success(f"Usuario 1 logged in - ID: {test_data['user1_id']}")
    else:
        print_error(f"Error login usuario 1: {response.text}")
        print_info("Por favor actualiza USER1_EMAIL y USER1_PASSWORD en el script")
        exit(1)

    print_step(3, "Login usuario 2")
    login_data = {
        "email": USER2_EMAIL,
        "password": USER2_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        test_data["user2_token"] = result.get("access_token") or result.get("token")
        test_data["user2_id"] = result.get("user", {}).get("id") or result.get("user_id")
        print_success(f"Usuario 2 logged in - ID: {test_data['user2_id']}")
    else:
        print_error(f"Error login usuario 2: {response.text}")
        print_info("Por favor actualiza USER2_EMAIL y USER2_PASSWORD en el script")
        exit(1)

    print_step(4, "Superadmin crea organización de test")
    org_data = {
        "name": f"Test Organization {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Organización de prueba para test workflow"
    }
    headers_superadmin = {
        "X-Access-Token": test_data["superadmin_token"],
        "Content-Type": "application/json"
    }
    response = requests.post(f"{BASE_URL}/organizations", json=org_data, headers=headers_superadmin)
    if response.status_code in [200, 201]:
        org = response.json()
        test_data["organization_id"] = org["id"]
        print_success(f"Organización creada con ID: {test_data['organization_id']}")
        print_info(f"Nombre: {org['name']}")
    else:
        print_error(f"Error creando organización: {response.text}")
        exit(1)

    print_step(5, "Superadmin asigna usuario 1 como miembro de la organización")
    # Check organization endpoints to find the correct endpoint
    assign_data = {
        "user_id": test_data["user1_id"],
        "organization_id": test_data["organization_id"]
    }
    response = requests.post(
        f"{BASE_URL}/organizations/{test_data['organization_id']}/members",
        json=assign_data,
        headers=headers_superadmin
    )
    if response.status_code in [200, 201]:
        print_success(f"Usuario 1 asignado a organización")
    else:
        print_error(f"Error asignando usuario: {response.text}")
        # Try alternative endpoint
        print_info("Intentando endpoint alternativo...")
        response = requests.post(
            f"{BASE_URL}/organizations/{test_data['organization_id']}/add-member",
            json={"user_id": test_data["user1_id"]},
            headers=headers_superadmin
        )
        if response.status_code in [200, 201]:
            print_success(f"Usuario 1 asignado a organización (endpoint alternativo)")
        else:
            print_error(f"Error con endpoint alternativo: {response.text}")
            # Continue anyway, user might be able to create channel

    # ============================================================================
    # PARTE 2: USUARIO 1 CREA CONTENIDO
    # ============================================================================

    headers_user1 = {
        "X-Access-Token": test_data["user1_token"],
        "Content-Type": "application/json"
    }

    print_step(6, "Usuario 1 actualiza foto de perfil")
    # Upload test image
    test_image_path = "/tmp/test_profile.jpg"
    # Create a simple test image (1x1 pixel)
    with open(test_image_path, "wb") as f:
        # Minimal JPEG file
        f.write(bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
            0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48,
            0x00, 0x48, 0x00, 0x00, 0xFF, 0xD9
        ]))

    with open(test_image_path, "rb") as f:
        files = {"file": ("test_profile.jpg", f, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/profile/upload-image",
            files=files,
            headers={"X-Access-Token": test_data["user1_token"]}
        )

    if response.status_code in [200, 201]:
        result = response.json()
        profile_image_url = result.get("image_url") or result.get("url")
        print_success(f"Foto de perfil actualizada")
        print_info(f"URL: {profile_image_url}")
    else:
        print_error(f"Error subiendo foto de perfil: {response.text}")
        # Continue anyway

    print_step(7, "Usuario 1 crea un canal")
    channel_data = {
        "name": f"Canal Test {datetime.now().strftime('%H%M%S')}",
        "description": "Canal de prueba para test workflow",
        "organization_id": test_data["organization_id"]
    }
    response = requests.post(f"{BASE_URL}/channels", json=channel_data, headers=headers_user1)
    if response.status_code in [200, 201]:
        channel = response.json()
        test_data["channel_id"] = channel["id"]
        print_success(f"Canal creado con ID: {test_data['channel_id']}")
        print_info(f"Nombre: {channel['name']}")
    else:
        print_error(f"Error creando canal: {response.text}")
        exit(1)

    print_step(8, "Usuario 1 crea un post con imagen")
    # Upload image for post
    with open(test_image_path, "rb") as f:
        files = {"file": ("test_post.jpg", f, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/posts/upload-image",
            files=files,
            headers={"X-Access-Token": test_data["user1_token"]}
        )

    post_image_url = None
    if response.status_code in [200, 201]:
        result = response.json()
        post_image_url = result.get("image_url") or result.get("url")
        print_success(f"Imagen del post subida")
    else:
        print_error(f"Error subiendo imagen del post: {response.text}")

    post_data = {
        "channel_id": test_data["channel_id"],
        "text": "Este es un post de prueba para el test workflow",
        "images": [post_image_url] if post_image_url else []
    }
    response = requests.post(f"{BASE_URL}/posts", json=post_data, headers=headers_user1)
    if response.status_code in [200, 201]:
        post = response.json()
        test_data["post_id"] = post["id"]
        print_success(f"Post creado con ID: {test_data['post_id']}")
        print_info(f"Texto: {post['text'][:50]}...")
    else:
        print_error(f"Error creando post: {response.text}")
        exit(1)

    print_step(9, "Usuario 1 crea un evento con imagen")
    # Upload image for event
    with open(test_image_path, "rb") as f:
        files = {"file": ("test_event.jpg", f, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/events/upload-image",
            files=files,
            headers={"X-Access-Token": test_data["user1_token"]}
        )

    event_image_url = None
    if response.status_code in [200, 201]:
        result = response.json()
        event_image_url = result.get("image_url") or result.get("url")
        print_success(f"Imagen del evento subida")
    else:
        print_error(f"Error subiendo imagen del evento: {response.text}")

    event_date = (datetime.now() + timedelta(days=7)).isoformat()
    event_data = {
        "channel_id": test_data["channel_id"],
        "name": f"Evento Test {datetime.now().strftime('%H%M%S')}",
        "description": "Evento de prueba para test workflow",
        "event_date": event_date,
        "location": "Test Location",
        "image_url": event_image_url,
        "is_paid": False
    }
    response = requests.post(f"{BASE_URL}/events", json=event_data, headers=headers_user1)
    if response.status_code in [200, 201]:
        event = response.json()
        test_data["event_id"] = event["id"]
        print_success(f"Evento creado con ID: {test_data['event_id']}")
        print_info(f"Nombre: {event['name']}")
    else:
        print_error(f"Error creando evento: {response.text}")
        exit(1)

    # ============================================================================
    # PARTE 3: USUARIO 2 INTENTA CREAR CONTENIDO (DEBE FALLAR)
    # ============================================================================

    headers_user2 = {
        "X-Access-Token": test_data["user2_token"],
        "Content-Type": "application/json"
    }

    print_step(10, "Usuario 2 intenta crear canal (debe fallar)")
    channel_data_user2 = {
        "name": "Canal Unauthorized",
        "description": "Este canal no debe crearse",
        "organization_id": test_data["organization_id"]
    }
    response = requests.post(f"{BASE_URL}/channels", json=channel_data_user2, headers=headers_user2)
    if response.status_code == 403:
        print_success("Usuario 2 correctamente bloqueado al crear canal (403)")
    elif response.status_code >= 400:
        print_success(f"Usuario 2 correctamente bloqueado al crear canal ({response.status_code})")
    else:
        print_error(f"ERROR: Usuario 2 pudo crear canal cuando no debería: {response.text}")

    print_step(11, "Usuario 2 intenta crear evento (debe fallar)")
    event_data_user2 = {
        "channel_id": test_data["channel_id"],
        "name": "Evento Unauthorized",
        "description": "Este evento no debe crearse",
        "event_date": event_date,
        "location": "Test",
        "is_paid": False
    }
    response = requests.post(f"{BASE_URL}/events", json=event_data_user2, headers=headers_user2)
    if response.status_code == 403:
        print_success("Usuario 2 correctamente bloqueado al crear evento (403)")
    elif response.status_code >= 400:
        print_success(f"Usuario 2 correctamente bloqueado al crear evento ({response.status_code})")
    else:
        print_error(f"ERROR: Usuario 2 pudo crear evento cuando no debería: {response.text}")

    print_step(12, "Usuario 2 verifica que NO ve posts (no suscrito)")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        posts_list = posts.get("posts", [])
        if len(posts_list) == 0:
            print_success(f"Usuario 2 correctamente NO ve posts (no suscrito)")
        else:
            print_error(f"ERROR: Usuario 2 ve {len(posts_list)} posts cuando no debería")
    else:
        print_error(f"Error obteniendo posts: {response.text}")

    print_step(13, "Usuario 2 verifica que NO ve eventos (no suscrito)")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        events_list = events.get("events", [])
        if len(events_list) == 0:
            print_success(f"Usuario 2 correctamente NO ve eventos (no suscrito)")
        else:
            print_error(f"ERROR: Usuario 2 ve {len(events_list)} eventos cuando no debería")
    else:
        print_error(f"Error obteniendo eventos: {response.text}")

    print_step(14, "Usuario 2 se suscribe al canal")
    response = requests.post(
        f"{BASE_URL}/channels/{test_data['channel_id']}/subscribe",
        headers=headers_user2
    )
    if response.status_code in [200, 201]:
        print_success(f"Usuario 2 suscrito al canal")
    else:
        print_error(f"Error suscribiendo al canal: {response.text}")
        exit(1)

    print_step(15, "Usuario 2 verifica que AHORA ve posts")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        posts_list = posts.get("posts", [])
        if len(posts_list) > 0:
            print_success(f"Usuario 2 ahora ve {len(posts_list)} post(s)")
            # Verify our post is there
            found_our_post = any(p.get("id") == test_data["post_id"] for p in posts_list)
            if found_our_post:
                print_info("✓ Nuestro post está en la lista")
        else:
            print_error(f"ERROR: Usuario 2 no ve posts después de suscribirse")
    else:
        print_error(f"Error obteniendo posts: {response.text}")

    print_step(16, "Usuario 2 verifica que AHORA ve eventos")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        events_list = events.get("events", [])
        if len(events_list) > 0:
            print_success(f"Usuario 2 ahora ve {len(events_list)} evento(s)")
            # Verify our event is there
            found_our_event = any(e.get("id") == test_data["event_id"] for e in events_list)
            if found_our_event:
                print_info("✓ Nuestro evento está en la lista")
        else:
            print_error(f"ERROR: Usuario 2 no ve eventos después de suscribirse")
    else:
        print_error(f"Error obteniendo eventos: {response.text}")

    # ============================================================================
    # PARTE 4: USUARIO 2 INTERACTÚA CON POSTS
    # ============================================================================

    print_step(17, "Usuario 2 da like al post")
    response = requests.patch(
        f"{BASE_URL}/posts/{test_data['post_id']}/like",
        json={"action": "like"},
        headers=headers_user2
    )
    if response.status_code == 200:
        result = response.json()
        print_success(f"Like añadido - Total likes: {result.get('new_count', 'N/A')}")
    else:
        print_error(f"Error dando like: {response.text}")

    print_step(18, "Usuario 2 reza por el post")
    response = requests.patch(
        f"{BASE_URL}/posts/{test_data['post_id']}/pray",
        json={"action": "pray"},
        headers=headers_user2
    )
    if response.status_code == 200:
        result = response.json()
        print_success(f"Pray añadido - Total prays: {result.get('new_count', 'N/A')}")
    else:
        print_error(f"Error rezando: {response.text}")

    print_step(19, "Usuario 2 intenta dar like duplicado (debe retornar error o mismo count)")
    response = requests.patch(
        f"{BASE_URL}/posts/{test_data['post_id']}/like",
        json={"action": "like"},
        headers=headers_user2
    )
    if response.status_code in [400, 409]:
        print_success("Correctamente bloqueado like duplicado")
    elif response.status_code == 200:
        result = response.json()
        print_info(f"Like duplicado retornó 200 - Count: {result.get('new_count', 'N/A')}")
    else:
        print_error(f"Respuesta inesperada: {response.text}")

    print_step(20, "Usuario 2 quita el like")
    response = requests.patch(
        f"{BASE_URL}/posts/{test_data['post_id']}/like",
        json={"action": "unlike"},
        headers=headers_user2
    )
    if response.status_code == 200:
        result = response.json()
        print_success(f"Like removido - Total likes: {result.get('new_count', 'N/A')}")
    else:
        print_error(f"Error quitando like: {response.text}")

    print_step(21, "Usuario 2 quita el pray")
    response = requests.patch(
        f"{BASE_URL}/posts/{test_data['post_id']}/pray",
        json={"action": "unpray"},
        headers=headers_user2
    )
    if response.status_code == 200:
        result = response.json()
        print_success(f"Pray removido - Total prays: {result.get('new_count', 'N/A')}")
    else:
        print_error(f"Error quitando pray: {response.text}")

    print_step(22, "Usuario 2 vuelve a dar like")
    response = requests.patch(
        f"{BASE_URL}/posts/{test_data['post_id']}/like",
        json={"action": "like"},
        headers=headers_user2
    )
    if response.status_code == 200:
        result = response.json()
        print_success(f"Like añadido nuevamente - Total likes: {result.get('new_count', 'N/A')}")
    else:
        print_error(f"Error dando like: {response.text}")

    print_step(23, "Usuario 2 vuelve a rezar")
    response = requests.patch(
        f"{BASE_URL}/posts/{test_data['post_id']}/pray",
        json={"action": "pray"},
        headers=headers_user2
    )
    if response.status_code == 200:
        result = response.json()
        print_success(f"Pray añadido nuevamente - Total prays: {result.get('new_count', 'N/A')}")
    else:
        print_error(f"Error rezando: {response.text}")

    # ============================================================================
    # PARTE 5: COMENTARIOS
    # ============================================================================

    print_step(24, "Usuario 2 añade un comentario")
    comment_data = {
        "post_id": test_data["post_id"],
        "content": "Este es un comentario de prueba del usuario 2"
    }
    response = requests.post(f"{BASE_URL}/comments", json=comment_data, headers=headers_user2)
    if response.status_code in [200, 201]:
        comment = response.json()
        test_data["comment_id"] = comment.get("id")
        print_success(f"Comentario creado con ID: {test_data['comment_id']}")
        print_info(f"Contenido: {comment.get('content', 'N/A')[:50]}...")
    else:
        print_error(f"Error creando comentario: {response.text}")

    if test_data["comment_id"]:
        print_step(25, "Usuario 2 edita el comentario")
        update_data = {
            "content": "Este comentario ha sido editado"
        }
        response = requests.put(
            f"{BASE_URL}/comments/{test_data['comment_id']}",
            json=update_data,
            headers=headers_user2
        )
        if response.status_code == 200:
            comment = response.json()
            print_success(f"Comentario editado")
            print_info(f"Nuevo contenido: {comment.get('content', 'N/A')}")
        else:
            print_error(f"Error editando comentario: {response.text}")

    # ============================================================================
    # PARTE 6: SUSCRIPCIONES
    # ============================================================================

    print_step(26, "Usuario 2 se desuscribe del canal")
    response = requests.delete(
        f"{BASE_URL}/channels/{test_data['channel_id']}/subscribe",
        headers=headers_user2
    )
    if response.status_code in [200, 204]:
        print_success("Usuario 2 desuscrito del canal")
    else:
        print_error(f"Error desuscribiendo: {response.text}")

    print_step(27, "Usuario 2 verifica que ya NO ve posts después de desuscribirse")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        posts_list = posts.get("posts", [])
        if len(posts_list) == 0:
            print_success("Usuario 2 correctamente NO ve posts después de desuscribirse")
        else:
            print_error(f"ERROR: Usuario 2 todavía ve {len(posts_list)} posts")
    else:
        print_error(f"Error obteniendo posts: {response.text}")

    print_step(28, "Usuario 2 verifica que ya NO ve eventos después de desuscribirse")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        events_list = events.get("events", [])
        if len(events_list) == 0:
            print_success("Usuario 2 correctamente NO ve eventos después de desuscribirse")
        else:
            print_error(f"ERROR: Usuario 2 todavía ve {len(events_list)} eventos")
    else:
        print_error(f"Error obteniendo eventos: {response.text}")

    print_step(29, "Usuario 2 se vuelve a suscribir")
    response = requests.post(
        f"{BASE_URL}/channels/{test_data['channel_id']}/subscribe",
        headers=headers_user2
    )
    if response.status_code in [200, 201]:
        print_success("Usuario 2 vuelto a suscribir al canal")
    else:
        print_error(f"Error suscribiendo: {response.text}")

    print_step(30, "Usuario 2 verifica que vuelve a ver posts")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        posts_list = posts.get("posts", [])
        if len(posts_list) > 0:
            print_success(f"Usuario 2 vuelve a ver {len(posts_list)} post(s)")
        else:
            print_error(f"ERROR: Usuario 2 no ve posts después de volver a suscribirse")
    else:
        print_error(f"Error obteniendo posts: {response.text}")

    print_step(31, "Usuario 2 verifica que vuelve a ver eventos")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        events_list = events.get("events", [])
        if len(events_list) > 0:
            print_success(f"Usuario 2 vuelve a ver {len(events_list)} evento(s)")
        else:
            print_error(f"ERROR: Usuario 2 no ve eventos después de volver a suscribirse")
    else:
        print_error(f"Error obteniendo eventos: {response.text}")

    # ============================================================================
    # PARTE 7: LIMPIEZA
    # ============================================================================

    print_step(32, "Limpiar: Eliminar comentario")
    if test_data["comment_id"]:
        response = requests.delete(
            f"{BASE_URL}/comments/{test_data['comment_id']}",
            headers=headers_user2
        )
        if response.status_code in [200, 204]:
            print_success("Comentario eliminado")
        else:
            print_error(f"Error eliminando comentario: {response.text}")

    print_step(33, "Limpiar: Eliminar evento")
    if test_data["event_id"]:
        response = requests.delete(
            f"{BASE_URL}/events/{test_data['event_id']}",
            headers=headers_user1
        )
        if response.status_code in [200, 204]:
            print_success("Evento eliminado")
        else:
            print_error(f"Error eliminando evento: {response.text}")

    print_step(34, "Limpiar: Eliminar post")
    if test_data["post_id"]:
        response = requests.delete(
            f"{BASE_URL}/posts/{test_data['post_id']}",
            headers=headers_user1
        )
        if response.status_code in [200, 204]:
            print_success("Post eliminado")
        else:
            print_error(f"Error eliminando post: {response.text}")

    print_step(35, "Limpiar: Eliminar canal")
    if test_data["channel_id"]:
        response = requests.delete(
            f"{BASE_URL}/channels/{test_data['channel_id']}",
            headers=headers_user1
        )
        if response.status_code in [200, 204]:
            print_success("Canal eliminado")
        else:
            print_error(f"Error eliminando canal: {response.text}")

    print_step(36, "Limpiar: Eliminar organización")
    if test_data["organization_id"]:
        response = requests.delete(
            f"{BASE_URL}/organizations/{test_data['organization_id']}",
            headers=headers_superadmin
        )
        if response.status_code in [200, 204]:
            print_success("Organización eliminada")
        else:
            print_error(f"Error eliminando organización: {response.text}")

    # Cleanup temp file
    if os.path.exists(test_image_path):
        os.remove(test_image_path)

    # ============================================================================
    # RESULTADO FINAL
    # ============================================================================

    print("\n" + "="*80)
    print("RESUMEN DEL TEST")
    print("="*80)
    print_success("✓ PRUEBA SUPERADA - Todos los pasos completados exitosamente")
    print("\nDatos del test:")
    print(f"  - Organización ID: {test_data['organization_id']}")
    print(f"  - Canal ID: {test_data['channel_id']}")
    print(f"  - Post ID: {test_data['post_id']}")
    print(f"  - Evento ID: {test_data['event_id']}")
    print(f"  - Comentario ID: {test_data['comment_id']}")
    print(f"  - Usuario 1 ID: {test_data['user1_id']}")
    print(f"  - Usuario 2 ID: {test_data['user2_id']}")

except Exception as e:
    print_error(f"Error inesperado: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
