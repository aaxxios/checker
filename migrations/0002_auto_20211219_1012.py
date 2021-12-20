# Generated by Django 3.2.8 on 2021-12-19 09:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('checker', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProtectedResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(blank=True, max_length=2048)),
                ('file', models.FileField(blank=True, upload_to='userfiles/%Y/%m/%d')),
                ('type', models.CharField(choices=[('URL', 'Website address'), ('PDF', 'PDF file'), ('DOC', 'Word document, old format'), ('DOCX', 'Word document, new format'), ('PPTX', 'Powerpoint presentation'), ('TXT', 'Standard text file')], default='URL', max_length=4)),
                ('status', models.CharField(choices=[('A', 'Active'), ('N', 'Newly placed order'), ('S', 'Being scanned'), ('F', 'Last scan failed'), ('P', 'Awaiting payment'), ('I', 'Inactive')], default='A', max_length=1)),
                ('scan_frequency', models.PositiveIntegerField(choices=[(86400, 'Daily'), (604800, 'Weekly'), (2592000, 'Monthly')], default=604800)),
                ('next_scan', models.DateTimeField()),
                ('original_filename', models.CharField(blank=True, max_length=260, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='scanlog',
            name='protected_resource',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='checker.protectedresource'),
        ),
    ]