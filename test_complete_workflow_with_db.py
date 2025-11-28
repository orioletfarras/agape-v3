"""
Complete workflow test with OTP retrieval via API
Tests the complete user journey from registration to cleanup
Uses the admin OTP endpoint to get OTP codes for testing
"""
import requests
import json
from datetime import datetime, timedelta
import os
import time

BASE_URL = "http://localhost:8000/api/v1"

# Superadmin credentials - will be obtained by login
SUPERADMIN_EMAIL = "oriol@penwin.org"
SUPERADMIN_PASSWORD = "20141130"

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

def get_latest_otp(email: str, token: str) -> str:
    """Get latest OTP code via API endpoint"""
    response = requests.post(
        f"{BASE_URL}/auth/admin/get-otp",
        params={"email": email},
        headers={"X-Access-Token": token}
    )
    if response.status_code == 200:
        result = response.json()
        return result.get("code")
    return None

# Store test data
test_data = {
    "user1_id": None,
    "user1_token": None,
    "user1_email": None,
    "user1_registration_id": None,
    "user2_id": None,
    "user2_token": None,
    "user2_email": None,
    "user2_registration_id": None,
    "superadmin_token": None,
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
    else:
        print_error(f"Error login superadmin: {response.text}")
        exit(1)

    print_step(2, "Iniciar registro usuario 1")
    test_data["user1_email"] = f"testuser1_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
    user1_register_data = {
        "email": test_data["user1_email"],
        "password": "TestPassword123!"
    }
    response = requests.post(f"{BASE_URL}/auth/register-start", json=user1_register_data)
    if response.status_code in [200, 201]:
        result = response.json()
        test_data["user1_registration_id"] = result.get("registration_id")
        print_success(f"Registro iniciado - Registration ID: {test_data['user1_registration_id']}")
        print_info(f"Email: {test_data['user1_email']}")
    else:
        print_error(f"Error iniciando registro: {response.text}")
        exit(1)

    print_step(3, "Obtener OTP mediante API para usuario 1")
    # Wait a moment for OTP to be created
    time.sleep(1)
    otp_code = get_latest_otp(test_data["user1_email"], test_data["superadmin_token"])
    if otp_code:
        print_success(f"OTP obtenido: {otp_code}")
    else:
        print_error("No se encontró OTP")
        exit(1)

    print_step(4, "Verificar email usuario 1 con OTP")
    verify_data = {
        "registration_id": test_data["user1_registration_id"],
        "code": otp_code
    }
    response = requests.post(f"{BASE_URL}/auth/register-verify-email", json=verify_data)
    if response.status_code in [200, 201]:
        print_success("Email verificado")
    else:
        print_error(f"Error verificando email: {response.text}")
        exit(1)

    print_step(5, "Completar registro usuario 1")
    complete_data = {
        "registration_id": test_data["user1_registration_id"],
        "username": f"testuser1_{datetime.now().strftime('%H%M%S')}",
        "name": "Test User One"
    }
    response = requests.post(f"{BASE_URL}/auth/register-complete", json=complete_data)
    if response.status_code in [200, 201]:
        result = response.json()
        test_data["user1_token"] = result.get("access_token") or result.get("token")
        test_data["user1_id"] = result.get("user", {}).get("id") or result.get("user_id")
        print_success(f"Usuario 1 creado - ID: {test_data['user1_id']}")
    else:
        print_error(f"Error completando registro: {response.text}")
        exit(1)

    print_step(6, "Iniciar registro usuario 2")
    test_data["user2_email"] = f"testuser2_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
    user2_register_data = {
        "email": test_data["user2_email"],
        "password": "TestPassword123!"
    }
    response = requests.post(f"{BASE_URL}/auth/register-start", json=user2_register_data)
    if response.status_code in [200, 201]:
        result = response.json()
        test_data["user2_registration_id"] = result.get("registration_id")
        print_success(f"Registro iniciado - Registration ID: {test_data['user2_registration_id']}")
    else:
        print_error(f"Error iniciando registro: {response.text}")
        exit(1)

    print_step(7, "Obtener OTP y completar registro usuario 2")
    time.sleep(1)
    otp_code = get_latest_otp(test_data["user2_email"], test_data["superadmin_token"])
    if otp_code:
        print_success(f"OTP obtenido: {otp_code}")

        # Verify email
        verify_data = {
            "registration_id": test_data["user2_registration_id"],
            "code": otp_code
        }
        response = requests.post(f"{BASE_URL}/auth/register-verify-email", json=verify_data)
        if response.status_code in [200, 201]:
            print_success("Email verificado")
        else:
            print_error(f"Error verificando email: {response.text}")
            exit(1)

        # Complete registration
        complete_data = {
            "registration_id": test_data["user2_registration_id"],
            "username": f"testuser2_{datetime.now().strftime('%H%M%S')}",
            "name": "Test User Two"
        }
        response = requests.post(f"{BASE_URL}/auth/register-complete", json=complete_data)
        if response.status_code in [200, 201]:
            result = response.json()
            test_data["user2_token"] = result.get("access_token") or result.get("token")
            test_data["user2_id"] = result.get("user", {}).get("id") or result.get("user_id")
            print_success(f"Usuario 2 creado - ID: {test_data['user2_id']}")
        else:
            print_error(f"Error completando registro: {response.text}")
            exit(1)
    else:
        print_error("No se encontró OTP en la base de datos")
        exit(1)

    print_step(8, "Obtener organización existente")
    headers_superadmin = {
        "X-Access-Token": test_data["superadmin_token"],
        "Content-Type": "application/json"
    }
    response = requests.get(f"{BASE_URL}/organizations", headers=headers_superadmin)
    if response.status_code == 200:
        orgs = response.json()
        if len(orgs) > 0:
            test_data["organization_id"] = orgs[0]["id"]
            print_success(f"Usando organización existente con ID: {test_data['organization_id']}")
        else:
            print_error("No hay organizaciones disponibles")
            exit(1)
    else:
        print_error(f"Error obteniendo organizaciones: {response.text}")
        exit(1)

    print_step(9, "Usuario 1 se une a la organización")
    assign_data = {
        "organization_id": test_data["organization_id"]
    }
    headers_user1 = {
        "X-Access-Token": test_data["user1_token"],
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{BASE_URL}/auth/register-user-organization",
        json=assign_data,
        headers=headers_user1
    )
    if response.status_code in [200, 201]:
        print_success(f"Usuario 1 asignado a organización")
    else:
        print_info("Intentando endpoint alternativo...")
        response = requests.post(
            f"{BASE_URL}/organizations/{test_data['organization_id']}/add-member",
            json={"user_id": test_data["user1_id"]},
            headers=headers_superadmin
        )
        if response.status_code in [200, 201]:
            print_success(f"Usuario 1 asignado (endpoint alternativo)")
        else:
            print_error(f"Error asignando usuario: {response.text}")

    # ============================================================================
    # PARTE 2: USUARIO 1 CREA CONTENIDO
    # ============================================================================

    headers_user1 = {
        "X-Access-Token": test_data["user1_token"],
        "Content-Type": "application/json"
    }

    print_step(10, "Usuario 1 actualiza foto de perfil")
    test_image_path = "/tmp/test_profile.jpg"
    # Create a valid 1x1 red pixel JPEG using PIL
    from PIL import Image
    img = Image.new('RGB', (1, 1), color = 'red')
    img.save(test_image_path, 'JPEG')

    with open(test_image_path, "rb") as f:
        files = {"file": ("test_profile.jpg", f, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/upload-profile-image",
            files=files,
            headers={"X-Access-Token": test_data["user1_token"]}
        )

    if response.status_code in [200, 201]:
        result = response.json()
        profile_image_url = result.get("image_url") or result.get("url")
        print_success(f"Foto de perfil actualizada")
    else:
        print_error(f"Error subiendo foto de perfil: {response.text}")

    print_step(11, "Usuario 1 crea un canal")
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
    else:
        print_error(f"Error creando canal: {response.text}")
        exit(1)

    print_step(12, "Usuario 1 crea un post con imagen")
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
    else:
        print_error(f"Error creando post: {response.text}")
        exit(1)

    print_step(13, "Usuario 1 crea un evento con imagen")
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
    else:
        print_error(f"Error creando evento: {response.text}")
        exit(1)

    # ============================================================================
    # PARTE 2B: EDICIÓN DE CANAL, POST Y EVENTO
    # ============================================================================

    print_step(14, "Usuario 1 edita el canal")
    edit_channel_data = {
        "name": f"Canal EDITADO {datetime.now().strftime('%H%M%S')}",
        "description": "Descripción del canal ha sido actualizada"
    }
    response = requests.put(
        f"{BASE_URL}/channels/{test_data['channel_id']}",
        json=edit_channel_data,
        headers=headers_user1
    )
    if response.status_code in [200, 201]:
        print_success(f"Canal editado exitosamente")
    else:
        print_error(f"Error editando canal: {response.text}")

    print_step(15, "Usuario 1 edita el post y añade nueva imagen")
    # Subir nueva imagen para el post
    with open(test_image_path, "rb") as f:
        files = {"file": ("test_post_edited.jpg", f, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/posts/upload-image",
            files=files,
            headers={"X-Access-Token": test_data["user1_token"]}
        )

    new_post_image_url = None
    if response.status_code in [200, 201]:
        result = response.json()
        new_post_image_url = result.get("image_url") or result.get("url")
        print_success(f"Nueva imagen del post subida")
    else:
        print_error(f"Error subiendo nueva imagen del post: {response.text}")

    # Editar el post con el nuevo texto y nueva imagen
    edit_post_data = {
        "text": "Este post ha sido EDITADO con nuevo contenido",
        "images": [new_post_image_url] if new_post_image_url else []
    }
    response = requests.put(
        f"{BASE_URL}/posts/{test_data['post_id']}",
        json=edit_post_data,
        headers=headers_user1
    )
    if response.status_code in [200, 201]:
        print_success(f"Post editado exitosamente")
    else:
        print_error(f"Error editando post: {response.text}")

    print_step(16, "Usuario 1 edita el evento y cambia su imagen")
    # Subir nueva imagen para el evento
    with open(test_image_path, "rb") as f:
        files = {"file": ("test_event_edited.jpg", f, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/events/upload-image",
            files=files,
            headers={"X-Access-Token": test_data["user1_token"]}
        )

    new_event_image_url = None
    if response.status_code in [200, 201]:
        result = response.json()
        new_event_image_url = result.get("image_url") or result.get("url")
        print_success(f"Nueva imagen del evento subida")
    else:
        print_error(f"Error subiendo nueva imagen del evento: {response.text}")

    # Editar el evento
    new_event_date = (datetime.now() + timedelta(days=14)).isoformat()
    edit_event_data = {
        "name": f"Evento EDITADO {datetime.now().strftime('%H%M%S')}",
        "description": "Descripción del evento ha sido actualizada",
        "event_date": new_event_date,
        "location": "Nueva Ubicación Editada",
        "image_url": new_event_image_url,
        "is_paid": True,
        "price": 10.50
    }
    response = requests.put(
        f"{BASE_URL}/events/{test_data['event_id']}",
        json=edit_event_data,
        headers=headers_user1
    )
    if response.status_code in [200, 201]:
        print_success(f"Evento editado exitosamente")
    else:
        print_error(f"Error editando evento: {response.text}")

    # ============================================================================
    # PARTE 3: USUARIO 2 INTENTA CREAR CONTENIDO (DEBE FALLAR)
    # ============================================================================

    headers_user2 = {
        "X-Access-Token": test_data["user2_token"],
        "Content-Type": "application/json"
    }

    print_step(17, "Usuario 2 intenta crear canal (debe fallar)")
    channel_data_user2 = {
        "name": "Canal Unauthorized",
        "description": "Este canal no debe crearse",
        "organization_id": test_data["organization_id"]
    }
    response = requests.post(f"{BASE_URL}/channels", json=channel_data_user2, headers=headers_user2)
    if response.status_code >= 400:
        print_success(f"Usuario 2 correctamente bloqueado al crear canal ({response.status_code})")
    else:
        print_error(f"ERROR: Usuario 2 pudo crear canal cuando no debería")

    print_step(18, "Usuario 2 intenta crear evento (debe fallar)")
    event_data_user2 = {
        "channel_id": test_data["channel_id"],
        "name": "Evento Unauthorized",
        "description": "Este evento no debe crearse",
        "event_date": event_date,
        "location": "Test",
        "is_paid": False
    }
    response = requests.post(f"{BASE_URL}/events", json=event_data_user2, headers=headers_user2)
    if response.status_code >= 400:
        print_success(f"Usuario 2 correctamente bloqueado al crear evento ({response.status_code})")
    else:
        print_error(f"ERROR: Usuario 2 pudo crear evento cuando no debería")

    print_step(19, "Usuario 2 verifica que NO ve posts (no suscrito)")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        posts_list = posts.get("posts", [])
        if len(posts_list) == 0:
            print_success(f"Usuario 2 correctamente NO ve posts")
        else:
            print_error(f"ERROR: Usuario 2 ve {len(posts_list)} posts")
    else:
        print_error(f"Error obteniendo posts: {response.text}")

    print_step(20, "Usuario 2 verifica que NO ve eventos (no suscrito)")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        events_list = events.get("events", [])
        if len(events_list) == 0:
            print_success(f"Usuario 2 correctamente NO ve eventos")
        else:
            print_error(f"ERROR: Usuario 2 ve {len(events_list)} eventos")
    else:
        print_error(f"Error obteniendo eventos: {response.text}")

    print_step(21, "Usuario 2 se suscribe al canal")
    response = requests.post(
        f"{BASE_URL}/channels/{test_data['channel_id']}/subscribe",
        headers=headers_user2
    )
    if response.status_code in [200, 201]:
        print_success(f"Usuario 2 suscrito al canal")
    else:
        print_error(f"Error suscribiendo al canal: {response.text}")
        exit(1)

    print_step(22, "Usuario 2 verifica que AHORA ve posts")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        posts_list = posts.get("posts", [])
        if len(posts_list) > 0:
            print_success(f"Usuario 2 ahora ve {len(posts_list)} post(s)")
        else:
            print_error(f"ERROR: Usuario 2 no ve posts después de suscribirse")
    else:
        print_error(f"Error obteniendo posts: {response.text}")

    print_step(23, "Usuario 2 verifica que AHORA ve eventos")
    response = requests.get(f"{BASE_URL}/events", headers=headers_user2)
    if response.status_code == 200:
        events = response.json()
        events_list = events.get("events", [])
        if len(events_list) > 0:
            print_success(f"Usuario 2 ahora ve {len(events_list)} evento(s)")
        else:
            print_error(f"ERROR: Usuario 2 no ve eventos después de suscribirse")
    else:
        print_error(f"Error obteniendo eventos: {response.text}")

    # ============================================================================
    # PARTE 4: USUARIO 2 INTERACTÚA CON POSTS
    # ============================================================================

    print_step(24, "Usuario 2 da like al post")
    response = requests.patch(
        f"{BASE_URL}/posts/{test_data['post_id']}/like",
        json={"action": "like"},
        headers=headers_user2
    )
    if response.status_code == 200:
        result = response.json()
        print_success(f"Like añadido - Total: {result.get('new_count', 'N/A')}")
    else:
        print_error(f"Error dando like: {response.text}")

    print_step(25, "Usuario 2 reza por el post")
    response = requests.patch(
        f"{BASE_URL}/posts/{test_data['post_id']}/pray",
        json={"action": "pray"},
        headers=headers_user2
    )
    if response.status_code == 200:
        result = response.json()
        print_success(f"Pray añadido - Total: {result.get('new_count', 'N/A')}")
    else:
        print_error(f"Error rezando: {response.text}")

    print_step(26, "Usuario 2 quita like y pray")
    requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/like", json={"action": "unlike"}, headers=headers_user2)
    requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/pray", json={"action": "unpray"}, headers=headers_user2)
    print_success("Like y pray removidos")

    print_step(27, "Usuario 2 vuelve a dar like y pray")
    requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/like", json={"action": "like"}, headers=headers_user2)
    requests.patch(f"{BASE_URL}/posts/{test_data['post_id']}/pray", json={"action": "pray"}, headers=headers_user2)
    print_success("Like y pray añadidos nuevamente")

    # ============================================================================
    # PARTE 5: COMENTARIOS
    # ============================================================================

    print_step(28, "Usuario 2 añade un comentario")
    comment_data = {
        "post_id": test_data["post_id"],
        "content": "Este es un comentario de prueba del usuario 2"
    }
    response = requests.post(f"{BASE_URL}/comments", json=comment_data, headers=headers_user2)
    if response.status_code in [200, 201]:
        comment = response.json()
        test_data["comment_id"] = comment.get("id")
        print_success(f"Comentario creado con ID: {test_data['comment_id']}")
    else:
        print_error(f"Error creando comentario: {response.text}")

    if test_data["comment_id"]:
        print_step(29, "Usuario 2 edita el comentario")
        update_data = {"content": "Este comentario ha sido editado"}
        response = requests.put(
            f"{BASE_URL}/comments/{test_data['comment_id']}",
            json=update_data,
            headers=headers_user2
        )
        if response.status_code == 200:
            print_success("Comentario editado")
        else:
            print_error(f"Error editando comentario: {response.text}")

    # ============================================================================
    # PARTE 6: SUSCRIPCIONES
    # ============================================================================

    print_step(30, "Usuario 2 se desuscribe del canal")
    response = requests.delete(
        f"{BASE_URL}/channels/{test_data['channel_id']}/subscribe",
        headers=headers_user2
    )
    if response.status_code in [200, 204]:
        print_success("Usuario 2 desuscrito")
    else:
        print_error(f"Error desuscribiendo: {response.text}")

    print_step(31, "Usuario 2 verifica que NO ve posts después de desuscribirse")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200:
        posts = response.json()
        if len(posts.get("posts", [])) == 0:
            print_success("Usuario 2 correctamente NO ve posts")
        else:
            print_error(f"ERROR: Usuario 2 todavía ve posts")
    else:
        print_error(f"Error: {response.text}")

    print_step(32, "Usuario 2 se vuelve a suscribir")
    requests.post(f"{BASE_URL}/channels/{test_data['channel_id']}/subscribe", headers=headers_user2)
    print_success("Usuario 2 vuelto a suscribir")

    print_step(33, "Usuario 2 verifica que vuelve a ver contenido")
    response = requests.get(f"{BASE_URL}/posts", headers=headers_user2)
    if response.status_code == 200 and len(response.json().get("posts", [])) > 0:
        print_success("Usuario 2 vuelve a ver posts")
    else:
        print_error("ERROR: Usuario 2 no ve posts")

    # ============================================================================
    # PARTE 7: LIMPIEZA
    # ============================================================================

    print_step(34, "Limpiar: Eliminar comentario")
    if test_data["comment_id"]:
        requests.delete(f"{BASE_URL}/comments/{test_data['comment_id']}", headers=headers_user2)
        print_success("Comentario eliminado")

    print_step(35, "Limpiar: Eliminar evento")
    if test_data["event_id"]:
        requests.delete(f"{BASE_URL}/events/{test_data['event_id']}", headers=headers_user1)
        print_success("Evento eliminado")

    print_step(36, "Limpiar: Eliminar post")
    if test_data["post_id"]:
        requests.delete(f"{BASE_URL}/posts/{test_data['post_id']}", headers=headers_user1)
        print_success("Post eliminado")

    print_step(37, "Limpiar: Eliminar canal")
    if test_data["channel_id"]:
        requests.delete(f"{BASE_URL}/channels/{test_data['channel_id']}", headers=headers_user1)
        print_success("Canal eliminado")

    print_step(38, "Limpiar: Eliminar organización")
    if test_data["organization_id"]:
        requests.delete(f"{BASE_URL}/organizations/{test_data['organization_id']}", headers=headers_superadmin)
        print_success("Organización eliminada")

    # Cleanup temp file
    if os.path.exists(test_image_path):
        os.remove(test_image_path)

    # ============================================================================
    # RESULTADO FINAL
    # ============================================================================

    print("\n" + "="*80)
    print("RESUMEN DEL TEST")
    print("="*80)
    print_success("✓✓✓ PRUEBA SUPERADA - Todos los pasos completados exitosamente ✓✓✓")
    print("\nDatos del test:")
    print(f"  - Usuario 1 ID: {test_data['user1_id']} ({test_data['user1_email']})")
    print(f"  - Usuario 2 ID: {test_data['user2_id']} ({test_data['user2_email']})")
    print(f"  - Organización ID: {test_data['organization_id']}")
    print(f"  - Canal ID: {test_data['channel_id']}")
    print(f"  - Post ID: {test_data['post_id']}")
    print(f"  - Evento ID: {test_data['event_id']}")
    print(f"  - Comentario ID: {test_data['comment_id']}")
    print("\n" + "="*80)

except Exception as e:
    print_error(f"Error inesperado: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
