# Generated by Django 3.2.8 on 2021-12-19 10:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('checker', '0003_alter_scanlog_queries'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='protectedresource',
            name='next_scan',
        ),
    ]
