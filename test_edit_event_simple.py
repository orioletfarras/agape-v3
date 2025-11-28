#!/usr/bin/env python3
"""Test editing event image on existing event"""
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
    print("PRUEBA DE EDICIÓN DE EVENTO - IMAGEN")
    print("=" * 60)

    # PASO 1: Obtener eventos existentes
    print("\n[PASO 1] Obteniendo eventos existentes...")
    response = requests.get(f"{BASE_URL}/events", headers=HEADERS)

    if response.status_code == 200:
        events_data = response.json()
        if events_data['events']:
            event = events_data['events'][0]
            event_id = event['id']
            print(f"✓ Usando evento: {event['name']} (ID: {event_id})")
            print(f"  Imagen actual: {event.get('image_url', 'None')}")
        else:
            print("✗ No hay eventos disponibles para probar")
            return
    else:
        print(f"✗ Error obteniendo eventos: {response.text}")
        return

    # PASO 2: Subir una imagen
    print("\n[PASO 2] Subiendo imagen de prueba...")

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

    # PASO 3: Editar evento para AGREGAR/CAMBIAR la imagen
    print(f"\n[PASO 3] Editando evento {event_id} para cambiar imagen...")

    update_data = {
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

    # PASO 4: Editar evento para ELIMINAR la imagen
    print(f"\n[PASO 4] Editando evento {event_id} para ELIMINAR imagen...")

    update_data = {
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

    # PASO 5: Verificar el evento final
    print(f"\n[PASO 5] Verificando estado final del evento {event_id}...")

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
