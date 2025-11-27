"""
Seed script to populate the database with mock data for testing

Creates:
- 5 users (with real passwords: "password123")
- 3 organizations (parishes)
- 3 channels (one per organization)
- Channel subscriptions
- 10 posts
- 3 events
- Some comments and interactions

Usage:
    python seed_data.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from passlib.context import CryptContext

from app.infrastructure.database import get_db, db
from app.infrastructure.database.models import (
    User,
    Organization,
    Parish,
    UserOrganization,
    Channel,
    ChannelSubscription,
    ChannelAdmin,
    Post,
    PostLike,
    PostPray,
    Comment,
    Event,
    EventRegistration,
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def clear_data(session):
    """Clear existing data (optional)"""
    print("⚠️  Clearing existing data...")

    # Delete in reverse order of dependencies
    await session.execute("SET FOREIGN_KEY_CHECKS = 0")

    tables = [
        "comment_likes",
        "comments",
        "post_favorites",
        "post_prays",
        "post_likes",
        "hidden_posts",
        "posts",
        "event_alerts",
        "discount_codes",
        "event_transactions",
        "event_registrations",
        "events",
        "channel_alerts",
        "hidden_channels",
        "channel_settings",
        "channel_admins",
        "channel_subscriptions",
        "channels",
        "user_organizations",
        "parishes",
        "organizations",
        "users",
    ]

    for table in tables:
        try:
            await session.execute(f"DELETE FROM {table}")
            print(f"  Cleared {table}")
        except Exception as e:
            print(f"  ⚠️  Could not clear {table}: {e}")

    await session.execute("SET FOREIGN_KEY_CHECKS = 1")
    await session.commit()
    print("✅ Data cleared\n")


async def seed_data():
    """Seed the database with mock data"""

    # Initialize database connection
    db.initialize()

    async for session in get_db():
        # Optional: Clear existing data
        # Uncomment if you want to start fresh
        # await clear_data(session)

        print("🌱 Seeding database with mock data...\n")

        # 1. CREATE ORGANIZATIONS (PARISHES)
        print("📍 Creating organizations...")

        org1 = Organization(
            name="Parroquia San Pedro",
            type="parish",
            address="Calle Mayor 123, Madrid",
            city="Madrid",
            country="España",
            phone="+34 91 123 4567",
            email="info@sanpedro.es",
            created_at=datetime.utcnow(),
        )
        session.add(org1)

        org2 = Organization(
            name="Parroquia Santa María",
            type="parish",
            address="Plaza de la Iglesia 5, Barcelona",
            city="Barcelona",
            country="España",
            phone="+34 93 987 6543",
            email="contacto@santamaria.es",
            created_at=datetime.utcnow(),
        )
        session.add(org2)

        org3 = Organization(
            name="Parroquia San José",
            type="parish",
            address="Avenida Principal 89, Valencia",
            city="Valencia",
            country="España",
            phone="+34 96 555 1234",
            email="hola@sanjose.es",
            created_at=datetime.utcnow(),
        )
        session.add(org3)

        await session.flush()  # Get IDs
        print(f"  ✅ Created 3 organizations (IDs: {org1.id}, {org2.id}, {org3.id})")

        # 2. CREATE USERS
        print("\n👥 Creating users...")

        users_data = [
            {
                "email": "juan@example.com",
                "username": "juan_garcia",
                "nombre": "Juan",
                "apellidos": "García López",
                "bio": "Fiel católico, me gusta la oración y el servicio comunitario",
                "genero": "male",
                "primary_organization_id": org1.id,
            },
            {
                "email": "maria@example.com",
                "username": "maria_rodriguez",
                "nombre": "María",
                "apellidos": "Rodríguez Sánchez",
                "bio": "Catequista y mamá de 3 hijos",
                "genero": "female",
                "primary_organization_id": org1.id,
            },
            {
                "email": "pedro@example.com",
                "username": "pedro_martinez",
                "nombre": "Pedro",
                "apellidos": "Martínez Fernández",
                "bio": "Sacerdote de la parroquia San José",
                "genero": "male",
                "primary_organization_id": org3.id,
            },
            {
                "email": "ana@example.com",
                "username": "ana_lopez",
                "nombre": "Ana",
                "apellidos": "López Torres",
                "bio": "Voluntaria en Cáritas",
                "genero": "female",
                "primary_organization_id": org2.id,
            },
            {
                "email": "carlos@example.com",
                "username": "carlos_sanchez",
                "nombre": "Carlos",
                "apellidos": "Sánchez Ruiz",
                "bio": "Juventud cristiana",
                "genero": "male",
                "primary_organization_id": org2.id,
            },
        ]

        users = []
        for user_data in users_data:
            user = User(
                **user_data,
                password_hash=pwd_context.hash("password123"),
                is_active=True,
                is_verified=True,
                onboarding_completed=True,
                created_at=datetime.utcnow(),
            )
            session.add(user)
            users.append(user)

        await session.flush()
        print(f"  ✅ Created {len(users)} users (password: 'password123' for all)")
        for user in users:
            print(f"     - {user.username} ({user.email})")

        # 3. CREATE CHANNELS
        print("\n📺 Creating channels...")

        channel1 = Channel(
            name="Anuncios San Pedro",
            description="Canal oficial de comunicaciones de la Parroquia San Pedro",
            channel_type="official",
            organization_id=org1.id,
            created_by_user_id=users[0].id,
            is_public=True,
            is_verified=True,
            created_at=datetime.utcnow(),
        )
        session.add(channel1)

        channel2 = Channel(
            name="Santa María Noticias",
            description="Noticias y eventos de nuestra parroquia",
            channel_type="official",
            organization_id=org2.id,
            created_by_user_id=users[3].id,
            is_public=True,
            is_verified=True,
            created_at=datetime.utcnow(),
        )
        session.add(channel2)

        channel3 = Channel(
            name="Juventud San José",
            description="Canal para jóvenes de la parroquia",
            channel_type="community",
            organization_id=org3.id,
            created_by_user_id=users[2].id,
            is_public=True,
            is_verified=False,
            created_at=datetime.utcnow(),
        )
        session.add(channel3)

        await session.flush()
        print(f"  ✅ Created 3 channels")
        print(f"     - {channel1.name} (ID: {channel1.id})")
        print(f"     - {channel2.name} (ID: {channel2.id})")
        print(f"     - {channel3.name} (ID: {channel3.id})")

        # 4. CREATE CHANNEL ADMINS
        print("\n👑 Assigning channel admins...")

        admin1 = ChannelAdmin(
            channel_id=channel1.id,
            user_id=users[0].id,
            role="owner",
            created_at=datetime.utcnow(),
        )
        session.add(admin1)

        admin2 = ChannelAdmin(
            channel_id=channel2.id,
            user_id=users[3].id,
            role="owner",
            created_at=datetime.utcnow(),
        )
        session.add(admin2)

        admin3 = ChannelAdmin(
            channel_id=channel3.id,
            user_id=users[2].id,
            role="owner",
            created_at=datetime.utcnow(),
        )
        session.add(admin3)

        print("  ✅ Assigned 3 channel admins")

        # 5. CREATE CHANNEL SUBSCRIPTIONS
        print("\n✨ Creating channel subscriptions...")

        subscriptions_count = 0

        # All users subscribe to channel 1
        for user in users:
            sub = ChannelSubscription(
                channel_id=channel1.id,
                user_id=user.id,
                subscribed_at=datetime.utcnow(),
            )
            session.add(sub)
            subscriptions_count += 1

        # Users 0, 3, 4 subscribe to channel 2
        for user in [users[0], users[3], users[4]]:
            sub = ChannelSubscription(
                channel_id=channel2.id,
                user_id=user.id,
                subscribed_at=datetime.utcnow(),
            )
            session.add(sub)
            subscriptions_count += 1

        # Users 2, 4 subscribe to channel 3
        for user in [users[2], users[4]]:
            sub = ChannelSubscription(
                channel_id=channel3.id,
                user_id=user.id,
                subscribed_at=datetime.utcnow(),
            )
            session.add(sub)
            subscriptions_count += 1

        print(f"  ✅ Created {subscriptions_count} channel subscriptions")

        # 6. CREATE POSTS
        print("\n📝 Creating posts...")

        posts_data = [
            {
                "channel_id": channel1.id,
                "user_id": users[0].id,
                "content": "¡Bienvenidos al canal de la Parroquia San Pedro! Aquí compartiremos noticias, eventos y reflexiones.",
                "is_published": True,
            },
            {
                "channel_id": channel1.id,
                "user_id": users[1].id,
                "content": "Mañana tenemos la misa de 10am. ¡Los esperamos a todos! 🙏",
                "is_published": True,
            },
            {
                "channel_id": channel1.id,
                "user_id": users[0].id,
                "content": "Recordatorio: Este sábado tenemos el retiro de Adviento. Inscripciones abiertas.",
                "is_published": True,
            },
            {
                "channel_id": channel2.id,
                "user_id": users[3].id,
                "content": "Santa María les desea un feliz domingo. Que Dios los bendiga.",
                "is_published": True,
            },
            {
                "channel_id": channel2.id,
                "user_id": users[3].id,
                "content": "Estamos organizando una campaña de recogida de alimentos. ¿Quién se anima a ayudar?",
                "is_published": True,
            },
            {
                "channel_id": channel2.id,
                "user_id": users[4].id,
                "content": "Gracias a todos los que participaron en el rosario de hoy. Fue muy emotivo 🌹",
                "is_published": True,
            },
            {
                "channel_id": channel3.id,
                "user_id": users[2].id,
                "content": "Jóvenes de San José: Este viernes reunión a las 19:00. ¡No falten!",
                "is_published": True,
            },
            {
                "channel_id": channel3.id,
                "user_id": users[4].id,
                "content": "¿Alguien se apunta para ir al concierto de música cristiana el próximo mes?",
                "is_published": True,
            },
            {
                "channel_id": channel1.id,
                "user_id": users[0].id,
                "content": "Les comparto esta reflexión del día: 'Ama a tu prójimo como a ti mismo' - Marcos 12:31",
                "is_published": True,
            },
            {
                "channel_id": channel3.id,
                "user_id": users[2].id,
                "content": "Próximo retiro juvenil: 15-17 de diciembre. Más info próximamente.",
                "is_published": True,
            },
        ]

        posts = []
        for i, post_data in enumerate(posts_data):
            post = Post(
                **post_data,
                created_at=datetime.utcnow() - timedelta(days=len(posts_data) - i),
            )
            session.add(post)
            posts.append(post)

        await session.flush()
        print(f"  ✅ Created {len(posts)} posts")

        # 7. CREATE POST INTERACTIONS (LIKES & PRAYS)
        print("\n❤️ Creating post interactions...")

        interactions_count = 0

        # Post 1: Multiple likes and prays
        for user in [users[1], users[2], users[3]]:
            like = PostLike(
                post_id=posts[0].id,
                user_id=user.id,
                created_at=datetime.utcnow(),
            )
            session.add(like)
            interactions_count += 1

        for user in [users[0], users[4]]:
            pray = PostPray(
                post_id=posts[0].id,
                user_id=user.id,
                created_at=datetime.utcnow(),
            )
            session.add(pray)
            interactions_count += 1

        # Post 2: Some prays
        for user in [users[0], users[2], users[3], users[4]]:
            pray = PostPray(
                post_id=posts[1].id,
                user_id=user.id,
                created_at=datetime.utcnow(),
            )
            session.add(pray)
            interactions_count += 1

        # Post 4: Likes
        for user in [users[0], users[4]]:
            like = PostLike(
                post_id=posts[3].id,
                user_id=user.id,
                created_at=datetime.utcnow(),
            )
            session.add(like)
            interactions_count += 1

        print(f"  ✅ Created {interactions_count} post interactions")

        # 8. CREATE COMMENTS
        print("\n💬 Creating comments...")

        comments_data = [
            {
                "post_id": posts[0].id,
                "user_id": users[1].id,
                "content": "¡Qué alegría estar aquí! Bendiciones a todos.",
            },
            {
                "post_id": posts[0].id,
                "user_id": users[3].id,
                "content": "Gracias por crear este espacio de comunión.",
            },
            {
                "post_id": posts[1].id,
                "user_id": users[2].id,
                "content": "Allí estaré. Que Dios los bendiga.",
            },
            {
                "post_id": posts[4].id,
                "user_id": users[0].id,
                "content": "Me apunto para ayudar en la campaña.",
            },
            {
                "post_id": posts[7].id,
                "user_id": users[2].id,
                "content": "¡Yo voy! Me encanta la música cristiana.",
            },
        ]

        comments = []
        for comment_data in comments_data:
            comment = Comment(
                **comment_data,
                created_at=datetime.utcnow(),
            )
            session.add(comment)
            comments.append(comment)

        print(f"  ✅ Created {len(comments)} comments")

        # 9. CREATE EVENTS
        print("\n🎉 Creating events...")

        events_data = [
            {
                "channel_id": channel1.id,
                "title": "Retiro de Adviento",
                "description": "Retiro espiritual de preparación para la Navidad. Incluye reflexiones, oración y compartir comunitario.",
                "location": "Casa de Retiros San Francisco",
                "event_date": datetime.utcnow() + timedelta(days=7),
                "registration_deadline": datetime.utcnow() + timedelta(days=5),
                "max_capacity": 50,
                "price": Decimal("15.00"),
                "currency": "EUR",
                "requires_payment": True,
                "created_by_user_id": users[0].id,
            },
            {
                "channel_id": channel2.id,
                "title": "Campaña de Recogida de Alimentos",
                "description": "Evento solidario para recoger alimentos no perecederos para familias necesitadas.",
                "location": "Parroquia Santa María",
                "event_date": datetime.utcnow() + timedelta(days=3),
                "registration_deadline": datetime.utcnow() + timedelta(days=2),
                "max_capacity": 100,
                "price": Decimal("0.00"),
                "currency": "EUR",
                "requires_payment": False,
                "created_by_user_id": users[3].id,
            },
            {
                "channel_id": channel3.id,
                "title": "Retiro Juvenil de Diciembre",
                "description": "Encuentro para jóvenes con actividades, reflexión y convivencia. ¡No te lo pierdas!",
                "location": "Albergue Juvenil Monte Alto",
                "event_date": datetime.utcnow() + timedelta(days=20),
                "registration_deadline": datetime.utcnow() + timedelta(days=15),
                "max_capacity": 30,
                "price": Decimal("25.00"),
                "currency": "EUR",
                "requires_payment": True,
                "created_by_user_id": users[2].id,
            },
        ]

        events = []
        for event_data in events_data:
            event = Event(
                **event_data,
                created_at=datetime.utcnow(),
            )
            session.add(event)
            events.append(event)

        await session.flush()
        print(f"  ✅ Created {len(events)} events")

        # 10. CREATE EVENT REGISTRATIONS
        print("\n🎫 Creating event registrations...")

        registrations_data = [
            # Event 1: 3 registrations
            {"event_id": events[0].id, "user_id": users[1].id},
            {"event_id": events[0].id, "user_id": users[2].id},
            {"event_id": events[0].id, "user_id": users[3].id},
            # Event 2: 5 registrations
            {"event_id": events[1].id, "user_id": users[0].id},
            {"event_id": events[1].id, "user_id": users[1].id},
            {"event_id": events[1].id, "user_id": users[2].id},
            {"event_id": events[1].id, "user_id": users[3].id},
            {"event_id": events[1].id, "user_id": users[4].id},
            # Event 3: 2 registrations
            {"event_id": events[2].id, "user_id": users[2].id},
            {"event_id": events[2].id, "user_id": users[4].id},
        ]

        for reg_data in registrations_data:
            registration = EventRegistration(
                **reg_data,
                payment_status="completed",
                created_at=datetime.utcnow(),
            )
            session.add(registration)

        print(f"  ✅ Created {len(registrations_data)} event registrations")

        # COMMIT ALL
        await session.commit()

        print("\n" + "="*60)
        print("✅ DATABASE SEEDED SUCCESSFULLY!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   - {len(users)} users created")
        print(f"   - 3 organizations created")
        print(f"   - 3 channels created")
        print(f"   - {subscriptions_count} channel subscriptions")
        print(f"   - {len(posts)} posts created")
        print(f"   - {interactions_count} post interactions")
        print(f"   - {len(comments)} comments created")
        print(f"   - {len(events)} events created")
        print(f"   - {len(registrations_data)} event registrations")

        print("\n🔐 Test credentials:")
        print("   Email: juan@example.com")
        print("   Email: maria@example.com")
        print("   Email: pedro@example.com")
        print("   Email: ana@example.com")
        print("   Email: carlos@example.com")
        print("   Password (all): password123")

        print("\n🚀 You can now test the API with these users and data!")

        # Break after first iteration (get_db is a generator)
        break


if __name__ == "__main__":
    try:
        asyncio.run(seed_data())
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
