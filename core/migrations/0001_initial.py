
from django.db import migrations


def dar_permisos_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    # Usar la base de datos correspondiente a esta migración.
    db_alias = schema_editor.connection.alias
    usuarios = User.objects.using(db_alias)

    # Buscar al usuario administrador.
    user = usuarios.filter(username='poyiyiyinis').first()

    # Si todavía no existe, no detener las migraciones.
    # El administrador podrá crearse posteriormente con createsuperuser.
    if user is None:
        return

    # Dar permisos de administrador.
    user.is_staff = True
    user.is_superuser = True
    user.save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(
            dar_permisos_admin,
            migrations.RunPython.noop
        ),
    ]
