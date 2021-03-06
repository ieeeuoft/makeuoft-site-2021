# Generated by Django 3.1.1 on 2020-09-13 02:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0002_auto_20200910_1606"),
    ]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="q1",
            field=models.TextField(help_text="First question?", max_length=1000),
        ),
        migrations.AlterField(
            model_name="application",
            name="q2",
            field=models.TextField(help_text="Second question?", max_length=1000),
        ),
        migrations.AlterField(
            model_name="application",
            name="q3",
            field=models.TextField(help_text="Third question?", max_length=1000),
        ),
    ]
