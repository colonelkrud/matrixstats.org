# Generated by Django 2.0.1 on 2018-01-26 14:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('room_stats', '0018_auto_20180126_1146'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_id', models.CharField(max_length=255)),
                ('proposed_category', models.CharField(blank=True, max_length=255, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sender_ip', models.GenericIPAddressField(blank=True, null=True, protocol='IPv4')),
            ],
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name_plural': 'categories'},
        ),
        migrations.AddField(
            model_name='categoryrequest',
            name='existing_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='room_stats.Category'),
        ),
    ]
