#!/usr/bin/env python3
"""Test editing event images: add and remove"""
import requests
import json
import base64

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MyIsImV4cCI6MTc2NDg4NDY2NCwidHlwZSI6ImFjY2VzcyJ9.Ci13sFT_CwImdQLbmY2VVLpVESbNuNxOpdymkffHzdY"
HEADERS = {"X-Access-Token": TOKEN}

def create_test_image(filename="/tmp/test_event_image.png"):
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
    print("PRUEBA DE EDICIÓN DE EVENTO - AGREGAR Y ELIMINAR IMAGEN")
    print("=" * 60)

    # PASO 1: Obtener un canal para crear el evento
    print("\n[PASO 1] Obteniendo canales...")
    response = requests.get(f"{BASE_URL}/channels", headers=HEADERS)
    channels_data = response.json()
    channel_id = channels_data['channels'][0]['id']
    print(f"✓ Canal seleccionado: {channel_id}")

    # PASO 2: Crear un evento SIN imagen
    print("\n[PASO 2] Creando evento inicial sin imagen...")

    event_data = {
        "channel_id": channel_id,
        "name": "Evento de prueba sin imagen",
        "description": "Este es un evento de prueba",
        "event_date": "2025-12-31T18:00:00",
        "location": "Test Location",
        "requires_payment": False
    }
    response = requests.post(f"{BASE_URL}/events", json=event_data, headers=HEADERS)

    if response.status_code == 201:
        event = response.json()
        event_id = event['id']
        print(f"✓ Evento creado con ID: {event_id}")
        print(f"  Nombre: {event['name']}")
        print(f"  Imagen: {event.get('image_url', 'None')}")
    else:
        print(f"✗ Error al crear evento: {response.text}")
        return

    # PASO 3: Subir una imagen
    print("\n[PASO 3] Subiendo imagen de prueba...")

    create_test_image("/tmp/test_event_image1.png")

    with open("/tmp/test_event_image1.png", 'rb') as f:
        files = {'file': ('test_event_image.png', f, 'image/png')}
        response = requests.post(
            f"{BASE_URL}/events/upload-image",
            files=files,
            headers={"X-Access-Token": TOKEN}
        )

    if response.status_code == 200:
        result = response.json()
        image_url = result['image_url']
        print(f"✓ Imagen subida: {image_url}")
    else:
        print(f"✗ Error subiendo imagen: {response.text}")
        return

    # PASO 4: Editar evento para AGREGAR la imagen
    print(f"\n[PASO 4] Editando evento {event_id} para AGREGAR imagen...")

    update_data = {
        "name": "Evento editado con imagen agregada",
        "image_url": image_url
    }

    response = requests.put(
        f"{BASE_URL}/events/{event_id}",
        json=update_data,
        headers=HEADERS
    )

    if response.status_code == 200:
        updated_event = response.json()
        print(f"✓ Evento actualizado")
        print(f"  Nombre: {updated_event['name']}")
        print(f"  Imagen: {updated_event.get('image_url', 'None')}")
    else:
        print(f"✗ Error al actualizar evento: {response.text}")
        return

    # PASO 5: Editar evento para ELIMINAR la imagen
    print(f"\n[PASO 5] Editando evento {event_id} para ELIMINAR imagen...")

    update_data = {
        "name": "Evento sin imagen de nuevo",
        "image_url": None
    }

    response = requests.put(
        f"{BASE_URL}/events/{event_id}",
        json=update_data,
        headers=HEADERS
    )

    if response.status_code == 200:
        updated_event = response.json()
        print(f"✓ Evento actualizado")
        print(f"  Nombre: {updated_event['name']}")
        print(f"  Imagen: {updated_event.get('image_url', 'None')}")
    else:
        print(f"✗ Error al actualizar evento: {response.text}")
        return

    # PASO 6: Verificar el evento final
    print(f"\n[PASO 6] Verificando estado final del evento {event_id}...")

    response = requests.get(f"{BASE_URL}/events/{event_id}", headers=HEADERS)

    if response.status_code == 200:
        final_event = response.json()
        print(f"✓ Evento recuperado")
        print(f"  Nombre: {final_event['name']}")
        print(f"  Imagen: {final_event.get('image_url', 'None')}")
    else:
        print(f"✗ Error al recuperar evento: {response.text}")

    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
