import pgvector.django.vector
from django.db import migrations, models
from pgvector.django import VectorExtension


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        VectorExtension(),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('source', models.CharField(blank=True, max_length=255, null=True)),
                ('embedding', pgvector.django.vector.VectorField(dimensions=384)),
            ],
        ),
        migrations.CreateModel(
            name='QueryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.TextField()),
                ('answer', models.TextField()),
                ('cache_hit', models.BooleanField(default=False)),
                ('cache_type', models.CharField(blank=True, max_length=20, null=True)),
                ('response_time_ms', models.IntegerField()),
                ('embedding', pgvector.django.vector.VectorField(dimensions=384)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
